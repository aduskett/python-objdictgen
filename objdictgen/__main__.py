from __future__ import absolute_import


def objdictgen_main():
    from .objdictgen import main as _objdictgen_main
    _objdictgen_main()


def objdictedit_main():
    from .objdictedit import main as _objdictedit_main
    _objdictedit_main()


# To support -m objdictgen
if __name__ == '__main__':
    from .objdictgen import main as _objdictgen_main
    _objdictgen_main()
