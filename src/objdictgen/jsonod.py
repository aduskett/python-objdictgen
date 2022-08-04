""" OD dict/json serialization and deserialization functions """

from datetime import datetime
import sys
import os
import re
from collections import OrderedDict
import json
import jsonschema
import deepdiff

from .node import Node
from . import node as nod
from . import SCRIPT_DIRECTORY
from . import dbg, warning, ODG_PROGRAM, ODG_VERSION
from . import maps
from .maps import OD

if sys.version_info[0] >= 3:
    unicode = str  # pylint: disable=invalid-name
    long = int  # pylint: disable=invalid-name
    ODict = dict
else:
    ODict = OrderedDict


class ValidationError(Exception):
    ''' Validation failure '''

# JSON Version history/formats
# ----------------------------
# 0 - JSON representation of internal OD memory structure
# 1 - Default JSON format
JSON_ID = "od data"
JSON_DESCRIPTION = "Canfestival object dictionary data"
JSON_INTERNAL_VERSION = "0"
JSON_VERSION = "1"

JSON_SCHEMA = os.path.join(SCRIPT_DIRECTORY, 'schema', 'od.schema.json')


# Output order in JSON file
JSON_TOP_ORDER = (
    "$id", "$version", "$description", "$tool", "$date", "$schema",
    "name", "description", "type", "id", "profile_name", "profile", "ds302",
    "default_string_size", "dictionary",
)
JSON_DICTIONARY_ORDER = (
    "index", "repeat",
    "name", "struct", "group",
    "need", "mandatory", "profile_callback", "callback", "unused",
    "default", "size", "incr", "nbmax",
    "each", "sub",
    # Not in use, but useful to keep in place for development/debugging
    "values", "dictionary", "params",
    "user", "profile", "ds302", "built-in",
)
JSON_SUB_ORDER = (
    "name", "type", "access", "pdo",
    "nbmin", "nbmax",
    "save", "comment",
    "default", "value",
)


# ----------
# Reverse validation (mem -> dict):

# Fields that must be present in the mapping (where the parameter is defined)
# mapping[index] = { ..dict.. }
FIELDS_MAPPING_MUST = {'name', 'struct', 'values'}
FIELDS_MAPPING_OPT = {'need', 'incr', 'nbmax', 'size', 'default'}

# Fields that must be present in the subindex values from mapping,
# mapping[index]['value'] = [ dicts ]
FIELDS_MAPVALS_MUST = {'name', 'type', 'access', 'pdo'}
FIELDS_MAPVALS_OPT = {'nbmin', 'nbmax', 'default'}

# Fields that must be present in parameter dictionary (user settings)
# node.ParamDictionary[index] = { N: { ..dict..}, ..dict.. }
FIELDS_PARAMS = {'comment', 'save', 'buffer_size'}
FIELDS_PARAMS_PROMOTE = {'callback'}

# ---------
# Forward validation (dict -> mem)

# Fields contents of the top-most level, json = { ..dict.. }
FIELDS_DATA_MUST = {'$id', '$version', 'name', 'description', 'type', 'dictionary'}
FIELDS_DATA_OPT = {
    '$description', '$tool', '$date', 'id', 'profile',
    'profile_name', 'ds302', 'default_string_size'
}

# Fields contents of the dictionary, data['dictionary'] = [ ..dicts.. ]
FIELDS_DICT_MUST = {'index', 'name', 'struct', 'sub'}
FIELDS_DICT_OPT = {'group', 'each', 'callback', 'profile_callback', 'unused'} | FIELDS_MAPPING_OPT

# With 'repeat' present, that is, this dict does not contain the parameter definition
# Fields contents of the dictionary, data['dictionary'] = [ ..dicts.. ]
FIELDS_DICT_REPEAT_MUST = {'index', 'repeat', 'struct', 'sub'}
FIELDS_DICT_REPEAT_OPT = {'callback', 'unused'} | FIELDS_MAPPING_OPT

# Fields representing the dictionary value
FIELDS_VALUE = {'value'}

# Valid values of data['dictionary'][index]['group']
GROUPS = {'user', 'profile', 'ds302', 'built-in'}

# Standard values of subindex 0 that can be omitted
SUBINDEX0 = {
    'name': 'Number of Entries',
    'type': 5,
    'access': 'ro',
    'pdo': False,
}


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
    with open(os.path.join(JSON_SCHEMA), 'r') as f:
        SCHEMA = json.loads(remove_jasonc(f.read()))
else:
    SCHEMA = None


