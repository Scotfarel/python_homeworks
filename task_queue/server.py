import socket
import argparse
import uuid
from collections import defaultdict


class Task:
    def __init__(self, length, data):
        self._task_id = uuid.uuid4()
        self._length = length
        self._data = data
        self._status = 'Free'

    @property
    def task_id(self):
        return self._task_id


class Command:
    def __init__(self, command):
        args_list = str(command).split(" ")
        print(args_list)

        self._method = args_list[0]
        self._queue_name = args_list[1]
        self._task_id = args_list[1]
        self._task_length = args_list[2]
        self._task_data = args_list[3]

    @property
    def method(self):
        return self._method

    @property
    def queue_name(self):
        return self._queue_name

    @property
    def task_length(self):
        return self._task_length

    @property
    def task_data(self):
        return self._task_data

    @property
    def task_id(self):
        return self._task_id


class TaskQueueServer:
    def __init__(self, ip, port, path, timeout):
        self._ip = ip
        self._port = port
        self._path = path
        self._timeout = timeout
        self._queues = defaultdict()

    def apply_command_action(self, current_command):
        t = "b'ADD"
        if current_command.method == t:
            self.add_task(current_command)
        elif current_command.method == 'GET':
            self.get_task(current_command)
        elif current_command.method == 'ACK':
            self.ack_task(current_command)
        elif current_command.method == 'IN':
            self.check_task_in_queue(current_command)
        elif current_command.method == 'SAVE':
            self.save_state()
        else:
            raise AttributeError

    def run(self):
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connection.bind((self.ip, self.port))
        connection.listen(1)
        while True:
            current_connection, address = connection.accept()
            while True:
                command = current_connection.recv(2048)
                current_command = Command(command)
                res = self.apply_command_action(current_command)
                current_connection.send(res)

    def add_task(self, current_command):
        task = Task(current_command.task_length, current_command.task_data)
        self.queues[current_command.queue_name].append(task)
        return task.task_id

    def get_task(self, current_command):
        pass

    def ack_task(self, current_command):
        pass

    def check_task_in_queue(self, current_command):
        pass

    def save_state(self):
        pass

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    @property
    def path(self):
        return self._path

    @property
    def timeout(self):
        return self._timeout

    @property
    def queues(self):
        return self._queues


def parse_args():
    parser = argparse.ArgumentParser(description='This is a simple task queue server with custom protocol')
    parser.add_argument(
        '-p',
        action="store",
        dest="port",
        type=int,
        default=5555,
        help='Server port')
    parser.add_argument(
        '-i',
        action="store",
        dest="ip",
        type=str,
        default='0.0.0.0',
        help='Server ip adress')
    parser.add_argument(
        '-c',
        action="store",
        dest="path",
        type=str,
        default='./',
        help='Server checkpoints dir')
    parser.add_argument(
        '-t',
        action="store",
        dest="timeout",
        type=int,
        default=300,
        help='Task maximum GET timeout in seconds')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    server = TaskQueueServer(**args.__dict__)
    server.run()
