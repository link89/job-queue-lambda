from typing import List, Dict
from logging import getLogger

from .connector import SshConnector, LocalConnector, Connector
from .config import ClusterConfig, LambdaConfig
from .job_queue import JobQueue, Slurm


logger = getLogger(__name__)


class Cluster:

    def __init__(self, config: ClusterConfig, state=None):
        if state is None:
            state = {}
        self._state = state

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
            # no job running, submit a new one
            # TODO: support multiple job
            job_id = await self.job_queue.new_job(lambda_config.script)
            job_info = await self.job_queue.get_job_info(job_id)
            if job_info is not None:
                new_jobs.append(job_info)
            else:
                logger.error(f"Failed to submit job: {job_id}")
        self._state[name]["jobs"] = new_jobs

    async def forward(self, lambda_name: str, req):
        lambda_state = self._state.get(lambda_name)
        if lambda_state is None:
            raise ValueError(f"Lambda not found: {lambda_name}")
        if not lambda_state["jobs"]:
            raise ValueError(f"No job running for lambda: {lambda_name}")
        job = lambda_state["jobs"][0]
        # TODO: use aiohttp to forward request, take care of socks proxy


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

    async def forward(self, cluster_name: str, lambda_name: str, req):
        cluster = self.clusters.get(cluster_name)
        if cluster is None:
            raise ValueError(f"Cluster not found: {cluster_name}")
        return await cluster.forward(lambda_name, req)
