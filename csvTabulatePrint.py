#! /usr/bin/python3

import csv
import tabulate
import sys


def print_logfile_tabulate(file):
    """function to print log file csv"""
    with open(file, "r") as f:
        csv_reader = csv.reader(f)
        rows = list(csv_reader)
        print(tabulate.tabulate(rows, tablefmt="pipe"))


if __name__ == "__main__":
    # get the file need to be printed as args
    if len(sys.argv) > 1:
        file = sys.argv[1]
        print_logfile_tabulate(file)
