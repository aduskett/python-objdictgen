from __future__ import absolute_import
from pprint import pformat
import sys
import getopt
import argparse
import functools
import logging
import attr
from colorama import init, Fore, Style

from . import nodemanager as nman
from . import jsonod
from . import ODG_VERSION, ODG_PROGRAM

# For colored output
init()

# Initalize the python logger to simply output to stdout
log = logging.getLogger()
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler(sys.stdout))


@attr.s
class DebugOpts(object):
    ''' Options for main to control the debug_wrapper '''
    show_debug = attr.ib(default=False)

    def set_debug(self, dbg):
        self.show_debug = dbg

        log.setLevel(logging.DEBUG)


def debug_wrapper():
    ''' Wrapper to catch all exceptions and supress the output unless debug
        is set
    '''
    def decorator(fn):
        @functools.wraps(fn)
        def inner(*args, **kw):
            opts = DebugOpts()
            try:
                return fn(opts, *args, **kw)
            except Exception as exc:
                if opts.show_debug:
                    raise
                print("{}: {}: {}".format(ODG_PROGRAM, exc.__class__.__name__, exc))
                sys.exit(1)
        return inner
    return decorator


def open_od(fname, validate=True, fix=False):
    ''' Open and validate the OD file'''

    od = nman.NodeManager()
    od.OpenFileInCurrent(fname)

    if validate and od.CurrentNode:
        od.CurrentNode.Validate(fix=fix)

    return od


def print_diffs(diffs, show=False):

    def _pprint(text):
        for line in pformat(text).splitlines():
            print("       ", line)

    def _printlines(entries):
        for chtype, change, path in entries:
            if 'removed' in chtype:
                print("<<<     {} only in LEFT".format(path))
                if show:
                    _pprint(change.t1)
            elif 'added' in chtype:
                print("    >>> {} only in RIGHT".format(path))
                if show:
                    _pprint(change.t2)
            elif 'changed' in chtype:
                print("<< - >> {} value changed from '{}' to '{}'".format(path, change.t1, change.t2))
            else:
                print("{}{} {} {}{}".format(Fore.RED, chtype, path, change, Style.RESET_ALL))

    rest = diffs.pop('', None)
    if rest:
        print("{}Changes:{}".format(Fore.GREEN, Style.RESET_ALL))
        _printlines(rest)

    for index in sorted(diffs):
        print("{}Index 0x{:04x} ({}){}".format(Fore.GREEN, index, index, Style.RESET_ALL))
        _printlines(diffs[index])


