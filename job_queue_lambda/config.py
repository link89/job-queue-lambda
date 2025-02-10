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
    cwd: str


class SlurmConfig(BaseModel):
    sbatch: str = "sbatch"
    squeue: str = "squeue"
    scancel: str = "scancel"
    scontrol: str = "scontrol"


class JobQueueConfig(BaseModel):
    slurm: Optional[SlurmConfig] = None


class ClusterConfig(BaseModel):
    name: str
    lambdas: List[LambdaConfig]
    ssh: Optional[SshConfig] = None
    job_queue: JobQueueConfig


class Config(BaseModel):
    host: str = "127.0.0.1"
    port: int = 9000
    base_url: str = "/"
    state_file : str = "./state.json"
    clusters: List[ClusterConfig]
