import yaml
import sys
import os
from aiohttp import web


with open(sys.argv[1]) as config_file:
    config = yaml.load(config_file)


async def hello(request):
    req_file_path = config.get('directory') + '/' + request.match_info.get('file_name')
    if os.path.exists(req_file_path):
        byte_text = open(req_file_path, "rb").read()
        return web.Response(body=byte_text)
    return web.Response(body=b'Hello, World!')


app = web.Application()
app.add_routes([web.get('/{file_name}', hello)])


if __name__ == '__main__':
    print(config.get('port'))

    web.run_app(app, host=config.get('host'), port=config.get('port'))