@debug_wrapper()
def main(debugopts, args=None):
    ''' Main command dispatcher '''

    parser = argparse.ArgumentParser(
        prog=ODG_PROGRAM,
        description="""
            A tool to read and convert object dictionary files for the
            CAN festival library
        """,
        add_help=True,
    )

    # FIXME: New options: new file, add parameter, delete parameter, copy parameter

    kw = dict(required=True) if sys.version_info[0] >= 3 else {}
    subparser = parser.add_subparsers(title="command", dest="command", metavar="command", help='''
        Commands
    ''', **kw)


    # -- COMMON --
    opt_debug = dict(action='store_true', help="Debug: enable tracebacks on errors")
    opt_od = dict(metavar='od', default=None, help="Object dictionary")

    parser.add_argument('--version', action='version', version='%(prog)s ' + ODG_VERSION)
    parser.add_argument('-D', '--debug', **opt_debug)

    # -- HELP --
    subp = subparser.add_parser('help', help='''
        Show help of all commands
    ''')
    subp.add_argument('-D', '--debug', **opt_debug)

    # -- CONVERT --
    kw = dict(aliases=['gen', 'conv']) if sys.version_info[0] >= 3 else {}
    subp = subparser.add_parser('convert', help='''
        Generate
    ''', **kw)
    subp.add_argument('od', **opt_od)
    subp.add_argument('out', default=None, help="Output file")
    subp.add_argument('-i', '--index', action="append", help="OD Index to include. Filter out the rest.")
    subp.add_argument('-f', '--fix', action="store_true", help="Fix any inconsistency errors in OD before generate output")
    subp.add_argument('-t', '--type', choices=['od', 'eds', 'json', 'c'], help="Select output file type")
    subp.add_argument('--internal', action="store_true", help="Store in internal format (json only)")
    subp.add_argument('--nosort', action="store_true", help="Don't order of parameters in output OD")
    subp.add_argument('--novalidate', action="store_true", help="Don't validate files before conversion")
    subp.add_argument('-D', '--debug', **opt_debug)

    # -- DIFF --
    kw = dict(aliases=['compare']) if sys.version_info[0] >= 3 else {}
    subp = subparser.add_parser('diff', help='''
        Compare OD files
    ''', **kw)
    subp.add_argument('od1', **opt_od)
    subp.add_argument('od2', **opt_od)
    subp.add_argument('--internal', action="store_true", help="Diff internal object")
    subp.add_argument('--novalidate', action="store_true", help="Don't validate input files before diff")
    subp.add_argument('--show', action="store_true", help="Show difference data")
    subp.add_argument('-D', '--debug', **opt_debug)

    # -- EDIT --
    subp = subparser.add_parser('edit', help='''
        Edit OD (UI)
    ''')
    subp.add_argument('od', nargs="*", help="Object dictionary")
    subp.add_argument('-D', '--debug', **opt_debug)

    # -- LIST --
    subp = subparser.add_parser('list', help='''
        List
    ''')
    subp.add_argument('od', nargs="+", help="Object dictionary")
    subp.add_argument('-i', '--index', action="append", help="Specify parameter index to show")
    subp.add_argument('--all', action="store_true", help="Show all subindexes, including subindex 0")
    subp.add_argument('--asis', action="store_true", help="Do not sort output")
    subp.add_argument('--compact', action="store_true", help="Compact listing")
    subp.add_argument('--header', action="store_true", help="List header only")
    subp.add_argument('--raw', action="store_true", help="Show raw parameter values")
    subp.add_argument('--short', action="store_true", help="Do not list sub-index")
    subp.add_argument('--unused', action="store_true", help="Include unused profile parameters")
    subp.add_argument('-D', '--debug', **opt_debug)

    # -- NETWORK --
    subp = subparser.add_parser('network', help='''
        Edit network (UI)
    ''')
    subp.add_argument('dir', nargs="?", help="Project directory")
    subp.add_argument('-D', '--debug', **opt_debug)

    # -- NODELIST --
    subp = subparser.add_parser('nodelist', help='''
        List project nodes
    ''')
    subp.add_argument('dir', nargs="?", help="Project directory")
    subp.add_argument('-D', '--debug', **opt_debug)


    # -- COMMON --

    # Parse command-line arguments
    opts = parser.parse_args(args)

    # Enable debug mode
    if opts.debug:
        debugopts.set_debug(opts.debug)


    # -- HELP command --
    if opts.command == "help":
        parser.print_help()
        print()

        for subparsers_action in (a for a in parser._actions
                                  if isinstance(a, argparse._SubParsersAction)):
            for choice, subparser in subparsers_action.choices.items():
                print("command '{}'".format(choice))
                for info in subparser.format_help().split('\n'):
                    print("    " + info)


    # -- CONVERT command --
    if opts.command in ("convert", "conv", "gen"):

        od = open_od(opts.od, fix=opts.fix)

        # If index is specified, strip away everything else
        if opts.index:
            index = [jsonod.str_to_number(i) for i in opts.index]
            node = od.CurrentNode
            node.Profile = {k: v for k, v in node.Profile.items() if k in index}
            node.Dictionary = {k: v for k, v in node.Dictionary.items() if k in index}
            node.ParamsDictionary = {k: v for k, v in node.ParamsDictionary.items() if k in index}
            node.UserMapping = {k: v for k, v in node.UserMapping.items() if k in index}

        # Write the data
        od.SaveCurrentInFile(opts.out,
            filetype=opts.type, sort=not opts.nosort,
            internal=opts.internal, validate=not opts.novalidate
        )


    # -- DIFF command --
    elif opts.command in ("diff", "compare"):
        if sys.version_info[0] < 3:
            parser.error("diff does not work with python 2")

        od1 = open_od(opts.od1, validate=not opts.novalidate)
        od2 = open_od(opts.od2, validate=not opts.novalidate)

        diffs = jsonod.diff_nodes(
            od1.CurrentNode, od2.CurrentNode, as_dict=not opts.internal,
            validate=not opts.novalidate,
        )

        if diffs:
            errcode = 1
            print("{}: '{}' and '{}' differ".format(ODG_PROGRAM, opts.od1, opts.od2))
        else:
            errcode = 0
            print("{}: '{}' and '{}' are equal".format(ODG_PROGRAM, opts.od1, opts.od2))

        print_diffs(diffs, show=opts.show)
        parser.exit(errcode)


    # -- EDIT command --
    elif opts.command == "edit":

        # Import here to prevent including optional UI components for cmd-line use
        from .ui.objdictedit import uimain  # pylint: disable=import-outside-toplevel
        uimain(opts.od)


    # -- LIST command --
    elif opts.command == "list":

        for n, name in enumerate(opts.od):

            if n > 0:
                print()
            if len(opts.od) > 1:
                s = name
                print(Fore.LIGHTBLUE_EX + s + '\n' + "="*len(s) + Style.RESET_ALL)

            od = open_od(name)
            node = od.CurrentNode
            assert node  # For mypy

            # Get the indexes to print and determine the order
            keys = node.GetAllParameters(sort=not opts.asis)
            if opts.index:
                index = tuple(jsonod.str_to_number(i) for i in opts.index)
                keys = tuple(k for k in keys if k in index)
                missing = ", ".join((str(k) for k in index if k not in keys))
                if missing:
                    parser.error("Unknown index {}".format(missing))

            profiles = []
            if node.DS302:
                loaded, equal = jsonod.compare_profile("DS-302", node.DS302)
                if equal:
                    extra = "DS-302 (equal)"
                elif loaded:
                    extra = "DS-302 (not equal)"
                else:
                    extra = "DS-302 (not loaded)"
                profiles.append(extra)

            pname = node.ProfileName
            if pname and pname != 'None':
                loaded, equal = jsonod.compare_profile(pname, node.Profile, node.SpecificMenu)
                if equal:
                    extra = "%s (equal)" % pname
                elif loaded:
                    extra = "%s (not equal)" % pname
                else:
                    extra = "%s (not loaded)" % pname
                profiles.append(extra)

            if not opts.compact:
                print("File:      %s" % (od.GetCurrentFilePath()))
                print("Name:      %s  [%s]  %s" % (node.Name, node.Type.upper(), node.Description))
                print("Profiles:  %s" % (", ".join(profiles) or None))
                if node.ID:
                    print("ID:        %s" % (node.ID))
                print("")

            if opts.header:
                continue

            # Print the parameters
            for line in node.PrintParams(keys=keys, short=opts.short, compact=opts.compact, unused=opts.unused, verbose=opts.all, raw=opts.raw):
                print(line)


    # -- NETWORK command --
    elif opts.command == "network":

        # Import here to prevent including optional UI components for cmd-line use
        from .ui.networkedit import uimain  # pylint: disable=import-outside-toplevel
        uimain(opts.dir)


    # -- NODELIST command --
    elif opts.command == "nodelist":

        # Import here to prevent including optional UI components for cmd-line use
        from .nodelist import main as _main  # pylint: disable=import-outside-toplevel
        _main(opts.dir)


    else:
        parser.error("Programming error: Uknown option '%s'" %(opts.command))


def main_objdictgen():
    """ Legacy objdictgen command """

    def usage():
        print("\nUsage of objdictgen :")
        print("\n   %s XMLFilePath CFilePath\n" % sys.argv[0])

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)

    for opt, _ in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()

    filein = ""
    fileout = ""
    if len(args) == 2:
        filein = args[0]
        fileout = args[1]
    else:
        usage()
        sys.exit()

    if filein != "" and fileout != "":
        manager = nman.NodeManager()
        print("Parsing input file", filein)
        manager.OpenFileInCurrent(filein)
        print("Writing output file", fileout)
        manager.ExportCurrentToCFile(fileout)
        print("All done")


def main_objdictedit():
    """ Legacy objdictedit command """

    # Import here to prevent including optional UI components for cmd-line use
    from .ui.objdictedit import main as _main  # pylint: disable=import-outside-toplevel
    _main()


# To support -m objdictgen
if __name__ == '__main__':
    main()
