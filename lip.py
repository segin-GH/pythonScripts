#! /usr/bin/python3

import sys

def print_lines(filename, start_line=0, end_line=None):
    with open(filename, 'r') as f:
        for current_line_num, line in enumerate(f, 1):
            if end_line is None:  # If the end_line is not provided, print till the end
                if current_line_num >= start_line:
                    print(line, end='')
            else:
                if start_line <= current_line_num <= end_line:
                    print(line, end='')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python print_lines.py <filename> [start_line] [end_line]")
        sys.exit(1)

    file_name = sys.argv[1]

    start = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else 0
    end = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else None

    print_lines(file_name, start, end)