def exc_amend(exc, text):
    """ Helper to prefix text to an exception """
    args = list(exc.args)
    if len(args) > 0:
        args[0] = text + str(args[0])
    else:
        args.append(text)
    exc.args = tuple(args)
    return exc


def ordereddict_hook(pairs):
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
    """ Convert string to a number, otherwise pass it through """
    if string is None or isinstance(string, (int, float, long)):
        return string
    s = string.strip()
    if s.startswith('0x') or s.startswith('-0x'):
        return int(s.replace('0x', ''), 16)
    if s.isdigit():
        return int(string)
    return string


def copy_in_order(d, order):
    """ Remake dict d with keys in order """
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
    """ Recursively remove any keys prefixed with '__' """
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


def member_compare(a, must=None, optional=None, not_want=None, msg='', only_if=None):
    ''' Compare the membes of a with set of wants
        must: Raise if a is missing any from must
        optional: Raise if a contains members that is not must or optional
        not_want: Raise error if any is present in a
        only_if: If False, raise error if must is present in a
    '''
    have = set(a)

    if only_if is False:  # is is important here
        not_want = must
        must = None

    # Check mandatory members are present
    if must:
        unexpected = must - have
        if unexpected:
            unexp = "', '".join(unexpected)
            raise ValidationError("Missing required parameters '{}'{}".format(unexp, msg))

    # Check if there are any fields beyond the expected
    if optional:
        unexpected = have - ((must or set()) | optional)
        if unexpected:
            unexp = "', '".join(unexpected)
            raise ValidationError("Unexpected parameters '{}'{}".format(unexp, msg))

    if not_want:
        unexpected = have & not_want
        if unexpected:
            unexp = "', '".join(unexpected)
            raise ValidationError("Unexpected parameters '{}'{}".format(unexp, msg))


def compare_profile(profilename, params, menu=None):
    try:
        dsmap, menumap = nod.ImportProfile(profilename)
        identical = all(
            k in dsmap and k in params and dsmap[k] == params[k]
            for k in set(dsmap) | set(params)
        )
        if menu and not menu == menumap:
            raise ValueError("Menu in OD not identical with profile")
        return True, identical

    except ValueError as exc:
        dbg("Loading profile failed: {}".format(exc))
        # FIXME: Is this an error?
        # Test case test-profile.od -> test-profile.json without access to profile
        warning("WARNING: %s", exc)
        return False, False


def GenerateFile(filepath, node, sort=False, internal=False, validate=True):
    ''' Write a JSON file representation of the node '''

    # Get the dict representation
    jd = node_todict(node, sort=sort, internal=internal, validate=validate)

    # Generate the json string
    text = json.dumps(jd, separators=(',', ': '), indent=2)

    # Convert the special __ fields to jasonc comments
    out = re.sub(
        r'^(\s*)"__(\w+)": "(.*)",$',
        r'\1// \2: \3',
        text,
        flags=re.MULTILINE,
    )

    # Convert the special __ fields to jasonc comments
    def _index_repl(m):
        return m.group(0) + '  // {}'.format(str_to_number(m.group(2)))
    out = re.sub(
        r'"(index)": "(0x[0-9a-fA-F]+)",',
        _index_repl,
        out,
        flags=re.MULTILINE,
    )

    # Writeout the json
    with open(filepath, "w") as f:
        f.write(out)


def GenerateNode(filepath):
    ''' Import a JSON file '''

    # Read the json file
    with open(filepath, "r") as f:
        text = f.read()

    # Remove jsonc annotations
    jsontext = remove_jasonc(text)

    # Load the json, with awareness on ordering in py2
    if sys.version_info[0] < 3:
        jd = json.loads(jsontext, object_pairs_hook=ordereddict_hook)
    else:
        jd = json.loads(jsontext)

    if SCHEMA:
        jsonschema.validate(jd, schema=SCHEMA)

    return node_fromdict(jd)


