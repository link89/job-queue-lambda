from typing import List, Dict, Optional
from logging import getLogger

from aiohttp import web
from aiohttp_socks import ProxyConnector
import aiohttp

from .connector import SshConnector, LocalConnector, Connector
from .config import ClusterConfig, LambdaConfig
from .job_queue import JobQueue, Slurm


logger = getLogger(__name__)


class Cluster:

    def __init__(self, config: ClusterConfig, state=None):
        if state is None:
            state = {}
        self._state = state

        self._proxy_connector: Optional[ProxyConnector] = None

        self.config = config
        if config.ssh:
            self.connector: Connector = SshConnector(config.ssh)
        else:
            self.connector: Connector = LocalConnector()

        if config.job_queue.slurm:
            self.job_queue: JobQueue = Slurm(
                config.job_queue.slurm, self.connector)
        else:
            raise ValueError("Unsupported job queue")

        self.lambdas: Dict[str, LambdaConfig] = {}
        for lambda_config in config.lambdas:
            if lambda_config.name in self.lambdas:
                raise ValueError(f"Duplicate lambda name: {lambda_config.name}")
            self.lambdas[lambda_config.name] = lambda_config

    async def poll(self):
        for lambda_config in self.lambdas.values():
            await self._poll_lambda(lambda_config)

    async def _poll_lambda(self, lambda_config: LambdaConfig):
        name = lambda_config.name
        if name not in self._state:
            self._state[name] = {
                "jobs": [],
            }
        # update job state
        new_jobs = []
        for job in self._state[name]["jobs"]:
            job_id = job["job_id"]
            job_info = await self.job_queue.get_job_info(job_id)
            if job_info is not None:
                new_jobs.append(job)

        if not new_jobs:
            # no job is running, submit a new one
            # TODO: support max_jobs option in the future
            job_id = await self.job_queue.new_job(lambda_config.script_path, lambda_config.script)
            job_info = await self.job_queue.get_job_info(job_id)
            if job_info is not None:
                new_jobs.append(job_info)
            else:
                logger.error(f"Failed to submit job: {job_id}")
        self._state[name]["jobs"] = new_jobs

    def get_socks_proxy(self):
        if self._proxy_connector is None:
            socks_url = self.connector.get_socks_proxy()
            if socks_url is None:
                return None
            self._proxy_connector = ProxyConnector.from_url(socks_url)
        return self._proxy_connector

    async def forward(self, lambda_name: str, req: web.Request, target_url: str):
        lambda_state  = self._state.get(lambda_name)
        lambda_config = self.lambdas.get(lambda_name)
        if lambda_state is None or lambda_config is None:
            raise ValueError(f"Lambda not found: {lambda_name}")
        if not lambda_state["jobs"]:
            raise ValueError(f"No job running for lambda: {lambda_name}")
        # TODO: load balance by request count if multiple jobs are supported
        job = lambda_state["jobs"][0]
        nodes = job["nodes"]
        if not nodes:
            raise ValueError(f"No node found for job: {job['id']}")
        # TODO: load balance by request count
        node = nodes[0]

        forword_to = lambda_config.forward_to.format(NODE_NAME=node).strip('/')
        forward_url = forword_to + target_url
        logger.info(f"Forwarding request to {forward_url}")

        # forward the request to the target server
        # TODO: use connection pool for better performance
        proxy_connector = self.get_socks_proxy()
        headers = dict(req.headers)
        headers.pop('Host', None)
        async with aiohttp.ClientSession(connector=proxy_connector) as session:
            async with session.request(
                method=req.method,
                url=forward_url,
                headers=headers,
                data=await req.read(),
                allow_redirects=False,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                resp_body = await response.read()
                return web.Response(
                    body=resp_body,
                    status=response.status,
                    headers=response.headers
                )

class ClusterManager:
    def __init__(self, clusters : List[ClusterConfig]):
        self.clusters: Dict[str, Cluster] = {}
        for config in clusters:
            if config.name in self.clusters:
                raise ValueError(f"Duplicate cluster name: {config.name}")
            self.clusters[config.name] = Cluster(config)

    async def poll(self):
        for cluster in self.clusters.values():
            await cluster.poll()

    async def forward(self, cluster_name: str, lambda_name: str, req: web.Request, target_url: str):
        cluster = self.clusters.get(cluster_name)
        if cluster is None:
            raise ValueError(f"Cluster not found: {cluster_name}")
        return await cluster.forward(lambda_name, req, target_url)
