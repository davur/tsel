#!/usr/bin/env python3

"""tsel helps filter, sort and display tabular data

Usage:
  tsel [--interactive] [--file=FILE] [--select=COL1,COL2] [--where=CONDITION]
  tsel --select NAME,AGE --where STATUS=Pending --order-by NAME
  tsel [options]
  tsel [--help | --version]

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

import curses
import os
import re
import sys
# from time import sleep

multiple_spaces = re.compile('  +')


class Tsel:

    headerline = None
    lines = None
    columns = None  # dict of column_name => (start, end) character indices
    rows = None
    filtered_rows = None

    select_columns = None
    where = None

    is_interactive = False

    def print_options(self):
        command = ["tsel"]

        if self.select_columns:
            csv = ",".join(self.select_columns)
            command.append(f"--select='{csv}'")
        if self.where:
            condition = f'{self.where[0]}={self.where[1]}'
            command.append(f"--where='{condition}'")
        print(" ".join(command))

    def load_infile(self, infile):
        lines = None
        if infile == '-':
            lines = sys.stdin.read().splitlines()
        else:
            with open(infile, 'r', encoding='UTF-8') as file:
                lines = file.read().splitlines()

        self.headerline = lines.pop(0)
        self.lines = lines

        column_names = multiple_spaces.split(self.headerline)
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
                stop = self.headerline.index(c2, start)
            else:
                stop = len(self.headerline)

            columns[c] = (len(columns), start, stop)
            start = stop

        # Get last column width from data
        max_length = start
        for line in lines:
            max_length = max(max_length, len(line))
        columns[c] = (columns[c][0], columns[c][1], max_length)

        self.columns = columns

        rows = []
        for line in lines:
            row = []
            for col in columns:
                _, start, stop = columns[col]
                row.append(line[start:stop].strip())
            rows.append(row)
        self.rows = rows


    def main(self):
        arguments = docopt(str(__doc__), version="0.0.1")

        debug = arguments['--debug']
        if debug:
            print(arguments)

        filename = arguments['--file']
        self.load_infile(filename)

        self.is_interactive = arguments['--interactive']

        self.select_columns = arguments['--select']
        if (not self.select_columns) or self.select_columns == 'ALL':
            self.select_columns = list(self.columns.keys())
        else:
            self.select_columns = [c.strip()
                                   for c in self.select_columns.split(',')]
        where = arguments['--where']
        if where:
            parts = where.split("=", 1)
            if len(parts) == 2:
                col, val = parts
                if col not in self.columns:
                    print("Unknown column '{col}' found in --where")
                    exit()
                self.where = (col, val)
                self.filtered_rows = [row for row in self.rows if
                                      row[self.columns[col][0]] == val]
        if not self.where:
            self.filtered_rows = list(self.rows)

        if self.is_interactive:
            curses.wrapper(self.interactive)
            self.print_options()
        else:
            self.table()

    def interactive(self, w):

        f = open("/dev/tty")
        os.dup2(f.fileno(), 0)


        y = 0
        selected = 0

        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_GREEN)
            curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_CYAN)

        ri = 0

        while True:
            w.clear()
            maxr, maxc = w.getmaxyx()
            self.table(w.addstr, ri, 0, ri + maxr - 2, maxc - 2)

            ch = w.getch()
            if ch == ord('q'): # q
                break
            if ch == ord('s'):
                self.select_prompt(w)
            elif ch == ord('w'):
                self.where_prompt(w)
            if ch == ord('j'):
                ri += 1
                ri = min(ri, len(self.filtered_rows))
            if ch == ord('k'):
                ri -= 1
                ri = max(0, ri)
            else:
                s = f'{ch=}'
                self.statusline(w, s)


    def all_columns(self):
        cols = list(self.select_columns)
        for col in self.columns.keys():
            if col not in cols:
                cols.append(col)
        return cols

    def statusline(self, w, msg):
        rows, cols = w.getmaxyx()
        w.addstr(rows - 2, 0, f'{msg: <{cols}}', curses.A_STANDOUT)
        # TODO look into why just rows throws error, but rows - 2 doesn't
        #   File "/Users/davur/repos/davur/tsel/tsel/__init__.py", line 130, in interactive
        # self.select_prompt(w)
        # File "/Users/davur/repos/davur/tsel/tsel/__init__.py", line 206, in select_prompt
        # self.statusline(w, msg)
        # File "/Users/davur/repos/davur/tsel/tsel/__init__.py", line 150, in statusline
        # w.addstr(68, 0, f'{msg: <{cols}}', curses.A_STANDOUT)
        # _curses.error: addwstr() returned ERR


    def where_prompt(self, w):
        y = 0
        x = 0
        selected_col = 0
        selected_val = 0

        all_columns = self.all_columns()
        distinct_values = [] # ['Ready', 'Cordoned', 'NotReady']

        while True:
            y = 0
            w.clear()
            maxr, maxc = w.getmaxyx()
            w.refresh()
            col = all_columns[selected_col]
            if x == 1 and selected_val < len(distinct_values):
                val = distinct_values[selected_val]
            else:
                val = ""

            if x == 0:
                w.addstr(0, 0, "Choose a column: ", curses.A_BOLD)
            else:
                w.addstr(0, 0, "Choose a value: ", curses.A_BOLD)

            msg = f"--where='{col}={val}'"
            self.statusline(w, msg)

            for col in all_columns:
                attr = 0
                if y < len(self.select_columns):
                    attr |= curses.A_BOLD
                    prefix = ' '
                else:
                    attr |= curses.A_DIM
                    prefix = ' '
                if y == selected_col:
                    attr |= curses.color_pair(1)
                s = f'{prefix}{col: <20}'
                w.addstr(2 + y, 0, s, attr)
                y += 1

            if x == 1:
                y = 0
                for val in distinct_values:
                    attr = 0
                    if y == selected_val:
                        attr |= curses.color_pair(1)
                    s = f'{val: <20}'
                    w.addstr(2 + y, 21, s, attr)
                    y += 1
                    if y > maxr - 5:
                        break


            ch = w.getch()

            # Move cursor
            if ch == 258 or ch == ord('j'): # down
                if x == 0:
                    selected_col += 1
                else:
                    selected_val += 1
            elif ch == 259 or ch == ord('k'): # up
                if x == 0:
                    selected_col -= 1
                else:
                    selected_val -= 1

            if x == 0:
                selected_col %= len(self.columns)
            else:
                selected_val %= len(distinct_values)

            if x == 0 and ch == ord('l'):
                x += 1
                distinct_values = self.distinct_values(all_columns[selected_col])
            elif x == 1 and ch == ord('h'):
                x -= 1

            # Back to table
            if ch == 10: # enter
                if x == 1:
                    col = all_columns[selected_col]
                    val = distinct_values[selected_val]
                    self.where = (col, val)
                    self.filtered_rows = [row for row in self.rows if
                                          row[self.columns[col][0]] == val]
                return


    def select_prompt(self, w):
        y = 0
        selected = 0
        while True:
            y = 0

            w.clear()
            w.refresh()
            all_columns = self.all_columns()

            w.addstr(0, 0, "Choose your columns: ", curses.A_BOLD)
            msg = "--select=%s" % (",".join(self.select_columns))
            self.statusline(w, msg)
            # w.addstr(1, 0, "-" * len(header))

            for col in all_columns:
                attr = 0
                if y < len(self.select_columns):
                    attr |= curses.A_BOLD
                    prefix = ' '
                else:
                    attr |= curses.A_DIM
                    prefix = ' '
                if y == selected:
                    attr |= curses.color_pair(1)
                s = f'{prefix}{col: <20}'
                w.addstr(2+y, 0, s, attr)
                y += 1

            ch = w.getch()

            # Move cursor
            if ch == 258 or ch == 106: # down
                selected += 1
            if ch == 259 or ch == 107: # up
                selected -= 1
            selected %= len(self.columns)

            # Move column under cursor
            if ch == 75 or ch == 104 or ch == 260: # move up
                if 0 < selected < len(self.select_columns):
                    col = self.select_columns[selected]
                    self.select_columns.pop(selected)
                    selected -= 1
                    self.select_columns.insert(selected, col)
            if ch == 74 or ch == 108 or ch == 261: # move down
                if selected < len(self.select_columns) - 1:
                    col = self.select_columns[selected]
                    self.select_columns.pop(selected)
                    selected += 1
                    self.select_columns.insert(selected, col)

            # Toggle column
            if ch == 32: # space
                if selected < len(self.select_columns):
                    self.select_columns.pop(selected)
                else:
                    self.select_columns.append(all_columns[selected])

            # Back to table
            if ch == 10: # enter
                return


    def distinct_values(self, col):
        col_index = self.columns[col][0]
        values = set([row[col_index] for row in self.rows])
        values = list(values)
        values.sort()
        return values


    def table(self, write=None, rmin=0, cmin=0, rmax=100, cmax=100):
        if not write:
            write = sys.stdout.write
#         if not self.select_columns:
#             write(self.headerline)
#             write('\n')
#         else:
        ci = 0
        for c in self.select_columns:
            _, start, stop = self.columns[c]
            if len(self.headerline) > start:
                width = stop - start
                if ci + width < cmax:
                    write(f'{self.headerline[start:stop]: <{width}}')
                    ci += width
        write('\n')

        rmin = max(0, rmin)
        rmin = min(rmin, 1+len(self.filtered_rows))
        rmax = min(rmax, 1+len(self.filtered_rows))

        ri = -1

        for row in self.filtered_rows:

            ri += 1
            ci = 0

            if ri < rmin:
                continue
            if ri >= rmax:
                break

#             if not self.select_columns:
#                 write(line)
#                 write('\n')
#                 continue

#             if self.where:
#                 col, val = self.where
#                 if row[self.columns[col][0]] != val:
#                     continue

            for c in self.select_columns:
                index, start, stop = self.columns[c]
                width = stop - start
                if ci + width < cmax:
                    write(f'{row[index]: <{width}}')
                    ci += width
            write('\n')

#         for line in self.lines:
#             if not self.select_columns:
#                 write(line)
#                 write('\n')
#                 continue
#
#             # TODO: Parse table into data structure
#             where = self.where
#             if where:
#                 col, val = where
#                 start, stop = self.columns[col]
#                 cur = line[start:stop]
#                 if cur.strip() != val.strip():
#                     continue
#
#             for c in self.select_columns:
#                 start, stop = self.columns[c]
#                 if len(line) > start:
#                     width = stop - start
#                     write(f'{line[start:stop]: <{width}}')
#             write('\n')


    def print(self):
        for c in self.select_columns:
            start, stop = self.columns[c]
            if len(self.headerline) > start:
                width = stop - start
                print(f'{self.headerline[start:stop]: <{width}}', end='')
        print()

        for line in self.lines:
            for c in self.select_columns:
                start, stop = self.columns[c]
                if len(line) > start:
                    width = stop - start
                    print(f'{line[start:stop]: <{width}}', end='')
            print()
