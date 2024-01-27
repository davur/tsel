from pprint import pprint
import os

debug = True


def char_grid_from_lines(lines):
    grid = []
    for line in lines:
        row = [c for c in line]
        grid.append(row)
    return grid


def read_data_sources(year, day):

    ds_num = 1
    data_sources = {}

    while True:
        num_suffix = '' if ds_num == 1 else f'-{ds_num}'
        in_path = f'year{year}/day{day}.sample{num_suffix}.in'
        p1_path = in_path.replace('.in', '.p1.out')
        p2_path = in_path.replace('.in', '.p2.out')

        in_content = None
        if os.path.isfile(in_path):
            in_content = read(in_path)
        else:
            break

        p1_out = None
        if os.path.isfile(p1_path):
            with open(p1_path, 'r', encoding='UTF-8') as file:
                p1_out = file.read().strip()

        p2_out = None
        if os.path.isfile(p2_path):
            with open(p2_path, 'r', encoding='UTF-8') as file:
                p2_out = file.read().strip()

        data_sources[in_path] = [in_content, p1_out, p2_out]

        ds_num += 1

    return data_sources


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def warn(*args):
    print(f"{bcolors.WARNING}", *args, f"{bcolors.ENDC}")


def dprint(*args):
    if debug:
        print(f"{bcolors.OKBLUE}", *args, f"{bcolors.ENDC}")


def ints(nums):
    return [int(num) for num in nums]


def rotate(grid):
    rotated = list(zip(*grid[::-1]))
    return rotated


def read(file):
    sections = []

    section = []

    lines = []
    with open(file, 'r', encoding='UTF-8') as file:
        for line in file.readlines():
            lines.append(line.rstrip("\n"))

    for line in lines:
        if line:
            section.append(line)
        else:
            sections.append(section)
            section = []
    sections.append(section)
    return sections


