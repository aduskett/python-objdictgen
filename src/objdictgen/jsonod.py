import sys
import os
import copy
from collections import OrderedDict
import json

from .node import Node
from . import node as nod
from . import dbg, SCRIPT_DIRECTORY

if sys.version_info[0] >= 3:
    unicode = str  # pylint: disable=invalid-name
    long = int  # pylint: disable=invalid-name
    ODict = dict
else:
    ODict = OrderedDict


class NA(object):
    """ Not applicable """


SUBINDEX0 = {
    "name": "Number of Entries",
    "type": 5,
    "pdo": False,
    "access": "ro",
}

IN_PARAMS = (
    "callback",
)

PARAM_FIELDS = (
    "buffer_size",
    "comment",
    "callback",
    "save",
)

RICH = True
TEXT_FIELDS = True


def deunicodify_hook(pairs):
    """ json convert helper for py2, where OrderedDict is used to preserve
        dict order
    """
    new_pairs = []
    for key, value in pairs:
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        new_pairs.append((key, value))
    return OrderedDict(new_pairs)


def str_to_number(string):
    if string is None or isinstance(string, (int, float, long)):
        return string
    s = string.strip()
    if s.startswith('0x') or s.startswith('-0x'):
        return int(s.replace('0x', ''), 16)
    if s.isdigit():
        return int(string)
    return string


def copy_in_order(d, order):
    out = ODict(
        (k, d[k])
        for k in order
        if k in d
    )
    out.update(ODict(
        (k, v)
        for k, v in d.items()
        if k not in out
    ))
    return out


def remove_underscore(d):
    if isinstance(d, dict):
        return {
            k: remove_underscore(v)
            for k, v in d.items()
            if not k.startswith('__')
        }
    if isinstance(d, list):
        return [
            remove_underscore(v)
            for v in d
        ]
    return d


def get_all_mappings(node):
    # Make a complete list of the entire mapping
    mapping = {}
    for group, mappings in (
            (None, nod.MAPPING_DICTIONARY),
            (None, node.UserMapping),
            ("profile", node.Profile),
            ("ds302", node.DS302),
    ):
        for index, v in mappings.items():
            obj = v.copy()
            obj.update({
                "group": group,
                # "values": [x.copy() for x in obj['values']]
            })
            mapping[index] = obj
    return mapping


def get_type_names(mapping):
    return {
        k: v["name"]
        for k, v in mapping.items()
        if k < 0x1000
    }


def compare_profile(profilename, params, menu=None):
    try:
        profilepath = os.path.join(SCRIPT_DIRECTORY, "config", "%s.prf" % profilename)
        dsmap, menumap = nod.ImportProfile(profilepath)
        identical = all(
            k in dsmap and k in params and dsmap[k] == params[k]
            for k in set(dsmap) | set(params)
        )
        if menu and not menu == menumap:
            raise ValueError("Menu in OD not idenical with profile")
        # dbg("Identical to %s: %s" % (profilename, identical))
        return identical

    except Exception as exc:  # pylint: disable=broad-except
        dbg("Loading profile failed: %s" % (exc))
        return False


