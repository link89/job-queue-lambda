from aiohttp import web

from .cluster import ClusterManager

def make_http_server(cluster_manager: ClusterManager, base_url: str):
    if not base_url.endswith('/'):
        base_url = base_url + '/'

    async def handle_request(request: web.Request) -> web.Response:
        cluster_name = request.match_info['cluster_name']
        lambda_name  = request.match_info['lambda_name']
        target_url = request.match_info.get('tail', '')
        if request.query_string:
            target_url = target_url + '?' + request.query_string
        try:
            return await cluster_manager.forward(cluster_name, lambda_name, request, target_url=target_url)
        except ValueError as e:
            return web.Response(status=400, text=str(e))
        except Exception as e:
            return web.Response(status=500, text=str(e))

    app = web.Application()
    forward_pattern = base_url + 'clusters/{cluster_name}/lambdas/{lambda_name}'
    app.add_routes([
        web.route('*', forward_pattern, handle_request),
        web.route('*', forward_pattern + '/{tail:.*}', handle_request)

    ])
    return app
