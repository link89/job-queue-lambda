from pydantic import BaseModel
from typing import List, Optional
import os


class SshConfig(BaseModel):
    host: str
    port: int = 22
    config_file: str = os.path.expanduser("~/.ssh/config")
    socks_port: int


class LambdaConfig(BaseModel):
    name: str
    forward_to: str
    script: str


class SlurmConfig(BaseModel):
    sbatch: str = "sbatch"
    squeue: str = "squeue"
    scancel: str = "scancel"


class JobQueueConfig(BaseModel):
    slurm: Optional[SlurmConfig] = None


class ClusterConfig(BaseModel):
    name: str
    lambdas: List[LambdaConfig]
    ssh: Optional[SshConfig] = None
    job_queue: Optional[JobQueueConfig] = None


class Config(BaseModel):
    listen: str = "127.0.0.1:9000"
    state_file : str = "./state.json"
    clusters: List[ClusterConfig]

