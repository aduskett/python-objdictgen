import sys
import os
import copy
import re
from collections import OrderedDict
import json
import jsonschema

from .node import Node
from . import node as nod
from . import SCHEMA_FILE
from . import dbg

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


def remove_jasonc(text):
    ''' Remove jsonc annotations '''
    # Copied from https://github.com/NickolaiBeloguzov/jsonc-parser/blob/master/jsonc_parser/parser.py#L11-L39
    def __re_sub(match):
        if match.group(2) is not None:
            return ""
        else:
            return match.group(1)

    return re.sub(
        r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)",
        __re_sub,
        text,
        flags=re.MULTILINE | re.DOTALL
    )


if sys.version_info[0] >= 3:
    with open(os.path.join(SCHEMA_FILE), 'r') as f:
        SCHEMA = json.loads(remove_jasonc(f.read()))
else:
    SCHEMA = None


def validate_json(jsonobj):

    if SCHEMA:
        jsonschema.validate(jsonobj, schema=SCHEMA)

    jd = jsonobj
    if not jd['dictionary']:
        raise ValueError("No dictionary values")

    for sindex, obj in jd['dictionary'].items():

        index = str_to_number(sindex)
        if not isinstance(index, int):
            raise ValueError("Invalid dictionary index '%s'" % sindex)
        if index <= 0 or index > 0xFFFF:
            raise ValueError("Invalid dictionary index value '%s'" % index)


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
        dsmap, menumap = nod.ImportProfile(profilename)
        identical = all(
            k in dsmap and k in params and dsmap[k] == params[k]
            for k in set(dsmap) | set(params)
        )
        if menu and not menu == menumap:
            raise ValueError("Menu in OD not idenical with profile")
        return identical

    except ValueError as exc:
        dbg("Loading profile failed: %s" % (exc))
        return False


def GenerateFile(filepath, node):

    jd = node.GetDict()
    # with open(filepath.replace(".json", ".raw.json"), "w") as f:
    #     json.dump(jd, f, separators=(',', ': '), indent=2)

    # Delete the fields that is not needed becuase the code below will access node directory
    for k in ("UserMapping", "DS302", "SpecificMenu", "Profile", "ParamsDictionary", "Dictionary"):
        del jd[k]

    # Rename the top-level fields
    for k, v in {
        'ProfileName': 'profile_name',
        'ID': 'id',
        'DefaultStringSize': 'default_string_size',
        'Description': 'description',
        'Type': 'type',
        'Name': 'name',
    }.items():
        if k in jd:
            jd[v] = jd.pop(k)

    # Make a complete list of the entire object mapping
    mapping = get_all_mappings(node)
    type_names = get_type_names(mapping)

    # Collect the list of user mappings (order preserved)
    dictionary = ODict((
        (k, mapping[k])  # mapping is ok to mutate
        for k in node.UserMapping
    ))

    # Process the DS-302 profile mapping
    jd["ds-302"] = False
    if node.DS302:
        identical = compare_profile("DS-302", node.DS302)
        jd['ds-302'] = identical

        # If profile doesn't match, the DS302 mapping objects is added to the output
        if not identical:
            for index in node.DS302:
                dictionary[index] = mapping[index]

    # Process the profile mapping
    jd["profile"] = False
    if node.Profile:
        identical = compare_profile(node.ProfileName, node.Profile, node.SpecificMenu)
        jd['profile'] = identical

        # If profile doesn't match, the profile mapping output is added to the output
        if not identical:
            for index in node.Profile:
                dictionary[index] = mapping[index]

    # Process the parameters (comments and UI settings)
    for index, paramdict in node.ParamsDictionary.items():
        obj = dictionary.setdefault(index, {})

        # Check the fields in the params dictionary matches the expectation within
        # this code. If not, there is a new field that this code doesn't account for.
        for k in paramdict:
            if isinstance(k, int):  # Corresponds to sub-index data
                for p in paramdict[k]:
                    if p not in PARAM_FIELDS:
                        raise ValueError("Unexpected field '%s' in ParamsDictionary" % p)
            else:  # Corresponds to object data
                if k not in PARAM_FIELDS:
                    raise ValueError("Unexpected field '%s' in ParamsDictionary" % k)

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
                    raise ValueError("A VAR object unexpectedly contains %s sub-indexes" % len(values))
                values[1] = values[0]
                values[0] = {}

            # The first element in values contains "Number of entries" which
            # can be omitted
            else:
                if values[0] and not values[0] == SUBINDEX0:  # Sanity checking.
                    raise ValueError("Unexpected data in sub-index 0: %s" % values[0])
                values[0] = {}

        # Move data from params into values
        params = obj.pop("params", {})
        if params:

            # ARRAY carries N items which must be added to sub-index 1 values
            if struct in (nod.OD.ARRAY, nod.OD.NARRAY):
                if max(params) > 0:
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
            if params:
                raise ValueError("Unexpected remaining parameters: %s" % params)

            # The ParamsDictionary might contain item 0 that has to be moved
            # The keys is be limited to PARAM_FIELDS as it has been checked above
            if values.get(0):

                # Move to either value[1] or to top-level, depending on type
                if struct in (nod.OD.ARRAY, nod.OD.NARRAY):
                    values[1].update(values.pop(0))
                else:
                    obj.update(values.pop(0))

        # Convert values dict to list
        values = [values[i] for i in sorted(values) if values[i]]
        if values:
            obj["sub"] = values

        # Delete empty group values
        if "group" in obj and not obj["group"]:
            del obj["group"]

        # Rename the mandatory field
        if "need" in obj:
            obj["mandatory"] = obj.pop("need")

        # Replace numerical struct with symbolic value
        if TEXT_FIELDS:
            obj["struct"] = nod.OD.to_string(struct, struct)

        if RICH and "name" not in obj:
            obj["__name"] = node.GetEntryName(index)

        if RICH and "struct" not in obj:
            obj["__struct"] = nod.OD.to_string(struct, struct)

        # Iterater over the sub-indexes (if present)
        for i, sub in enumerate(obj.get("sub", [])):

            # Replace numeric type with string value
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
            if 'values' in sub:
                sub["values"] = [
                    copy_in_order(d, (
                        "name", "__name", "comment", "buffer_size", "save",
                        "value",
                    ))
                    for d in sub["values"]
                ]

        # Rearrage order of Dictionary[*]["sub"]
        if "sub" in obj:
            obj["sub"] = [
                copy_in_order(d, (
                    "__name", "__type", "name", "comment", "type", "access",
                    "pdo", "nbmax", "buffer_size", "save", "value", "values",
                ))
                for d in obj["sub"]
            ]

    # Rearrange order of Dictionary[*]
    # Convert the key to hex
    jd["dictionary"] = ODict((
        ("0x%04X" % k, copy_in_order(v, (
            "index", "name", "__name", "comment", "struct", "__struct", "size",
            "mandatory", "group", "default", "callback", "buffer_size", "save",
            "values", "sub",
        )))
        for k, v in dictionary.items()
    ))

    # Rearrange the order of the top-level dict
    jd = copy_in_order(jd, (
        "name", "description", "type", "id", "profile_name", "profile", "ds-302",
        "default_string_size", "dictionary",
    ))

    # Generate the json string
    text = json.dumps(jd, separators=(',', ': '), indent=2)

    # Convert the special __ fields to jasonc comments
    out = re.sub(
        r'^(\s*)"__(\w+)": "(.*)",$',
        r'\1// \2: \3',
        text,
        flags=re.MULTILINE,
    )

    # Writeout the json
    with open(filepath, "w") as f:
        f.write(out)


