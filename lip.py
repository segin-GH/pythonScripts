#! /usr/bin/python3

import sys

def print_lines(filename, start_line, end_line):
    with open(filename, 'r') as f:
        for current_line_num, line in enumerate(f, 1):
            if start_line <= current_line_num <= end_line:
                print(line, end='')

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: lip <filename> <start_line> <end_line>")
        sys.exit(1)

    file_name = sys.argv[1]
    start = int(sys.argv[2])
    end = int(sys.argv[3])

    print_lines(file_name, start, end)