def node_todict(node, sort=False, rich=True, use_text=True, omit_profile=False,
                omit_ds302=False, internal=False, validate=True, omit_date=False):
    '''
        Convert a node to dict representation for serialization.

        sort: Set if the output dictionary should be sorted before output.
        rich: If true, additional __fields will be added to the output. These
            fields are not needed, but helps the readability of the json.
        use_text: Replace some numerical fields with strings
        omit_profile: Set to true if inclusion of the profile params should be
            omitted
    '''

    # Get the dict representation of the node object
    jd = node.GetDict()

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

    # Insert meta-data
    jd.update({
        '$id': JSON_ID,
        '$version': JSON_INTERNAL_VERSION if internal else JSON_VERSION,
        '$description': JSON_DESCRIPTION,
        '$tool': str(ODG_PROGRAM) + ' ' + str(ODG_VERSION),
    })
    if not omit_date:
        jd['$date'] = datetime.isoformat(datetime.now())

    # Get the order for the indexes
    order = node.GetAllParameters(sort=sort)

    # Parse through all parameters
    dictionary = []
    for index in order:
        obj = None
        try:
            # Get the internal dict representation of the node parameter
            obj = node.GetIndexDict(index)

            # Add in the index (as dictionary is a list)
            obj["index"] = "0x{:04X}".format(index)

            # Don't wrangle further if the internal format is wanted
            if internal:
                continue

            # The internal memory model of Node is complex, this function exists
            # to validate the input data, i.e. the Node object before migrating
            # to JSON format. This is mainly to ensure no wrong assumptions
            # produce unexpected output.
            if validate:
                validate_nodeindex(node, index, obj)

            # Get the parameter for the index
            obj = node_todict_parameter(obj, node, index)

            # Rearrage order of 'sub' and 'each'
            obj["sub"] = [
                copy_in_order(k, JSON_SUB_ORDER)
                for k in obj["sub"]
            ]
            if 'each' in obj:
                obj["each"] = copy_in_order(obj["each"], JSON_SUB_ORDER)

        except Exception as exc:
            exc_amend(exc, "Index 0x{:04x} ({}): ".format(index, index))
            raise

        finally:
            dictionary.append(obj)

    # Rearrange order of Dictionary[*]
    jd["dictionary"] = [
        copy_in_order(k, JSON_DICTIONARY_ORDER) for k in dictionary
    ]

    # Rearrange the order of the top-level dict
    jd = copy_in_order(jd, JSON_TOP_ORDER)

    # Cleanup of unwanted members
    # - NOTE: SpecificMenu is not used in dict representation
    for k in ('Dictionary', 'ParamsDictionary', 'Profile', 'SpecificMenu',
              'DS302', 'UserMapping', 'IndexOrder'):
        jd.pop(k, None)

    # Verification to see if we later can import the generated dict
    if validate and not internal:
        validate_fromdict(jd)

    return jd


def node_todict_parameter(obj, node, index):
    ''' Modify obj from internal dict representation to generic dict structure
        which is suitable for serialization into JSON.
    '''

    # Observations:
    # =============
    # - 'callback' might be set in the mapping. If it is, then the
    #   user cannot change the value from the UI. Otherwise 'callback'
    #   is defined by user in 'params'
    # - In [N]ARRAY formats, the number of elements is determined by the
    #   length of 'dictionary'
    # - 'params' stores by subindex num (integer), except for [N]VAR, where
    #   the data is stored directly in 'params'
    # - 'dictionary' is a list of number of subindexes minus 1 for the
    #   number of subindexes. If [N]VAR the value is immediate.
    # - ARRAY expects mapping 'values[1]' to contain the repeat specification,
    #   RECORD only if 'nbmax' is defined in said values. Attempting to use
    #   named array entries fails.
    # - "nbmax" (on values level) is used for indicating "each" elements
    #   and must be present in index 1.
    # - "incr" an "nbmax" (on mapping level) is used for N* types
    # - "default" on values level is only used for custom types <0x100
    # - NVAR with empty dictionary value is not possible

    # -- STEP 1) --
    # Blend the mapping type (baseobj) with obj

    # Get group membership (what object type it is) and if the prarmeter is repeated
    groups = obj.pop('groups')
    is_repeat = obj.pop('base', index) != index

    # Is the definition for the parameter present?
    if not is_repeat:

        # Extract mapping baseobject that contains the object definitions. Checked in A
        group = groups[0]
        if group != 'user':
            obj['group'] = group

        baseobj = obj.pop(group)
        struct = baseobj["struct"]  # Checked in B

    else:
        obj["repeat"] = True
        info = node.GetEntryInfos(index)
        baseobj = {}
        struct = info['struct']

    # Callback in mapping collides with the user set callback, so it is renamed
    if 'callback' in baseobj:
        obj['profile_callback'] = baseobj.pop('callback')

    # Move members from baseobj to top-level object. Checked in B
    for k in FIELDS_MAPPING_MUST | FIELDS_MAPPING_OPT:
        if k in baseobj:
            obj[k] = baseobj.pop(k)

    # Ensure fields exists
    obj['struct'] = struct
    obj['sub'] = obj.pop('values', [])

    # Move subindex[1] to 'each' on objecs that contain 'nbmax'
    if len(obj['sub']) > 1 and 'nbmax' in obj['sub'][1]:
        obj['each'] = obj['sub'].pop(1)

    # Baseobj should have been emptied
    if baseobj != {}:
        raise ValidationError("Mapping data not empty. Programming error?. Contains: {}".format(baseobj))

    # -- STEP 2) --
    # Migrate 'params' and 'dictionary' to common 'sub'

    # Extract the params
    has_params = 'params' in obj
    has_dictionary = 'dictionary' in obj
    params = obj.pop("params", {})
    dictvals = obj.pop("dictionary", [])

    # These types places the params in the top-level dict
    if has_params and struct in (OD.VAR, OD.NVAR):
        params = params.copy()  # Important, as its mutated here
        param0 = {}
        for k in FIELDS_PARAMS:
            if k in params:
                param0[k] = params.pop(k)
        params[0] = param0

    # Promote the global parameters from params into top-level object
    for k in FIELDS_PARAMS_PROMOTE:
        if k in params:
            obj[k] = params.pop(k)

    # Extract the dictionary values
    # NOTE! It is important to capture that 'dictionary' exists is obj, even if
    #       empty. This might happen on a ARRAY with 0 elements.
    start = 0
    if has_dictionary:
        if struct in (OD.VAR, OD.NVAR):
            dictvals = [dictvals]
        else:
            start = 1  # Have "number of entries" first

        for i, v in enumerate(dictvals, start=start):
            params.setdefault(i, {})['value'] = v
    else:
        # This is now unused profile parameters are stored
        obj['unused'] = True

    # Commit the params to the 'sub' list
    if params:
        # Ensure there are enough items in 'sub' to hold the param items
        dictlen = start + len(dictvals)
        sub = obj["sub"]
        if dictlen > len(sub):
            sub += [dict() for i in range(len(sub), dictlen)]

        # Commit the params to 'sub'
        for i, val in enumerate(sub):
            val.update(params.pop(i, {}))

    # Params should have been emptied
    if params != {}:
        raise ValidationError("User parameters not empty. Programming error? Contains: {}".format(params))

    return obj


