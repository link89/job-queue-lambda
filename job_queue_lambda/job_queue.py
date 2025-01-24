from typing import Optional
from logging import getLogger
import csv
import re

from .config import SlurmConfig
from .connector import Connector

logger = getLogger(__name__)

class JobQueue:
    async def new_job(self, script: str) -> str:
        raise NotImplementedError()

    async def get_job_info(self, job_id: str) -> Optional[dict]:
        raise NotImplementedError()


class Slurm(JobQueue):

    def __init__(self, config: SlurmConfig, connector: Connector):
        self.config = config
        self.connector = connector

    async def new_job(self, script: str):
        # FIXME: create a script file and submit it
        cmd = f"{self.config.sbatch} {script}"
        result = await self.connector.run(cmd)
        if result.return_code != 0:
            raise ValueError(f"Failed to submit job: {result.stderr}")
        job_id = self._parse_job_id(result.stdout)
        if not job_id:
            raise ValueError(f"Failed to parse job id from: {result.stdout}, err: {result.stderr}")
        return job_id

    async def get_job_info(self, job_id: str):
        # query jobs
        cmd = f'{self.config.squeue} -o "%i|%t|%r|%N" -j {job_id}'
        result = await self.connector.run(cmd)
        if result.return_code != 0:
            if 'Invalid job id specified' in result.stderr:
                return None
            logger.error(f"Unexpected squeue error: {result.stderr}")
            return {'id': job_id, 'nodes': []}
        # query nodes
        nodes = []
        job = parse_csv(result.stdout, delimiter="|")[0]
        state = job.get('ST', '').strip()
        if state == 'R':
            nodelist = job.get('NODELIST', '').strip()
            result = await self.connector.run(f'{self.config.scontrol} show hostname {nodelist}')
            if result.return_code == 0:
                nodes = result.stdout.strip().splitlines()
            else:
                logger.error(f"Failed to parse nodelist: {result.stderr}")
        return { 'id': job_id, 'nodes': nodes, }

    def _parse_job_id(self, stdout: str):
        m = re.search(r'\d+', stdout)
        return m.group(0) if m else ''


def parse_csv(text: str, delimiter="|"):
    """
    Parse CSV text to list of dictionaries
    """
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    return list(reader)
