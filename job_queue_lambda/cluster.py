from typing import List, Dict


from .connector import SshConnector, LocalConnector
from .config import ClusterConfig
from .job_queue import JobQueue, Slurm


class Cluster:

    def __init__(self, config: ClusterConfig):
        self.config = config
        if config.ssh:
            self.connector = SshConnector(config.ssh)
        else:
            self.connector = LocalConnector()

        if config.job_queue.slurm:
            self.job_queue: JobQueue = Slurm(
                config.job_queue.slurm, self.connector)
        else:
            raise ValueError("Unsupported job queue")


    def start(self):
        ...



class ClusterManager:

    def __init__(self, clusters : List[ClusterConfig]):
        self.clusters: Dict[str, Cluster] = {}
        for config in clusters:
            if config.name in self.clusters:
                raise ValueError(f"Duplicate cluster name: {config.name}")
            self.clusters[config.name] = Cluster(config)

    def start(self):
        ...