def validate_nodeindex(node, index, obj):
    """ Validate index dict contents (see Node.GetIndexDict). The purpose is to
        validate the assumptions in the data format.

        NOTE: Do not implement two parallel validators. This function exists
        to validate the data going into node_todict() in case the programmed
        assumptions are wrong. For general data validation, see
        validate_fromdict()
    """

    groups = obj['groups']
    is_repeat = obj.get('base', index) != index

    # Is the definition for the parameter present?
    if not is_repeat:

        # A) Ensure only one definition of the object group
        if len(groups) == 0:
            raise ValidationError("Missing mapping")
        if len(groups) != 1:
            raise ValidationError("Contains uexpected number of definitions for the object")

        # Extract the definition
        group = groups[0]
        baseobj = obj[group]

        # B) Check baseobj object members is present
        member_compare(baseobj.keys(),
            FIELDS_MAPPING_MUST, FIELDS_MAPPING_OPT | FIELDS_PARAMS_PROMOTE,
            msg=' in mapping object'
        )

        struct = baseobj['struct']

    else:
        # If this is a repeated paramter, this object should not contain any definitions

        # A) Ensure no definition of the object group
        if len(groups) != 0:
            raise ValidationError("Unexpected to find any groups ({}) in repeated object".format(", ".join(groups)))

        info = node.GetEntryInfos(index)
        baseobj = {}
        struct = info["struct"]  # Implicit

    # Helpers
    is_var = struct in (OD.VAR, OD.NVAR)

    # Ensure obj does NOT contain any fields found in baseobj (sanity check really)
    member_compare(obj.keys(),
        not_want=FIELDS_MAPPING_MUST | FIELDS_MAPPING_OPT | FIELDS_PARAMS_PROMOTE,
        msg=' in object'
    )

    # Check baseobj object members
    for val in baseobj.get('values', []):
        member_compare(val.keys(),
            FIELDS_MAPVALS_MUST, FIELDS_MAPVALS_OPT,
            msg=' in mapping values'
        )

    # Collect some information
    params = obj.get('params', {})
    dictvalues = obj.get('dictionary', [])
    dictlen = 0

    # These types places the params in the top-level dict
    if params and is_var:
        params = params.copy()  # Important, as its mutated here
        param0 = {}
        for k in FIELDS_PARAMS:
            if k in params:
                param0[k] = params.pop(k)
        params[0] = param0

    # Verify type of dictionary
    if 'dictionary' in obj:
        if is_var:
            dictlen = 1
            # dictvalues = [dictvalues]
        else:
            if not isinstance(dictvalues, list):
                raise ValidationError("Unexpected type in dictionary '{}'".format(dictvalues))
            dictlen = len(dictvalues) + 1
            # dictvalues = [None] + dictvalues  # Which is a copy

    # Check numbered params
    excessive = {}
    for param in params:
        # All int keys corresponds to a numbered index
        if isinstance(param, int):
            # Check that there are no unexpected fields in numbered param
            member_compare(params[param].keys(),
                {},
                FIELDS_PARAMS,
                not_want=FIELDS_PARAMS_PROMOTE | FIELDS_MAPVALS_MUST | FIELDS_MAPVALS_OPT,
                msg=' in params'
            )

            if param > dictlen:
                excessive[param] = params[param]

    # Do we have too many params?
    if excessive:
        raise ValidationError("Excessive params, or too few dictionary values: {}".format(excessive))

    # Find all non-numbered params and check them against
    promote = {k for k in params if not isinstance(k, int)}
    if promote:
        member_compare(promote, optional=FIELDS_PARAMS_PROMOTE, msg=' in params')

    # Check that we got the number of values and nbmax we expect for the type
    nbmax = ['nbmax' in v for v in baseobj.get('values', [])]
    lenok, nbmaxok = False, False

    if not baseobj:
        # Bypass tests if no baseobj is present
        lenok, nbmaxok = True, True

    elif struct in (OD.VAR, OD.NVAR):
        if len(nbmax) == 1:
            lenok = True
        if sum(nbmax) == 0:
            nbmaxok = True

    elif struct in (OD.ARRAY, OD.NARRAY):
        if len(nbmax) == 2:
            lenok = True
        if sum(nbmax) == 1 and nbmax[1]:
            nbmaxok = True

    elif struct in (OD.RECORD, OD.NRECORD):
        if sum(nbmax) and len(nbmax) > 1 and nbmax[1]:
            nbmaxok = True
            if len(nbmax) == 2:
                lenok = True
        elif sum(nbmax) == 0:
            nbmaxok = True
            if len(nbmax) > 1:
                lenok = True
    else:
        raise ValidationError("Unknown struct '{}'".format(struct))

    if not nbmaxok:
        raise ValidationError("Unexpected 'nbmax' use in mapping values, used {} times".format(sum(nbmax)))
    if not lenok:
        raise ValidationError("Unexpexted count of subindexes in mapping object, found {}".format(len(nbmax)))


