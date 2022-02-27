from __future__ import absolute_import
import sys
import getopt
from argparse import ArgumentParser

from . import nodemanager as nman
from . import node as nod
from . import jsonod
from . import __version__, dbg


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
        print("Parsing input file", filein)
        manager.OpenFileInCurrent(filein)
        print("Writing output file", fileout)
        manager.ExportCurrentToCFile(fileout)
        print("All done")


def main_objdictedit():
    # Import here to prevent including optional UI components for cmd-line use
    from .ui.objdictedit import main as _main  # pylint: disable=import-outside-toplevel
    _main()


def read_od(filename):
    manager = nman.NodeManager()
    if nman.isXml(filename):
        dbg("Loading XML OD '%s'" % filename)
        manager.ImportCurrentFromODFile(filename)
    elif nman.isEds(filename):
        dbg("Loading EDS '%s'" % filename)
        manager.ImportCurrentFromEDSFile(filename, True)
    else:
        dbg("Loading JSON OD '%s'" % filename)
        manager.ImportCurrentFromJsonFile(filename)
    return manager


def write_od(filename, node):
    low = filename.lower() if filename else ''
    if filename == '-':
        low = '.json'
        filename = '/dev/stdout'
    if low.endswith('.od'):
        dbg("Writing XML OD '%s'" % filename)
        node.ExportCurrentToODFile(filename)
    elif low.endswith('.c'):
        dbg("Writing C files '%s'" % filename)
        node.ExportCurrentToCFile(filename)
    elif low.endswith('.eds'):
        dbg("Writing EDS '%s'" % filename)
        node.ExportCurrentToEDSFile(filename)
    elif low.endswith('.json'):
        dbg("Writing JSON OD '%s'" % filename)
        node.ExportCurrentToJsonFile(filename)


def main():

    parser = ArgumentParser(
        prog="odg",
        description="Description",
        add_help=True,
    )
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)

    subparser = parser.add_subparsers(title="command", dest="command", metavar="command", help='''
        Commands
    ''')
    opt_od = {'metavar': 'od', 'default': None, 'help': "Object dictionary"}

    # -- GEN --
    subp = subparser.add_parser('gen', help='''
        Generate
    ''')
    subp.add_argument('--index', '-i', action="append",
                      help="OD Index to include")
    subp.add_argument('od', **opt_od)
    subp.add_argument('out', default=None, help="Output file")

    # -- EDIT --
    subp = subparser.add_parser('edit', help='''
        Edit OD (UI)
    ''')
    subp.add_argument('od', nargs="*", help="Object dictionary")

    # -- NETWORK --
    subp = subparser.add_parser('network', help='''
        Edit network (UI)
    ''')
    subp.add_argument('dir', nargs="?", help="Project directory")

    # -- LIST --
    subp = subparser.add_parser('list', help='''
        List
    ''')
    subp.add_argument('od', **opt_od)
    subp.add_argument('--nosub', action="store_true", help="Do not list sub-index")

    # -- NODELIST --
    subp = subparser.add_parser('nodelist', help='''
        List project nodes
    ''')
    subp.add_argument('dir', nargs="?", help="Project directory")

    # -- COMPARE --
    subp = subparser.add_parser('compare', help='''
        Compare OD
    ''')
    subp.add_argument('od1', **opt_od)
    subp.add_argument('od2', **opt_od)

    # Parse command-line arguments
    opts = parser.parse_args()

    # Read OD
    od = None
    if 'od' in opts and not isinstance(opts.od, list):
        try:
            od = read_od(opts.od)
        except OSError as exc:
            parser.error("%s: %s" % (exc.__class__.__name__, str(exc)))

    # -- GEN command --
    if opts.command == "gen":

        # If index is specified, strip away everything else
        if opts.index:
            index = [jsonod.str_to_number(i) for i in opts.index]
            node = od.CurrentNode
            node.Profile = {k: v for k, v in node.Profile.items() if k in index}
            node.Dictionary = {k: v for k, v in node.Dictionary.items() if k in index}
            node.ParamsDictionary = {k: v for k, v in node.ParamsDictionary.items() if k in index}
            node.UserMapping = {k: v for k, v in node.UserMapping.items() if k in index}

        write_od(opts.out, od)

    # -- EDIT command --
    elif opts.command == "edit":

        # Import here to prevent including optional UI components for cmd-line use
        from .ui.objdictedit import uimain  # pylint: disable=import-outside-toplevel
        uimain(opts.od)

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

    # -- COMPARE command --
    elif opts.command == "compare":

        try:
            od1 = read_od(opts.od1)
            od2 = read_od(opts.od2)
        except OSError as exc:
            parser.error("%s: %s" % (exc.__class__.__name__, str(exc)))

        node1 = od1.CurrentNode.GetDict()
        node2 = od2.CurrentNode.GetDict()

        equal = node1 == node2
        print("OD '%s' and '%s' are %s" % (
            opts.od1,
            opts.od2,
            "EQUAL" if equal else "NOT EQUAL"
        ))
        sys.exit(0 if equal else 1)

    # -- LIST command --
    elif opts.command == "list":

        node = od.CurrentNode

        index_range = None
        for k in sorted(node.Dictionary):

            for ir in nod.INDEX_RANGES:
                if ir["min"] <= k <= ir["max"] and ir != index_range:
                    index_range = ir
                    print(ir["description"])

            obj = node.GetEntryInfos(k)
            name = node.GetEntryName(k)
            struct = obj.get('struct')
            struct = nod.OD.to_string(struct, '???').upper()
            flags = []
            if obj.get('need'):
                flags.append("Mandatory")
            if k in node.UserMapping:
                flags.append("User")
            if k in node.DS302:
                flags.append("DS-302")
            if k in node.Profile:
                flags.append("Profile")
            if node.HasEntryCallbacks(k):
                flags.append('CB')
            flag = ''
            if flags:
                flag = '  ' + ','.join(flags)

            print("    0x%04X (%d)  %s   [%s]%s" % (k, k, name, struct, flag))

            if opts.nosub:
                continue

            values = node.GetEntry(k, aslist=True)
            entries = node.GetParamsEntry(k, aslist=True)

            lines = []
            for i, (value, entry) in enumerate(zip(values, entries)):
                info = node.GetSubentryInfos(k, i)
                info.update(entry)

                if 'COB ID' in info["name"]:
                    value = "0x%x" % (value)
                if i and index_range["name"] in ('rpdom', 'tpdom'):
                    index, subindex, _ = node.GetMapIndex(value)
                    pdo = node.GetSubentryInfos(index, subindex)
                    suffix = '???'
                    if pdo:
                        suffix = '%s' % (pdo["name"],)
                    value = "0x%x  %s" % (value, suffix)
                lines.append({
                    'i': "%02d" % i,
                    'name': info['name'],
                    'access': info["access"],
                    'type': "%s" % node.GetTypeName(info.get('type')),
                    'value': str(value),
                    'pdo': 'P' if info.get('pdo') else ' ',
                    'comment': '/* %s */' % info.get('comment') if info.get('comment') else '',
                })

            w = {
                k: max(len(v[k]) for v in lines)
                for k in lines[0]
            }
            out = "        {i:%ss}  {access:%ss}  {pdo:%ss}  {name:%ss}  {type:%ss}  {value:%ss}  {comment}" % (
                w["i"], w["access"], w["pdo"], w["name"], w["type"], w["value"]
            )
            for line in lines:
                print(out.format(**line))
            print("")


# To support -m objdictgen
if __name__ == '__main__':
    main()
