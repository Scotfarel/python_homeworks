import socket
import argparse
import uuid
import re
import time
import pickle
from collections import defaultdict


class Task:
    def __init__(self, length, data):
        self._task_id = uuid.uuid4()
        self._length = length
        self._data = data
        self._status = 'Free'


class TaskQueueServer:
    def __init__(self, ip, port, path, timeout):
        self._ip = ip
        self._port = port
        self._path = path
        self._timeout = timeout
        self._queues = defaultdict(list)
        self._task_in_work = defaultdict(list)

    def add_cmd(self, current_command):
        add_cmd_pattern = re.compile('(?P<method>.*) (?P<queue>.*) (?P<length>.*) (?P<data>.*)')
        match = add_cmd_pattern.match(current_command.rstrip())
        added_task = Task(match.group('length'), match.group('data'))
        self._queues[match.group('queue')].append(added_task)
        return str(added_task._task_id)

    def get_cmd(self, current_command):
        get_cmd_pattern = re.compile('(?P<method>.*) (?P<queue>.*)')
        match = get_cmd_pattern.match(current_command.rstrip())
        res = 'NONE'
        for task in self._queues[match.group('queue')]:
            if task._status == 'Free':
                res = str(task._task_id) + str(task._length) + str(task._data)
                task._status = 'Busy'
                task.issue_time = time.time()
                self._task_in_work[match.group('queue')].append(task)
                break
        return res

    def ack_cmd(self, current_command):
        ack_cmd_pattern = re.compile('(?P<method>.*) (?P<queue>.*) (?P<id>.*)')
        match = ack_cmd_pattern.match(current_command.rstrip())
        for task in self._queues[match.group('queue')]:
            if task._task_id == match.group('id'):
                self._queues[match.group('queue')].remove(task)
                self._task_in_work[match.group('queue')].remove(task)
        return 'OK'

    def check_task_cmd(self, current_command):
        in_cmd_pattern = re.compile('(?P<method>.*) (?P<queue>.*) (?P<id>.*)')
        match = in_cmd_pattern.match(current_command.rstrip())
        res = 'NO'
        for task in self._queues[match.group('queue')]:
            if str(task._task_id) == match.group('id'):
                res = 'YES'
                break
        return res

    def save_cmd(self, current_command):
        return 'OK'

    def check_tasks_timeout(self):
        for queue in self._task_in_work.values():
            for task in queue:
                if time.time() - task.issue_time > self._timeout:
                    task._status = 'Free'
                    self._task_in_work[queue].remove(task)

    def apply_command_action(self, current_command):
        cmd_name, *args = current_command.split(' ')
        if not cmd_name:
            return 'recv_cmd_error'
        cmd_name = cmd_name.strip()
        cmd = {'ADD': self.add_cmd, 'GET': self.get_cmd, 'ACK': self.ack_cmd,
               'IN': self.check_task_cmd, 'SAVE': self.save_cmd}.get(cmd_name)
        if not cmd:
            return 'ERROR'
        return cmd(current_command)

    def run(self):
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connection.bind((self._ip, self._port))
        connection.listen(1)
        while True:
            current_connection, address = connection.accept()
            while True:
                command = (current_connection.recv(2048)).decode('utf8')
                self.check_tasks_timeout()
                res = self.apply_command_action(command)
                current_connection.send(res.encode('utf8'))


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