def node_fromdict(jd, internal=False):
    ''' Convert a dict jd into a Node '''

    # Remove all underscore keys from the file
    jd = remove_underscore(jd)

    # Validate the input json against the schema
    validate_fromdict(jd)

    # Create default values for optional components
    jd.setdefault("id", 0)
    jd.setdefault("profile", False)
    jd.setdefault("ds302", False)
    jd.setdefault("profile_name", "None")

    # Create the node and fill the most basic data
    node = Node(name=jd["name"], type=jd["type"], id=jd["id"],
                description=jd["description"], profilename=jd["profile_name"])

    # Restore optional values
    if 'default_string_size' in jd:
        node.DefaultStringSize = jd["default_string_size"]

    # An import of a internal JSON file?
    internal = internal or jd['$version'] == JSON_INTERNAL_VERSION

    # Iterate over dictionary
    dictionary = []
    for obj in jd.get("dictionary", []):
        try:
            index = str_to_number(obj['index'])
            obj["index"] = index

            # Don't unwrangle further if the internal format is wanted
            if internal:
                continue

            # Mutate obj containing the generic dict to the internal node format
            obj = node_fromdict_parameter(obj)

        except Exception as exc:
            exc_amend(exc, "Index 0x{:04x} ({}): ".format(index, index))
            raise

        finally:
            dictionary.append(obj)

    # Reiterate over the items to convert them to Node object
    for obj in dictionary:
        index = obj["index"]

        # Copy the object to node object entries
        if 'dictionary' in obj:
            node.Dictionary[index] = obj['dictionary']
        if 'params' in obj:
            node.ParamsDictionary[index] = {str_to_number(k): v for k, v in obj['params'].items()}
        if 'profile' in obj:
            node.Profile[index] = obj['profile']
        if 'ds302' in obj:
            node.DS302[index] = obj['ds302']
        if 'user' in obj:
            node.UserMapping[index] = obj['user']

        # Verify against built-in data (don't verify repeated params)
        if 'built-in' in obj and not obj.get('repeat', False):
            baseobj = maps.MAPPING_DICTIONARY.get(index)

            diff = deepdiff.DeepDiff(obj['built-in'], baseobj, view='tree')
            if diff:
                if sys.version_info[0] >= 3:
                    print(diff.pretty())
                else:
                    print("WARNING: Py2 cannot print difference of objects")
                raise ValidationError("Built-in parameter index 0x{:04x} ({}) does not match against system parameters".format(index, index))

    # There is a weakness to the Node implementation: There is no store
    # of the order of the incoming parameters, instead the data is spread over
    # many dicts, e.g. Profile, DS302, UserMapping, Dictionary, ParamsDictionary
    # Node.IndexOrder has been added to store this information.
    node.IndexOrder = [obj["index"] for obj in jd.get('dictionary', [])]

    # DEBUG
    # out = json.dumps(jd, separators=(',', ': '), indent=2)
    # with open('_tmp_mk4.debug.json', "w") as f:
    #     f.write(out)

    return node


