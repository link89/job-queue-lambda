from yaml import safe_load
from aiohttp import web
import asyncio

from .server import make_http_server
from .config import Config
from .cluster import ClusterManager


def start(config_file: str):
    with open(config_file, 'r') as f:
        config = Config(**safe_load(f))

    loop = asyncio.new_event_loop()

    cluster_manager = ClusterManager(config.clusters)
    loop.create_task(cluster_manager.start())

    app = make_http_server(cluster_manager, config.base_url)
    web.run_app(app, host=config.host, port=config.port, loop=loop)


def main():
    import fire
    import logging
    import os

    level_name = os.environ.get('LOG_LEVEL', 'INFO')
    level = logging._nameToLevel.get(level_name, logging.INFO)
    logging.basicConfig(format='%(asctime)s %(name)s: %(message)s', level=level)
    # config log level of asyncssh to warning
    logging.getLogger('asyncssh').setLevel(logging.WARNING)
    fire.Fire(start)
