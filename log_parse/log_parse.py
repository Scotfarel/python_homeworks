import re
import datetime
from collections import defaultdict
from urllib.parse import urlparse
from os.path import splitext


def parse(
        ignore_files=False, ignore_urls=[], start_at=None, stop_at=None,
        request_type=None, ignore_www=False, slow_queries=False):
    log_pattern = re.compile('\[(?P<request_date>.*) (?P<request_time>.*)\] '
                             '\"(?P<request>.*) (?P<URL>.*) (?P<protocol>.*)\"'
                             ' (?P<response_code>.*) (?P<response_time>.*)')
    urls_dict = defaultdict(lambda: [0, 0])
    urls_number = 5
    f = open('log.log')
    for line in f:
        if log_pattern.match(line.rstrip()):
            match = log_pattern.match(line.rstrip())
            dict_assert(match, ignore_files, ignore_www, ignore_urls, start_at, stop_at, request_type, urls_dict)
    f.close()

    return top_urls(slow_queries, urls_dict, urls_number)


def dict_assert(match, ignore_files, ignore_www, ignore_urls, start_at, stop_at, request_type, URLs_dict):
    parsed = urlparse(match.group('URL'))
    url_netloc = parsed.netloc
    if ignore_www:
        if url_netloc.startswith('www.'):
            url_netloc = url_netloc[4:]
    url_path, extension = splitext(parsed.path)
    url = url_netloc + url_path + extension

    ignore_files_flag = not (extension and ignore_files)
    ignore_urls_flag = url not in ignore_urls
    time_flag = bool_time_flag(match, start_at, stop_at)
    request_type_flag = request_type is None or request_type == match.group('request')

    response_time = int(match.group('response_time'))

    if ignore_files_flag and ignore_urls_flag and request_type_flag and time_flag:
        URLs_dict[url][0] += 1
        URLs_dict[url][1] += response_time


def bool_time_flag(match, start_at, stop_at):
    str_log_datetime = match.group('request_date') + match.group('request_time')
    log_datetime = datetime.datetime.strptime(str_log_datetime, '%d/%b/%Y%H:%M:%S')

    start = stop = False
    if start_at is None or log_datetime >= start_at:
            start = True
    if stop_at is None or log_datetime <= stop_at:
            stop = True

    return True if start and stop else False


def top_urls(slow_requeries, urls_dict, urls_number):
    top_urls_list = []
    if slow_requeries:
        for item in sorted(urls_dict.items(), key=lambda x: (x[1][1] / x[1][0]), reverse=True)[:urls_number]:
            top_urls_list.append(int(item[1][1] / item[1][0]))
    else:
        for item in sorted(urls_dict.items(), key=lambda x: x[1][0], reverse=True)[:urls_number]:
            top_urls_list.append(item[1][0])
    urls_dict.clear()

    return top_urls_list
