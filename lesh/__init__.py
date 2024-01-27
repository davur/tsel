#!/usr/bin/env python3

"""lesh helps filter, sort and display tabular data

Usage:
  lesh.py --file=FILE --select=NAME,AGE
  lesh.py --select NAME,AGE
  lesh.py --select NAME,AGE --where STATUS=Pending --order-by NAME
  lesh.py [options]
  lesh.py [--help | --version]

Options:
  -h, --help             Show this screen.
  -d, --debug            Print debug information.
  -f, --file=FILE        Read from file [default: -].
  -i, --interactive      Enable interactive mode.
  -o, --order-by=COLUMN  Sort output by COLUMN.
  -s, --select=COLUMNS   Select column names [Default: ALL].
  -v, --verbose          Give more output. Option is additive, and can be used
  -V, --version          Show version.
  -w, --where COL=Value  Show only rows matching predicate.
"""
from docopt import docopt

from utils import dprint
import utils

import sys
import curses
from curses import wrapper


class Lesh:

    headerline = None
    lines = None
    columns = None  # dict of column_name => (start, end) character indices

    select_columns = None

    interactive = False

    def load_infile(self, infile):
        lines = None
        if infile == '-':
            lines = sys.stdin.read().splitlines()
        else:
            with open(infile, 'r', encoding='UTF-8') as file:
                lines = file.read().splitlines()

        self.headerline = lines.pop(0)
        self.lines = lines

        column_names = self.headerline.split()
        if not len(column_names) == len(set(column_names)):
            raise NotImplementedError("Duplicate column names not supported")

        # Work out column name => (start, end) character indices
        columns = dict()
        start = 0
        c = None
        while len(column_names):
            c = column_names.pop(0)

            if len(column_names):
                c2 = column_names[0]
                stop = self.headerline.index(c2, len(c))
            else:
                stop = len(self.headerline)

            columns[c] = (start, stop)
            start = stop

        # Get last column width from data
        max_length = start
        for line in lines:
            max_length = max(max_length, len(line))
        columns[c] = (columns[c][0], max_length)

        self.columns = columns

    def main(self):
        arguments = docopt(str(__doc__), version="0.0.1")

        debug = arguments['--debug']
        utils.debug = bool(debug)
        if debug:
            dprint(arguments)

        filename = arguments['--file']
        self.load_infile(filename)

        self.interactive = arguments['--interactive']

        self.select_columns = arguments['--select']
        if self.select_columns == 'ALL':
            self.select_columns = None
        else:
            self.select_columns = [c.strip()
                                   for c in self.select_columns.split(',')]

        self.print()


    def print(self):

        if not self.select_columns:
            print(self.headerline)
        else:
            for c in self.select_columns:
                start, stop = self.columns[c]
                if len(self.headerline) > start:
                    width = stop - start
                    print(f'{self.headerline[start:stop]: <{width}}', end='')
            print()

        for line in self.lines:
            if not self.select_columns:
                print(line)
                continue

            for c in self.select_columns:
                start, stop = self.columns[c]
                if len(line) > start:
                    width = stop - start
                    print(f'{line[start:stop]: <{width}}', end='')
            print()


if __name__ == '__main__':
    lesh = Lesh()
    lesh.main()
    # lesh.interactive()