def GenerateFile(filepath, node):

    jd = node.GetDict()
    # with open(filepath.replace(".json", ".raw.json"), "w") as f:
    #     json.dump(jd, f, separators=(',', ': '), indent=2)

    # Make a complete list of the entire mapping
    mapping = get_all_mappings(node)
    type_names = get_type_names(mapping)

    # Start with the list of user mappings
    dictionary = ODict((
        (k, mapping[k])  # mapping is ok to mutate
        for k in node.UserMapping
    ))
    del jd["UserMapping"]

    # Process the DS-302 profile mapping
    del jd["DS302"]
    jd["DS-302"] = False
    if node.DS302:
        # dbg("Have DS302")
        identical = compare_profile("DS-302", node.DS302)
        jd['DS-302'] = identical

        # If profile doesn't match, the DS302 mapping objects is added to the output
        if not identical:
            for index in node.DS302:
                dictionary[index] = mapping[index]

    # Process the profile mapping
    del jd["SpecificMenu"]
    jd["Profile"] = False
    if node.Profile:
        # dbg("Have Profile %s" % node.ProfileName)
        identical = compare_profile(node.ProfileName, node.Profile, node.SpecificMenu)
        jd['Profile'] = identical

        # If profile doesn't match, the profile mapping output is added to the output
        if not identical:
            for index in node.Profile:
                dictionary[index] = mapping[index]

    # Process the parameters (comments and UI settings)
    del jd["ParamsDictionary"]
    for index, paramdict in node.ParamsDictionary.items():
        obj = dictionary.setdefault(index, {})

        # Check the fields in the params dictionary
        for k in paramdict:
            if isinstance(k, int):  # Corresponds to sub-index data
                for p in paramdict[k]:
                    if p not in PARAM_FIELDS:
                        raise Exception("Unexpected field '%s' in ParamsDictionary" % p)
            else:  # Corresponds to "master" data
                if k not in PARAM_FIELDS:
                    raise Exception("Unexpected field '%s' in ParamsDictionary" % k)

        # Make a copy of the parameter dictionary
        params = copy.deepcopy(paramdict)
        obj["params"] = params

        # Move all global data (non-integer items) into a separate index
        zero = {
            k: params[k]
            for k in params if not isinstance(k, int)
        }
        if zero:
            params[-1] = zero  # Global data goes into this index
        for k in zero:
            del params[k]

    # Process the dictionary (values)
    del jd["Dictionary"]
    for index, val in node.Dictionary.items():
        obj = dictionary.setdefault(index, {})
        params = obj.setdefault("params", {})

        # Convert signular values
        if not isinstance(val, list):
            val = [val]

        # Get the range membership
        index_range = nod.GetIndexRange(index)
        is_pdom = index_range.get("name") in ('rpdom', 'tpdom')

        # Map the data into index 1 and upwards
        for i, v in enumerate(val, start=1):
            if v and isinstance(v, int) and is_pdom:
                v = "0x%x" % v
            params.setdefault(i, {})["value"] = v

    # Processing of the collected dictionary
    for index, obj in dictionary.items():

        # The base object contains the full object
        base = mapping[node.GetBaseIndex(index)]

        # The struct describes what kind of object structure this object have
        # See OD_* in node.py
        struct = obj.setdefault("struct", base["struct"])
        offset = 1 if struct not in (nod.OD.VAR, nod.OD.NVAR) else 0

        # Copy the values (aka the sub-indexes) and convert into a dict
        values = {i: v.copy() for i, v in enumerate(obj.pop("values", []))}
        if values:

            # Move index 0 -> index 1 for VAR types
            if struct in (nod.OD.VAR, nod.OD.NVAR):
                if len(values) != 1:
                    raise Exception("Unexpected data in values")
                values[1] = values[0]
                values[0] = {}

            # The first element in values contains "Number of entries" which
            # can be omitted
            else:
                if values[0] and not values[0] == SUBINDEX0:  # Sanity checking.
                    raise Exception("Unexpected inequality in sub-index 0")
                values[0] = {}

        # Move data from params into values
        params = obj.pop("params", {})
        if params:

            # REC carries N items which must be added to sub-index 1 values
            if struct & nod.OD.IdenticalSubindexes:
                values.setdefault(1, {})["values"] = [  # Note the plural values
                    params.pop(i + 1)
                    for i in range(max(params))
                ]

            # Move data from the numbered parameters to values
            for k in list(k for k in params if k != -1):  # list enables mutation of params
                values.setdefault(k, {}).update(params.pop(k))

            # Handle the global parameters
            param0 = params.get(-1)
            if param0:

                # Move any params not listed in IN_PARAMS to values[1]
                # E.g. moves "comment" into "values" instead of in top-object
                if struct in (nod.OD.VAR, nod.OD.NVAR):
                    for k in list(k for k in param0 if k not in IN_PARAMS):
                        values[1][k] = param0.pop(k)

                # Commit the remaining parameters into the parent object
                obj.update(params.pop(-1))

            # At this point, params should be empty
            if len(params):
                raise Exception("Unexpected number of remaining parameters: %s" % list(params.keys()))

            # The ParamsDictionary might contain item 0 that has to be moved
            # The keys is be limited to PARAM_FIELDS as it has been checked above
            if values.get(0):

                # Move to either value[1] or to top-level, depending on type
                if struct in (nod.OD.ARRAY, nod.OD.NARRAY):
                    values[1].update(values.pop(0))
                else:
                    obj.update(values.pop(0))

        # Convert values dict to list
        obj["sub"] = [values[i] for i in sorted(values) if values[i]]

        # Delete empty group values
        if "group" in obj and not obj["group"]:
            del obj["group"]

        if TEXT_FIELDS:
            obj["struct"] = nod.OD.to_string(struct, struct)

        if RICH and "name" not in obj:
            obj["__name"] = node.GetEntryName(index)

        if RICH and "struct" not in obj:
            obj["__struct"] = nod.OD.to_string(struct, struct)

        # Iterater over the sub-indexes
        for i, sub in enumerate(obj["sub"]):

            # Replace numeric types with string
            if TEXT_FIELDS and "type" in sub:
                sub["type"] = type_names.get(sub["type"], sub["type"])

            # Add __name when rich format
            if RICH and "name" not in sub:
                info = node.GetSubentryInfos(index, i + offset)
                sub["__name"] = info["name"]

            # Add __type when rich format
            if RICH and "type" not in sub:
                num = base["values"][i + offset]["type"]
                sub["__type"] = type_names.get(num, num)

            # Iterate over the values (if present)
            for j, val in enumerate(sub.get('values', [])):

                # Add __name to values
                if RICH:
                    info = node.GetSubentryInfos(index, j + offset)
                    val["__name"] = info["name"]

            # Rearrange order of Dictionary[*]["sub"]["values"]
            if sub.get('values'):
                sub["values"] = [
                    copy_in_order(d, (
                        "name", "__name", "comment",
                        "buffer_size", "save",
                        "value"
                    ))
                    for d in sub["values"]
                ]

        # Rearrage order of Dictionary[*]["sub"]
        obj["sub"] = [
            copy_in_order(d, (
                "__name", "__type",
                "name", "comment", "type", "access", "pdo",
                "nbmax", "value", "values",
            ))
            for d in obj["sub"]
        ]

    # Organize the dictionary order, Dictionary[]
    jd["Dictionary"] = ODict((
        ("0x%04X" % k, copy_in_order(v, (
            "index", "name", "__name", "struct", "__struct", "size", "need",
            "group", "default", "callback", "comment", "values", "sub",
        )))
        for k, v in dictionary.items()
    ))

    # Rearrange the order of the top-level dict
    jd = copy_in_order(jd, (
        "Name", "Description", "Type", "ID",
        "ProfileName", "Profile", "DS-302",
        "DefaultStringSize", "SpecificMenu", "Dictionary",
    ))

    # Writeout the json
    with open(filepath, "w") as f:
        json.dump(jd, f, separators=(',', ': '), indent=2)


