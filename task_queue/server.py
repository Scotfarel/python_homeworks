import socket
import argparse
import os
import uuid
import re
import time
import pickle
from collections import defaultdict


class Task:
    def __init__(self, length, data):
        self.task_id = uuid.uuid4()
        self.length = length
        self.data = data
        self.in_work = False


class TaskQueueServer:
    def __init__(self, ip, port, path, timeout):
        self.ip = ip
        self.port = port
        self.path = path
        self.timeout = timeout
        if os.path.exists(path):
            load_queues = pickle.load(open(path, 'rb'))
            self.queues = load_queues[0][1]
            self.tasks_in_work = load_queues[1][1]
        else:
            self.queues = defaultdict(list)
            self.tasks_in_work = defaultdict(list)

    def add_cmd(self, current_command):
        add_cmd_pattern = re.compile('(?P<method>.*) (?P<queue>.*) (?P<length>.*) (?P<data>.*)')
        match = add_cmd_pattern.match(current_command.rstrip())
        if not match:
            return 'ERROR'
        if int(match.group('length')) > 10**6 or int(match.group('length')) != len(match.group('data')):
            return 'ERROR'
        added_task = Task(match.group('length'), match.group('data'))
        self.queues[match.group('queue')].append(added_task)
        return str(added_task.task_id)

    def get_cmd(self, current_command):
        get_cmd_pattern = re.compile('(?P<method>.*) (?P<queue>.*)')
        match = get_cmd_pattern.match(current_command.rstrip())
        if not match:
            return 'ERROR'
        res = 'NONE'
        for task in self.queues[match.group('queue')]:
            if not task.in_work:
                res = f'{task.task_id} {task.length} {task.data}'
                task.in_work = True
                task.issue_time = time.time()
                self.tasks_in_work[match.group('queue')].append(task)
                break
        return res

    def ack_cmd(self, current_command):
        ack_cmd_pattern = re.compile('(?P<method>.*) (?P<queue>.*) (?P<id>.*)')
        match = ack_cmd_pattern.match(current_command.rstrip())
        if not match:
            return 'ERROR'
        for task in self.queues[match.group('queue')]:
            if str(task.task_id) == match.group('id'):
                self.queues[match.group('queue')].remove(task)
                self.tasks_in_work[match.group('queue')].remove(task)
                return 'YES'
        return 'NO'

    def check_task_cmd(self, current_command):
        in_cmd_pattern = re.compile('(?P<method>.*) (?P<queue>.*) (?P<id>.*)')
        match = in_cmd_pattern.match(current_command.rstrip())
        if not match:
            return 'ERROR'
        res = 'NO'
        for task in self.queues[match.group('queue')]:
            if str(task.task_id) == match.group('id'):
                res = 'YES'
                break
        return res

    def save_cmd(self, _):
        queues_to_save = {'_queues': self.queues, '_tasks_in_work': self.tasks_in_work}
        pickle.dump(queues_to_save, open(self.path, 'wb'))
        return 'OK'

    def check_tasks_timeout(self):
        for queue in self.tasks_in_work.values():
            for task in queue:
                if time.time() - task.issue_time > self.timeout:
                    task.in_work = False
                    self.tasks_in_work[queue].remove(task)

    def handle_connection(self, current_command):
        try:
            cmd_name, *args = current_command.split(' ')
            if not cmd_name:
                return 'ERROR'
            cmd_name = cmd_name.strip().lower()
            cmd = {'add': self.add_cmd, 'get': self.get_cmd, 'ack': self.ack_cmd,
                   'in': self.check_task_cmd, 'save': self.save_cmd}.get(cmd_name)
            if not cmd:
                return 'ERROR'
            resp = cmd(current_command)
        except Exception as e:
            resp = e
        return resp

    def run(self):
        print('Starting the server...')
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connection.bind((self.ip, self.port))
        connection.listen(1)
        while True:
            try:
                current_connection, address = connection.accept()
                command = (current_connection.recv(2**20)).decode('utf')
                self.check_tasks_timeout()
                res = self.handle_connection(command)
                current_connection.send(res.encode('utf'))
                current_connection.shutdown(1)
                current_connection.close()
            except KeyboardInterrupt:
                print('Shutting down...')
                connection.close()
                break
        print('Done')


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
        default='db.pickle',
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