def node_fromdict_parameter(obj):

    # -- STEP 1a) --
    # Move 'definition' into individual mapping type category

    baseobj = {}

    # Get struct
    struct = obj["struct"]
    if not isinstance(struct, int):
        struct = OD.from_string(struct)

    # Set the baseobj in the right category
    group = obj.pop("group", None) or 'user'

    if 'profile_callback' in obj:
        baseobj['callback'] = obj.pop('profile_callback')

    # Restore the definition entries
    for k in FIELDS_MAPPING_MUST | FIELDS_MAPPING_OPT:
        if k in obj:
            baseobj[k] = obj.pop(k)

    # -- STEP 2) --
    # Migrate 'sub' into 'params' and 'dictionary'

    # Restore the param entries
    params = {}
    for k in FIELDS_PARAMS_PROMOTE:
        if k in obj:
            params[k] = obj.pop(k)

    # Restore the values and dictionary
    subitems = obj.pop('sub')

    # Recreate the dictionary list
    dictionary = [
        v.pop('value') for v in subitems
        if v and 'value' in v
    ]

    # Restore the dictionary values
    if dictionary:
        # [N]VAR needs them as immediate values
        if struct in (OD.VAR, OD.NVAR):
            dictionary = dictionary[0]
        obj['dictionary'] = dictionary

    # Unless 'unused' is True, then an empty dict must be reinstated to signal
    # that the parameter is in used, but empty.
    elif not obj.get('unused', False):
        # NOTE: If struct in VAR and NVAR, it is not correct to set to [], but
        #       the should be captured by the validator.
        obj['dictionary'] = []

    # Restore param dictionary
    for i, vals in enumerate(subitems):
        pars = params.setdefault(i, {})
        for k in FIELDS_PARAMS:
            if k in vals:
                pars[k] = vals.pop(k)

    # Move entries from item 0 into the params object
    if 0 in params and struct in (OD.VAR, OD.NVAR):
        params.update(params.pop(0))

    # Remove the empty params and values
    params = {k: v for k, v in params.items() if v}
    subitems = [v for v in subitems if v]

    # Commit params if there is any data
    if params:
        obj['params'] = params

    # -- STEP 1b) --

    # Move back the each object
    if 'each' in obj:
        subitems.append(obj.pop('each'))

    # Restore values
    if subitems:
        baseobj['values'] = subitems
        obj[group] = baseobj

    # Restore optional items from subindex 0
    if not obj.get('repeat', False) and struct in (OD.ARRAY, OD.NARRAY, OD.RECORD, OD.NRECORD):
        index0 = baseobj['values'][0]
        for k, v in SUBINDEX0.items():
            index0.setdefault(k, v)

    return obj


