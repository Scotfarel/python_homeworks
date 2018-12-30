import argparse
import yaml
import os
import asyncio
from aiohttp import web, ClientSession, client_exceptions
import collections

Neighbour = collections.namedtuple('Neighbour', 'name, host, port, url')


class StaticServerConfig:
    def __init__(self, host, port, directory, save_found, neighbours):
        self.host = host
        self.port = port
        self.directory = directory
        self.save_found = save_found
        self.neighbours = neighbours

    @classmethod
    def load_from_yaml(cls, config_path):
        with open(config_path, 'rb') as config_file:
            config = yaml.load(config_file)

        def parse_neighbours():
            n_list = []
            for n_name, n_conf in config['neighbours'].items():
                protocol = 'http://'
                host, port = n_conf['host'], int(n_conf.get('port'))
                url = protocol + f'{host}:{port}' if port else host
                n_list.append(Neighbour(n_name, host, port, url))
            return n_list

        return cls(config['host'], config['port'], config['directory'], config['save_found'], parse_neighbours())


class StaticServer:

    n_download_endpoint = 'neighbour_download'
    n_check_endpoint = 'neighbour_check'

    def __init__(self, config, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.config = config
        self.app = web.Application()
        self.setup_routes()
        self.runner = None
        self.site = None

    def run(self):
        web.run_app(self.app, host=self.config.host, port=self.config.port)

    def setup_routes(self):
        self.app.add_routes([
            web.get('/{file_name}', self.main_download),
            web.get(f'/{self.n_download_endpoint}/{{file_name}}', self.neighbour_download),
            web.get(f'/{self.n_check_endpoint}/{{file_name}}', self.neighbour_check)
        ])

    async def prepare_file_response(self, file_bytes):
        try:
            file_text = await self.loop.run_in_executor(None, file_bytes.decode, 'utf8')
            return web.Response(text=file_text)
        except UnicodeDecodeError:
            return web.Response(body=file_bytes)

    async def main_download(self, request):
        file_name = request.match_info.get('file_name')

        search_in_neighbour = False

        file_bytes = await self.get_file_from_storage(file_name)
        if not file_bytes:
            file_bytes = await self.ask_neighbours(file_name)
            search_in_neighbour = True

        if not file_bytes:
            raise web.HTTPNotFound(text=f'There is no file with name {file_name!r}')

        if search_in_neighbour and self.config.save_found:
            await self.loop.run_in_executor(None, self.write_file_to_storage, file_name, file_bytes)

        return await self.prepare_file_response(file_bytes)

    async def neighbour_download(self, request):
        file_name = request.match_info.get('file_name')

        file_bytes = await self.get_file_from_storage(file_name)
        if not file_bytes:
            raise web.HTTPNotFound(text=f'Sry, neighbour, there is no file with name {file_name!r}')

        return await self.prepare_file_response(file_bytes)

    async def neighbour_check(self, request):
        file_name = request.match_info.get('file_name')

        file_path = self.check_file_in_storage(file_name)
        if not file_path:
            raise web.HTTPNotFound(text=f'Sry, neighbour, there is no file with name {file_name!r}')

        return web.Response(text='File found')

    def check_file_in_storage(self, file_name):
        file_path = os.path.join(self.config.directory, file_name)
        if not os.path.exists(file_path):
            return None
        return file_path

    @staticmethod
    def read_file_from_storage(path):
        with open(path, 'rb') as file:
            return file.read()

    def write_file_to_storage(self, file_name, file_bytes):
        file_path = os.path.join(self.config.directory, file_name)
        with open(file_path, 'wb') as file:
            return file.write(file_bytes)

    async def get_file_from_storage(self, file_name):
        file_path = self.check_file_in_storage(file_name)
        if not file_path:
            return None
        file_bytes = await self.loop.run_in_executor(None, self.read_file_from_storage, file_path)
        return file_bytes

    async def ask_neighbours(self, file_name):
        tasks = []
        async with ClientSession() as session:
            for n in self.config.neighbours:
                task = asyncio.ensure_future(self.ask_neighbour(n, file_name, session))
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

            for neighbour, result in filter(lambda n_and_res: bool(n_and_res[1]), responses):
                return await self.download_from_neighbour(neighbour, file_name, session)
            else:
                return None

    async def download_from_neighbour(self, neighbour, file_name, session):
        download_url = f'{neighbour.url}/{self.n_download_endpoint}/{file_name}'

        async with session.get(download_url) as response:
            if response.status == 200:
                return await response.read()
            return None

    async def ask_neighbour(self, neighbour, file_name, session):
        asking_url = f'{neighbour.url}/{self.n_check_endpoint}/{file_name}'
        try:
            async with session.get(asking_url) as response:
                if response.status == 200:
                    return neighbour, await response.read()
                return neighbour, None
        except client_exceptions.ClientConnectionError:
            return neighbour, None


def create_args_parser():
    prs = argparse.ArgumentParser(description='Async file storage')
    prs.add_argument('config_path', help='A path for daemon config')
    return prs


if __name__ == '__main__':
    parser = create_args_parser()
    args = parser.parse_args()
    cfg = StaticServerConfig.load_from_yaml(args.config_path)

    async_loop = asyncio.get_event_loop()
    server = StaticServer(cfg, async_loop)

    server.run()
