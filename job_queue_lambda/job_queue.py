from .config import SlurmConfig
from .connector import Connector

class JobQueue:
    ...


class Slurm(JobQueue):

    def __init__(self, config: SlurmConfig, connector: Connector):
        self.config = config
        self.connector = connector