def validate_fromdict(jsonobj):
    ''' Validate that jsonobj is a properly formatted dictionary that may
        be imported to the internal OD-format
    '''

    jd = jsonobj

    if not jd or not isinstance(jd, dict):
        raise ValidationError("Not data or not dict")
    if jd.get('$id') != JSON_ID:
        raise ValidationError("Unknown file format, expected '$id' to be '{}', found '{}'".format(
            JSON_ID, jd.get('$id')))
    if jd.get('$version') not in (JSON_INTERNAL_VERSION, JSON_VERSION):
        raise ValidationError("Unknown file version, expected '$version' to be '{}', found '{}'".format(
            JSON_VERSION, jd.get('$version')))

    # Don't validate the internal format any further
    if jd['$version'] == JSON_INTERNAL_VERSION:
        return


    def _validate_sub(obj, idx=0, is_var=False, is_repeat=False, is_each=False):
        if not isinstance(obj, dict):
            raise ValidationError("Is not a dict")

        if idx > 0 and is_var:
            raise ValidationError("Expects only one subitem on VAR/NVAR")

        # Subindex 0 of a *ARRAY, *RECORD cannot hold any value
        if idx == 0 and not is_var:
            member_compare(obj.keys(), not_want=FIELDS_VALUE)

        # Validate "nbmax" if parsing the "each" sub
        member_compare(obj.keys(), {'nbmax'}, only_if=idx == -1)

        # Default parameter precense
        defs = 'must'   # Parameter definition (FIELDS_MAPVALS_*)
        params = 'opt'  # User parameters (FIELDS_PARAMS)
        value = 'no'    # User value (FIELDS_VALUE)

        # Set what parameters should be present, optional or not present
        if idx == -1:  # Checking "each" section. Never parameter or value
            params = 'no'

        elif is_repeat:  # Object is defined elsewhere. No definition needed.
            defs = 'no'
            if is_var or idx > 0:
                value = 'must'

        elif is_var:  # VAR types, assumed idx==0 here
            value = 'opt'

        elif is_each:  # Param use "each" should never have defs in idx > 0
            if idx > 0:
                defs = 'no'
                value = 'must'

        else:  # Params without 'each' and not VAR.
            if idx > 0:
                value = 'opt'

        # Calculate the expected parameters
        must = set()
        opts = set()
        if defs == 'must':
            must |= FIELDS_MAPVALS_MUST
            opts |= FIELDS_MAPVALS_OPT
        if defs == 'opt':
            opts |= FIELDS_MAPVALS_MUST | FIELDS_MAPVALS_OPT
        if params == 'must':
            must |= FIELDS_PARAMS
        if params == 'opt':
            opts |= FIELDS_PARAMS
        if value == 'must':
            must |= FIELDS_VALUE
        if value == 'opt':
            opts |= FIELDS_VALUE

        # Verify parameters
        member_compare(obj.keys(), must, opts)

        # Validate "name"
        if 'name' in obj and not obj['name']:
            raise ValidationError("Must have a non-zero length name")


    def _validate_dictionary(obj):

        is_repeat = obj.get('repeat', False)

        # Validate all present fields
        if is_repeat:
            member_compare(obj.keys(), FIELDS_DICT_REPEAT_MUST, FIELDS_DICT_REPEAT_OPT,
                           msg=' in dictionary')

        else:
            member_compare(obj.keys(), FIELDS_DICT_MUST, FIELDS_DICT_OPT,
                           msg=' in dictionary')

        # Validate "index"
        if not isinstance(index, int):
            raise ValidationError("Invalid dictionary index '{}'".format(obj['index']))
        if index <= 0 or index > 0xFFFF:
            raise ValidationError("Invalid dictionary index value '{}'".format(index))

        # Validate "struct"
        struct = obj["struct"]
        if not isinstance(struct, int):
            struct = OD.from_string(struct)
        if struct not in OD.STRINGS:
            raise ValidationError("Unknown struct value '{}'".format(obj['struct']))

        # Validate "group"
        group = obj.get("group", None) or 'user'
        if group and group not in GROUPS:
            raise ValidationError("Unknown group value '{}'".format(group))

        # Validate "sub"
        subitems = obj['sub']
        has_name = ['name' in v for v in subitems]
        has_value = ['value' in v for v in subitems]

        if not isinstance(subitems, list):
            raise ValidationError("'sub' is not a list")
        for idx, val in enumerate(subitems):
            try:
                is_var = struct in (OD.VAR, OD.NVAR)
                _validate_sub(val, idx, is_var=is_var, is_repeat=is_repeat, is_each='each' in obj)
            except Exception as exc:
                exc_amend(exc, "sub[{}]: ".format(idx))
                raise

        # Validate "each"
        if 'each' in obj:
            try:
                _validate_sub(obj['each'], idx=-1)
            except Exception as exc:
                exc_amend(exc, "'each': ")
                raise

            # Having 'each' requires only one sub item
            if not (sum(has_name) == 1 and has_name[0]):
                raise ValidationError("Unexpected subitems. Subitem 0 must contain name")

            # Ensure the format is correct
            # NOTE: Not all seems to be the same. E.g. default is 'access'='ro',
            # however in 0x1600, 'access'='rw'.
            # if not all(subitems[0].get(k, v) == v for k, v in SUBINDEX0.items()):
            #     raise ValidationError("Incorrect definition in subindex 0. Found {}, expects {}".format(subitems[0], SUBINDEX0))

        # Validate "default"
        if 'default' in obj and index >= 0x1000:
            raise ValidationError("'default' cannot be used in index 0x1000 and above")

        # Validate "default"
        if 'size' in obj and index >= 0x1000:
            raise ValidationError("'size' cannot be used in index 0x1000 and above")

        # Validate that "nbmax" and "incr" is only present in right struct type
        need_nbmax = not is_repeat and struct in (OD.NVAR, OD.NARRAY, OD.NRECORD)
        member_compare(obj.keys(), {'nbmax', 'incr'}, only_if=need_nbmax)

        # Validate "unused"
        if 'unused' in obj:
            if obj['unused'] and sum(has_value):
                raise ValidationError("There is {} values in subitems, but 'unused' is true".format(sum(has_value)))
            if not obj['unused'] and not sum(has_value):
                raise ValidationError("There is no values in subitems, but 'unused' is false")

        # Validate that we got the number of subs we expect for the type
        if struct in (OD.VAR, OD.NVAR):
            if 'each' in obj:
                raise ValidationError("Unexpected 'each' found in VAR/NVAR object")
            if not is_repeat and sum(has_name) != 1:
                raise ValidationError("Must have definition in subitem 0")
            if is_repeat and sum(has_value) == 0:
                raise ValidationError("Must have value in subitem 0")

        elif struct in (OD.ARRAY, OD.NARRAY, OD.RECORD, OD.NRECORD):
            if not is_repeat and len(subitems) < 1:
                raise ValidationError("Expects at least two subindexes")
            if sum(has_value) and has_value[0]:
                raise ValidationError("Subitem 0 should not contain any value")
            if sum(has_value) and sum(has_value) != len(has_value) - 1:
                raise ValidationError("All subitems except item 0 must contain values")

        if struct in (OD.ARRAY, OD.NARRAY):
            if not is_repeat and 'each' not in obj:
                raise ValidationError("Field 'each' missing from ARRAY/NARRAY object")
            # Covered by 'each' validation

        elif struct in (OD.RECORD, OD.NRECORD):
            if not is_repeat and 'each' not in obj:
                if sum(has_name) != len(has_name):
                    raise ValidationError("Not all subitems have name, {} of {}".format(sum(has_name), len(has_name)))

    # Verify that we have the expected members
    member_compare(jsonobj.keys(), FIELDS_DATA_MUST, FIELDS_DATA_OPT)

    if not isinstance(jd['dictionary'], list):
        raise ValidationError("No dictionary or dictionary not list")

    for num, obj in enumerate(jd['dictionary']):
        if not isinstance(obj, dict):
            raise ValidationError("Item number {} of 'dictionary' is not a dict".format(num))

        sindex = obj.get('index', 'item {}'.format(num))
        index = str_to_number(sindex)

        try:
            _validate_dictionary(obj)
        except Exception as exc:
            exc_amend(exc, "Index 0x{:04x} ({}): ".format(index, index))
            raise