def GenerateNode(filepath):
    with open(filepath, "r") as f:
        if sys.version_info[0] < 3:
            jd = json.load(f, object_pairs_hook=deunicodify_hook)
        else:
            jd = json.load(f)

    # Create the node and fill the most basic data
    node = Node(name=jd["Name"], type=jd["Type"], id=jd["ID"], description=jd["Description"], profilename=jd["ProfileName"])

    if 'DefaultStringSize' in jd:
        node.DefaultStringSize = jd["DefaultStringSize"]

    # Load the DS-302 profile
    if jd.get("DS-302"):
        profilename = "DS-302"
        profilepath = os.path.join(SCRIPT_DIRECTORY, "config", "%s.prf" % profilename)
        dsmap, menumap = nod.ImportProfile(profilepath)
        node.DS302 = dsmap

    # Load the custom profile
    if jd.get("Profile"):
        profilename = node.ProfileName
        profilepath = os.path.join(SCRIPT_DIRECTORY, "config", "%s.prf" % profilename)
        dsmap, menumap = nod.ImportProfile(profilepath)
        node.Profile = dsmap
        node.SpecificMenu = menumap

    # PASS 1: Add the od parameters to the node variable dictionaries
    dictionary = {}
    for index_str, obj in jd.get("Dictionary", {}).items():
        index = str_to_number(index_str)

        # Remove any entries starting with __
        obj = remove_underscore(obj)
        dictionary[index] = obj

        # Get the type of structure
        if "struct" not in obj:
            raise Exception("Missing 'struct' member")
        struct = obj["struct"]
        if not isinstance(struct, int):
            obj["struct"] = nod.OD.from_string(struct)

        # Get the parameter group (None, "profile", "ds302")
        group = obj.pop("group", None)

        # Add the objects to the corresponding dictionaries
        if 'name' in obj:
            if group == "profile":
                node.Profile[index] = obj
            elif group == "ds302":
                node.DS302[index] = obj
            else:
                node.UserMapping[index] = obj

    # Make a complete list of the entire mapping
    mapping = get_all_mappings(node)
    type_index = {v: k for k, v in get_type_names(mapping).items()}

    # PASS 2: Parse the data
    for index, obj in dictionary.items():

        # Setup vars
        struct = obj["struct"]
        sublist = obj.pop("sub", [])

        # Restore the Dictionary values
        if struct in (nod.OD.VAR, nod.OD.NVAR):
            if "value" in sublist[0]:
                node.Dictionary[index] = sublist[0].pop("value")
                values = None
        elif struct & nod.OD.IdenticalSubindexes:
            values = [v.pop("value", NA) for v in sublist[0]["values"]]
        else:
            values = [v.pop("value", NA) for v in sublist]

        # Commit the dictionary
        if isinstance(values, list):
            values = [str_to_number(v) for v in values if v is not NA]
            if values:
                node.Dictionary[index] = values

        # Restore the ParamDictionary values
        params = {}

        # Restore params from top-object
        for k in list(k for k in obj if k in PARAM_FIELDS):
            if k in IN_PARAMS:
                params[k] = obj.pop(k)
            else:
                params.setdefault(0, {})[k] = obj.pop(k)

        # Restore Params values from sub
        for i, sub in enumerate(sublist):

            # Parse the type names and replace "UNSIGNED8" -> 5
            if 'type' in sub:
                if isinstance(sub["type"], (str, )):
                    sub["type"] = type_index[sub["type"]]

            # Move parameter fields to params
            offset = 1 if struct in (nod.OD.RECORD, nod.OD.NRECORD) else 0
            for k in list(k for k in sub if k in PARAM_FIELDS):  # list enabled use of pop
                params.setdefault(i + offset, {})[k] = sub.pop(k)

        # Restore Params values for N equal entries of the same type
        if struct in (nod.OD.ARRAY, nod.OD.NARRAY):
            for i, sub in enumerate(sublist[0]["values"]):

                # Move parameter fields to params
                for k in list(k for k in sub if k in PARAM_FIELDS):
                    params.setdefault(i + 1, {})[k] = sub.pop(k)

            # At this point values should be empty
            nonempty = any(sublist[0].pop("values"))
            if nonempty:
                raise Exception("Values is not empty")

        # For some reason expects Node() to find params for these types directly
        # in params
        if struct in (nod.OD.VAR, nod.OD.NVAR):
            if 0 in params:
                params.update(params.pop(0))

        # Commit values:
        if params:
            node.ParamsDictionary[index] = params

        # Reconstruct the values list
        values = obj.setdefault('values', [])
        if struct not in (nod.OD.VAR, nod.OD.NVAR):
            values.append(SUBINDEX0.copy())
        values.extend(sublist)

    # with open(filepath.replace(".json", ".in.json"), "w") as f:
    #     json.dump(node.__dict__, f, separators=(',', ': '), indent=2)

    return node
