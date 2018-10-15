import argparse
import sys
import re


def output(line):
    print(line)


def create_req(params):
    params.pattern = re.sub('[?]', '.', params.pattern)
    params.pattern = re.sub('[*]', '.*', params.pattern)
    req = re.compile(params.pattern, re.I) if params.ignore_case else re.compile(params.pattern)
    return req


def str_format(params, idx, line, context_line):
    index = str(idx + 1) if params.line_number else ''
    if params.line_number:
        index += ':' if context_line else '-'
    out_str = index + line
    return out_str


def grep(lines, params):
    req = create_req(params)
    before_line = max(params.before_context, params.context)
    after_line = max(params.context, params.after_context)
    context_lines = []
    last_matched = -1 - after_line

    if params.count:
        num_count = 0
        for line in lines:
            if params.invert ^ bool(req.search(line)):
                num_count += 1
        output(str(num_count))
        return

    for idx, line in enumerate(lines):
        if params.invert ^ bool(req.search(line)):
            for item in context_lines:
                begin = 0 if idx - before_line < 0 else idx - before_line
                output(str_format(params, begin, item, False))
            context_lines.clear()
            output(str_format(params, idx, line, True))
            last_matched = idx
        else:
            if idx - last_matched <= after_line:
                output(str_format(params, idx, line, False))
            elif before_line > 0:
                context_lines.append(line)
                if len(context_lines) > before_line:
                    del context_lines[0]


def parse_args(args):
    parser = argparse.ArgumentParser(description='This is a simple grep on python')
    parser.add_argument(
        '-v',
        action="store_true",
        dest="invert",
        default=False,
        help='Selected lines are those not matching pattern.')
    parser.add_argument(
        '-i',
        action="store_true",
        dest="ignore_case",
        default=False,
        help='Perform case insensitive matching.')
    parser.add_argument(
        '-c',
        action="store_true",
        dest="count",
        default=False,
        help='Only a count of selected lines is written to standard output.')
    parser.add_argument(
        '-n',
        action="store_true",
        dest="line_number",
        default=False,
        help='Each output line is preceded by its relative line number in the file, starting at line 1.')
    parser.add_argument(
        '-C',
        action="store",
        dest="context",
        type=int,
        default=0,
        help='Print num lines of leading and trailing context surrounding each match.')
    parser.add_argument(
        '-B',
        action="store",
        dest="before_context",
        type=int,
        default=0,
        help='Print num lines of trailing context after each match')
    parser.add_argument(
        '-A',
        action="store",
        dest="after_context",
        type=int,
        default=0,
        help='Print num lines of leading context before each match.')
    parser.add_argument('pattern', action="store", help='Search pattern. Can contain magic symbols: ?*')
    return parser.parse_args(args)


def main():
    params = parse_args(sys.argv[1:])
    grep(sys.stdin.readlines(), params)


if __name__ == '__main__':
    main()
