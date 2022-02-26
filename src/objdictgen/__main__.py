from __future__ import absolute_import
import sys
import getopt

from . import nodemanager as nman


def usage_objdictgen():
    print("\nUsage of objdictgen :")
    print("\n   %s XMLFilePath CFilePath\n" % sys.argv[0])


def main_objdictgen():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError:
        # print help information and exit:
        usage_objdictgen()
        sys.exit(2)

    for opt, _ in opts:
        if opt in ("-h", "--help"):
            usage_objdictgen()
            sys.exit()

    filein = ""
    fileout = ""
    if len(args) == 2:
        filein = args[0]
        fileout = args[1]
    else:
        usage_objdictgen()
        sys.exit()

    if filein != "" and fileout != "":
        manager = nman.NodeManager()
        print("Parsing input file")
        manager.OpenFileInCurrent(filein)
        print("Writing output file")
        manager.ExportCurrentToCFile(fileout)
        print("All done")


def main_objdictedit():
    # Import here to prevent including optional UI components for cmd-line use
    from .ui.objdictedit import main as _main  # pylint: disable=import-outside-toplevel
    _main()


# To support -m objdictgen
if __name__ == '__main__':
    main_objdictgen()
