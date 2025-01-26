from yaml import safe_load
from aiohttp import web

from .server import make_http_server
from .config import Config
from .cluster import ClusterManager

def start(config_file: str):
    with open(config_file, 'r') as f:
        config = Config(**safe_load(f))

    cluster_manager = ClusterManager(config.clusters)
    app = make_http_server(cluster_manager, config.base_url)
    web.run_app(app, host=config.host, port=config.port)


def main():
    import fire
    fire.Fire(start)
