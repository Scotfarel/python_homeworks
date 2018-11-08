import socket
import argparse
import uuid
import re
from collections import defaultdict


class Task:
    def __init__(self, length, data):
        self._task_id = uuid.uuid4()
        self._length = length
        self._data = data
        self._status = 'Free'
        self._timeout = 300

    @property
    def task_id(self):
        return self._task_id


class Command:
    def parse_cmd(self, command):
        self.method = command[0]
        queue_name = command[1]
        task_id = command[1]
        task_length = command[2]
        task_data = command[3]

    @staticmethod
    def apply():
        pass


class ADDcommand(Command):
    def __init__(self):
        self._queue_name = self.command[1]

    pass


class GETcommand(Command):
    pass


class ACKcommand(Command):
    pass


class INcommand(Command):
    pass


class TaskQueueServer:
    def __init__(self, ip, port, path, timeout):
        self._ip = ip
        self._port = port
        self._path = path
        self._timeout = timeout
        self._queues = defaultdict(list)

    def apply_command_action(self, current_command):
        cmd_name, *args = current_command.split(' ')
        if not cmd_name:
            raise AttributeError
        cmd_name = cmd_name.strip().lower()
        cmd = {'ADD': add_cmd, 'GET': del_cmd, 'ACK': ack_cmd, 'IN': in_cmd, 'SAVE': save_cmd}

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
                #current_command = Command(command)
                self.apply_command_action(command)
                res = self.apply_command_action(current_command)
                current_connection.send(res.encode('utf8'))

    def add_task(self, current_command):
        added_task = Task(current_command.task_length, current_command.task_data)
        self.queues[current_command.queue_name].append(added_task)
        return str(added_task.task_id)

    def get_task(self, current_command):
        res = None
        for x in list(reversed(self.queues[current_command.queue_name])):
            if x.status == 'Free' and x.timeout == '300':
                res = x.id + x.lenght + x.data
                x.status = 'Busy' # что делать с таймаутом?
                break
        return res

    def ack_task(self, current_command):
        for idx, x in enumerate(self.queues[current_command.queue_name]):
            if x.id == current_command.id:
                self.queues[current_command.queue_name].pop(idx - 1)
        return 'OK'

    def check_task_in_queue(self, current_command):
        res = 'NO'
        if current_command.task_id in self.queues[current_command.queue_name]:
            res = 'YES'
        return res

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
