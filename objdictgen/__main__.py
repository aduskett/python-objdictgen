from __future__ import absolute_import

from .objdictgen import main as _objdictgen_main


def objdictgen_main():
    _objdictgen_main()


# To support -m objdictgen
if __name__ == '__main__':
    _objdictgen_main()
