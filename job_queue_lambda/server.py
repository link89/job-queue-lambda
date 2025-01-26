import aiohttp
from aiohttp import web
import asyncio
import os
import re

from .cluster import ClusterManager

# Configuration from environment variables


def make_http_server(cluster_manager: ClusterManager, base_url: str):
    if not base_url.endswith('/'):
        base_url = base_url + '/'

    async def handle_request(request: web.Request) -> web.Response:
        print(request)
        cluster_name = request.match_info['cluster_name']
        lambda_name = request.match_info['lambda_name']
        return web.Response(text=f"Hello, {cluster_name}! You called {lambda_name}.")

        # res = await cluster_manager.forward(cluster_name, lambda_name, request, target_url=request.path)

        # # Prepare headers, excluding 'Host' to avoid conflicts
        # headers = dict(request.headers)
        # headers.pop('Host', None)

        # # Read the original request's body
        # data = await request.read()

        # try:
        #     async with aiohttp.ClientSession() as session:
        #         async with session.request(
        #             method=request.method,
        #             url=target_url,
        #             headers=headers,
        #             data=data,
        #             allow_redirects=False,
        #             timeout=aiohttp.ClientTimeout(total=TIMEOUT)
        #         ) as response:
        #             # Read the response body from the target server
        #             resp_body = await response.read()
        #             # Forward the response with the same status, headers, and body
        #             return web.Response(
        #                 body=resp_body,
        #                 status=response.status,
        #                 headers=response.headers
        #             )
        # except aiohttp.ClientError as e:
        #     # Handle client connection errors (e.g., target server unreachable)
        #     return web.Response(status=502, text=f"Bad Gateway Error: {str(e)}")
        # except asyncio.TimeoutError:
        #     # Handle request timeout
        #     return web.Response(status=504, text="Gateway Timeout")

    # Set up the aiohttp application with a catch-all route
    app = web.Application()
    # the route should be /{base_url}/clusters/{cluster_name}/lambdas/{lambda_name}/.*
    forward_url = base_url + 'clusters/{cluster_name}/lambdas/{lambda_name}/.*'
    app.add_routes([
        web.route('*', forward_url, handle_request),
    ])
    return app
