import sys

from tsel import Tsel

def tsel_cli():
    tsel = Tsel()
    tsel.main()


if __name__ == '__main__':
    sys.exit(tsel_cli())