def diff_nodes(node1, node2, as_dict=True, validate=True):

    diffs = {}

    if as_dict:
        j1 = node_todict(node1, sort=True, validate=validate, omit_date=True)
        j2 = node_todict(node2, sort=True, validate=validate, omit_date=True)

        diff = deepdiff.DeepDiff(j1, j2, exclude_paths=[
            "root['dictionary']"
        ], view='tree')

        for chtype, changes in diff.items():
            for change in changes:
                path = change.path()
                entries = diffs.setdefault('', [])
                entries.append((chtype, change, path.replace('root', '')))

        diff = deepdiff.DeepDiff(j1['dictionary'], j2['dictionary'], view='tree', group_by='index')

        res = re.compile(r"root\[('0x[0-9a-fA-F]+'|\d+)\]")

        for chtype, changes in diff.items():
            for change in changes:
                path = change.path()
                m = res.search(path)
                if m:
                    num = str_to_number(m.group(1).strip("'"))
                    entries = diffs.setdefault(num, [])
                    entries.append((chtype, change, path.replace(m.group(0), '')))
                else:
                    entries = diffs.setdefault('', [])
                    entries.append((chtype, change, path.replace('root', '')))

    else:
        diff = deepdiff.DeepDiff(node1, node2, exclude_paths=[
            "root.IndexOrder"
        ], view='tree')

        res = re.compile(r"root\.(Profile|Dictionary|ParamsDictionary|UserMapping|DS302)\[(\d+)\]")

        for chtype, changes in diff.items():
            for change in changes:
                path = change.path()
                m = res.search(path)
                if m:
                    entries = diffs.setdefault(int(m.group(2)), [])
                    entries.append((chtype, change, path.replace(m.group(0), m.group(1))))
                else:
                    entries = diffs.setdefault('', [])
                    entries.append((chtype, change, path.replace('root.', '')))

    return diffs
