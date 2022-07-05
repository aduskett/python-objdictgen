from __future__ import absolute_import
import json
import sys
import getopt
from argparse import ArgumentParser
import logging
from colorama import init, Fore, Style

from . import nodemanager as nman
from . import node as nod
from . import jsonod
from . import __version__, dbg

init()
log = logging.getLogger()
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler(sys.stdout))


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


def main(args=None):

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
                      help="OD Index to include. Filter out the rest.")
    subp.add_argument('--correct', action="store_true", help="Correct any inconsistency errors in OD before generate output")
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
    subp.add_argument('--short', action="store_true", help="Do not list sub-index")
    subp.add_argument('--unselected', '--unsel', action="store_true", help="Include unselected profile params")

    # -- NODELIST --
    subp = subparser.add_parser('nodelist', help='''
        List project nodes
    ''')
    subp.add_argument('dir', nargs="?", help="Project directory")

    # -- DIFF --
    subp = subparser.add_parser('diff', help='''
        Diff OD
    ''')
    subp.add_argument('od1', **opt_od)
    subp.add_argument('od2', **opt_od)

    # -- DUMP --
    subp = subparser.add_parser('dump', help='''
        Debug dump
    ''')
    subp.add_argument('od', **opt_od)
    subp.add_argument('out', default=None, help="Output file")

    # Parse command-line arguments
    opts = parser.parse_args(args)

    # Read OD
    od = None
    if 'od' in opts and not isinstance(opts.od, list):
        try:
            od = read_od(opts.od)

            if opts.command not in ("gen", ):
                # Inform about inconsistencies in node
                od.CurrentNode.Validate(correct=False)

        except OSError as exc:
            parser.error("%s: %s" % (exc.__class__.__name__, str(exc)))

    # -- GEN command --
    if opts.command == "gen":

        # Inform about inconsistencies in node and possibly correct contents
        od.CurrentNode.Validate(correct=opts.correct)

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

    # -- DUMP command --
    if opts.command == "dump":

        with open(opts.out, 'w') as f:
            json.dump(od.CurrentNode.__dict__, f, separators=(',', ': '), indent=2)

    # -- DIFF command --
    elif opts.command == "diff":

        try:
            od1 = read_od(opts.od1)
            od2 = read_od(opts.od2)
        except OSError as exc:
            parser.error("%s: %s" % (exc.__class__.__name__, str(exc)))

        changes = od1.CurrentNode.Compare(od2.CurrentNode)
        for change in changes:
            print(change)

        sys.exit(1 if changes else 0)

    # -- LIST command --
    elif opts.command == "list":

        node = od.CurrentNode

        profiles = []
        if node.DS302:
            if jsonod.compare_profile("DS-302", node.DS302):
                extra = "DS-302"
            else:
                extra = "DS-302 (not equal)"
            profiles.append(extra)

        if node.Profile:
            if jsonod.compare_profile(node.ProfileName, node.Profile, node.SpecificMenu):
                extra = node.ProfileName
            else:
                extra = "%s (not equal)" % node.ProfileName
            profiles.append(extra)

        print("File:      %s" % (od.GetCurrentFilePath()))
        print("Name:      %s  [%s]  %s" % (node.Name, node.Type.upper(), node.Description))
        print("Profiles:  %s" % (", ".join(profiles) or None))
        if node.ID:
            print("ID:        %s" % (node.ID))
        print("")

        index_range = None
        for k in sorted(node.GetAllParameters()):

            for ir in nod.INDEX_RANGES:
                if ir["min"] <= k <= ir["max"] and ir != index_range:
                    index_range = ir
                    print(Fore.YELLOW + ir["description"] + Style.RESET_ALL)

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
            if k not in node.Dictionary:
                if k in node.DS302 or k in node.Profile:
                    flags.append("Unselected")
                    if not opts.unselected:
                        continue
                else:
                    flags.append(Fore.RED + " *MISSING* " + Style.RESET_ALL)
            flag = ''
            if flags:
                flag = '  ' + ','.join(flags)

            print("    %s0x%04X (%d)  %s%s   [%s]%s" % (Fore.GREEN, k, k, name, Style.RESET_ALL, struct, flag))

            if opts.short:
                continue

            if k not in node.Dictionary:
                print("")
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
                k: max(len(v[k]) for v in lines) or ''
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