def GenerateNode(filepath):

    # Read the json file
    with open(filepath, "r") as f:
        text = f.read()

    # Remove jsonc annotations
    jsontext = remove_jasonc(text)

    # Load the json, with awareness on ordering in py2
    if sys.version_info[0] < 3:
        jd = json.loads(jsontext, object_pairs_hook=deunicodify_hook)
    else:
        jd = json.loads(jsontext)

    # Remove all underscore from the file
    jd = remove_underscore(jd)

    # Validate the input json
    validate_json(jd)

    # Create default values for optional components
    jd.setdefault("id", 0)
    jd.setdefault("profile", False)
    jd.setdefault("ds-302", False)
    jd.setdefault("profile_name", "None")

    # Create the node and fill the most basic data
    node = Node(name=jd["name"], type=jd["type"], id=jd["id"],
                description=jd["description"], profilename=jd["profile_name"])

    # Restore optional values
    if 'default_string_size' in jd:
        node.DefaultStringSize = jd["default_string_size"]

    # Load the DS-302 profile
    if jd.get("ds-302"):
        dsmap, menumap = nod.ImportProfile("DS-302")
        node.DS302 = dsmap

    # Load the custom profile
    if jd.get("profile"):
        dsmap, menumap = nod.ImportProfile(node.ProfileName)
        node.Profile = dsmap
        node.SpecificMenu = menumap

    # PASS 1: Add the od parameters to the node variable dictionaries
    dictionary = {}
    for index_str, obj in jd.get("dictionary", {}).items():
        index = str_to_number(index_str)

        # Add the object to the dictionary
        dictionary[index] = obj

        # Rename fields
        if 'mandatory' in obj:
            obj['need'] = obj.pop('mandatory')

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

    # Make a complete list of the entire object mapping
    mapping = get_all_mappings(node)
    type_index = {v: k for k, v in get_type_names(mapping).items()}

    # PASS 2: Parse the data
    for index, obj in dictionary.items():

        # Setup vars
        struct = obj["struct"]
        sublist = obj.pop("sub", [])
        values = None

        # Restore the Dictionary values (if present)
        if sublist:
            if struct in (nod.OD.VAR, nod.OD.NVAR):
                node.Dictionary[index] = sublist[0].pop("value")
            elif struct in (nod.OD.ARRAY, nod.OD.NARRAY):
                values = [v.pop("value", NA) for v in sublist[0]["values"]]
            else:
                values = [v.pop("value", NA) for v in sublist]

        # Commit the dictionary if it has any data
        if values:
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
        if sublist and struct in (nod.OD.ARRAY, nod.OD.NARRAY):
            for i, sub in enumerate(sublist[0]["values"]):

                # Move parameter fields to params
                for k in list(k for k in sub if k in PARAM_FIELDS):
                    params.setdefault(i + 1, {})[k] = sub.pop(k)

            # At this point values should be empty
            nonempty = sublist[0].pop("values")
            if any(nonempty):
                raise ValueError("Values is not empty: %s" % nonempty)

        # Copy params from index 0 directly into the ParamsDictionary object.
        # for some reason expects Node() to find params for these types directly
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
