# -*- coding: utf-8 -*-
#
# This file is part of CanFestival, a library implementing CanOpen Stack.
#
# Copyright (C): Edouard TISSERANT, Francis DUPIN and Laurent BESSARD
#
# See COPYING file for copyrights details.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from __future__ import print_function
from builtins import chr
from builtins import object
from builtins import range

import os
import sys
import re
import copy
from collections import OrderedDict
from past.builtins import execfile
from future.utils import raise_from
import pprint

from .nosis import pickle as nosis
from . import PROFILE_DIRECTORIES
from . import dbg, warning

if sys.version_info[0] >= 3:
    unicode = str  # pylint: disable=invalid-name
    ODict = dict
else:
    ODict = OrderedDict


#
# Dictionary of translation between access symbol and their signification
#
ACCESS_TYPE = {"ro": "Read Only", "wo": "Write Only", "rw": "Read/Write"}
BOOL_TYPE = {True: "True", False: "False"}
OPTION_TYPE = {True: "Yes", False: "No"}
CUSTOMISABLE_TYPES = [
    (0x02, 0), (0x03, 0), (0x04, 0), (0x05, 0), (0x06, 0), (0x07, 0), (0x08, 0),
    (0x09, 1), (0x0A, 1), (0x0B, 1), (0x10, 0), (0x11, 0), (0x12, 0), (0x13, 0),
    (0x14, 0), (0x15, 0), (0x16, 0), (0x18, 0), (0x19, 0), (0x1A, 0), (0x1B, 0),
]
DEFAULT_PARAMS = {"comment": None, "save": False, "buffer_size": None}

# ------------------------------------------------------------------------------
#                      Dictionary Mapping and Organisation
# ------------------------------------------------------------------------------

class ODStructTypes:
    #
    # Properties of entry structure in the Object Dictionary
    #
    Subindex = 1             # Entry has at least one subindex
    MultipleSubindexes = 2   # Entry has more than one subindex
    IdenticalSubindexes = 4  # Subindexes of entry have the same description
    IdenticalIndexes = 8     # Entry has the same description on multiple indexes

    #
    # Structures of entry in the Object Dictionary, sum of the properties described above
    # for all sorts of entries use in CAN Open specification
    #
    NOSUB = 0  # Entry without subindex (only for type declaration)
    VAR = Subindex  # 1
    RECORD = Subindex | MultipleSubindexes  # 3
    ARRAY = Subindex | MultipleSubindexes | IdenticalSubindexes  # 7
    # Entries identical on multiple indexes
    NVAR = Subindex | IdenticalIndexes  # 9
    NRECORD = Subindex | MultipleSubindexes | IdenticalIndexes  # 11, Example : PDO Parameters
    NARRAY = Subindex | MultipleSubindexes | IdenticalSubindexes | IdenticalIndexes  # 15, Example : PDO Mapping

    #
    # Mapping against name and structure number
    #
    STRINGS = {
        NOSUB: None,
        VAR: "var",
        RECORD: "record",
        ARRAY: "array",
        NVAR: "nvar",
        NRECORD: "nrecord",
        NARRAY: "narray",
    }

    @classmethod
    def to_string(cls, val, default=None):
        return cls.STRINGS.get(val, default)

    @classmethod
    def from_string(cls, val, default=None):
        try:
            return next(k for k, v in cls.STRINGS.items() if v == val)
        except StopIteration:
            return default


# Convenience shortcut
OD = ODStructTypes

#
# List of the Object Dictionary ranges
#
INDEX_RANGES = [
    {"min": 0x0001, "max": 0x0FFF, "name": "dtd", "description": "Data Type Definitions"},
    {"min": 0x1000, "max": 0x1029, "name": "cp", "description": "Communication Parameters"},
    {"min": 0x1200, "max": 0x12FF, "name": "sdop", "description": "SDO Parameters"},
    {"min": 0x1400, "max": 0x15FF, "name": "rpdop", "description": "Receive PDO Parameters"},
    {"min": 0x1600, "max": 0x17FF, "name": "rpdom", "description": "Receive PDO Mapping"},
    {"min": 0x1800, "max": 0x19FF, "name": "tpdop", "description": "Transmit PDO Parameters"},
    {"min": 0x1A00, "max": 0x1BFF, "name": "tpdom", "description": "Transmit PDO Mapping"},
    {"min": 0x1C00, "max": 0x1FFF, "name": "ocp", "description": "Other Communication Parameters"},
    {"min": 0x2000, "max": 0x5FFF, "name": "ms", "description": "Manufacturer Specific"},
    {"min": 0x6000, "max": 0x9FFF, "name": "sdp", "description": "Standardized Device Profile"},
    {"min": 0xA000, "max": 0xBFFF, "name": "sip", "description": "Standardized Interface Profile"},
]

#
# MAPPING_DICTIONARY is the structure used for writing a good organised Object
# Dictionary. It follows the specifications of the CANOpen standard.
# Change the informations within it if there is a mistake. But don't modify the
# organisation of this object, it will involve in a malfunction of the application.
#
MAPPING_DICTIONARY = {
    # -- Static Data Types
    0x0001: {"name": "BOOLEAN", "struct": OD.NOSUB, "size": 1, "default": False, "values": []},
    0x0002: {"name": "INTEGER8", "struct": OD.NOSUB, "size": 8, "default": 0, "values": []},
    0x0003: {"name": "INTEGER16", "struct": OD.NOSUB, "size": 16, "default": 0, "values": []},
    0x0004: {"name": "INTEGER32", "struct": OD.NOSUB, "size": 32, "default": 0, "values": []},
    0x0005: {"name": "UNSIGNED8", "struct": OD.NOSUB, "size": 8, "default": 0, "values": []},
    0x0006: {"name": "UNSIGNED16", "struct": OD.NOSUB, "size": 16, "default": 0, "values": []},
    0x0007: {"name": "UNSIGNED32", "struct": OD.NOSUB, "size": 32, "default": 0, "values": []},
    0x0008: {"name": "REAL32", "struct": OD.NOSUB, "size": 32, "default": 0.0, "values": []},
    0x0009: {"name": "VISIBLE_STRING", "struct": OD.NOSUB, "size": 8, "default": "", "values": []},
    0x000A: {"name": "OCTET_STRING", "struct": OD.NOSUB, "size": 8, "default": "", "values": []},
    0x000B: {"name": "UNICODE_STRING", "struct": OD.NOSUB, "size": 16, "default": "", "values": []},
    # 0x000C: {"name": "TIME_OF_DAY", "struct": OD.NOSUB, "size": 48, "default": 0, "values": []},
    # 0x000D: {"name": "TIME_DIFFERENCE", "struct": OD.NOSUB, "size": 48, "default": 0, "values": []},
    # 0x000E: RESERVED
    0x000F: {"name": "DOMAIN", "struct": OD.NOSUB, "size": 0, "default": "", "values": []},
    0x0010: {"name": "INTEGER24", "struct": OD.NOSUB, "size": 24, "default": 0, "values": []},
    0x0011: {"name": "REAL64", "struct": OD.NOSUB, "size": 64, "default": 0.0, "values": []},
    0x0012: {"name": "INTEGER40", "struct": OD.NOSUB, "size": 40, "default": 0, "values": []},
    0x0013: {"name": "INTEGER48", "struct": OD.NOSUB, "size": 48, "default": 0, "values": []},
    0x0014: {"name": "INTEGER56", "struct": OD.NOSUB, "size": 56, "default": 0, "values": []},
    0x0015: {"name": "INTEGER64", "struct": OD.NOSUB, "size": 64, "default": 0, "values": []},
    0x0016: {"name": "UNSIGNED24", "struct": OD.NOSUB, "size": 24, "default": 0, "values": []},
    # 0x0017: RESERVED
    0x0018: {"name": "UNSIGNED40", "struct": OD.NOSUB, "size": 40, "default": 0, "values": []},
    0x0019: {"name": "UNSIGNED48", "struct": OD.NOSUB, "size": 48, "default": 0, "values": []},
    0x001A: {"name": "UNSIGNED56", "struct": OD.NOSUB, "size": 56, "default": 0, "values": []},
    0x001B: {"name": "UNSIGNED64", "struct": OD.NOSUB, "size": 64, "default": 0, "values": []},
    # 0x001C-0x001F: RESERVED

    # -- Communication Profile Area
    0x1000: {"name": "Device Type", "struct": OD.VAR, "need": True, "values":
             [{"name": "Device Type", "type": 0x07, "access": 'ro', "pdo": False}]},
    0x1001: {"name": "Error Register", "struct": OD.VAR, "need": True, "values":
             [{"name": "Error Register", "type": 0x05, "access": 'ro', "pdo": True}]},
    0x1002: {"name": "Manufacturer Status Register", "struct": OD.VAR, "need": False, "values":
             [{"name": "Manufacturer Status Register", "type": 0x07, "access": 'ro', "pdo": True}]},
    0x1003: {"name": "Pre-defined Error Field", "struct": OD.ARRAY, "need": False, "callback": True, "values":
             [{"name": "Number of Errors", "type": 0x05, "access": 'rw', "pdo": False},
              {"name": "Standard Error Field", "type": 0x07, "access": 'ro', "pdo": False, "nbmin": 1, "nbmax": 0xFE}]},
    0x1005: {"name": "SYNC COB ID", "struct": OD.VAR, "need": False, "callback": True, "values":
             [{"name": "SYNC COB ID", "type": 0x07, "access": 'rw', "pdo": False}]},
    0x1006: {"name": "Communication / Cycle Period", "struct": OD.VAR, "need": False, "callback": True, "values":
             [{"name": "Communication Cycle Period", "type": 0x07, "access": 'rw', "pdo": False}]},
    0x1007: {"name": "Synchronous Window Length", "struct": OD.VAR, "need": False, "values":
             [{"name": "Synchronous Window Length", "type": 0x07, "access": 'rw', "pdo": False}]},
    0x1008: {"name": "Manufacturer Device Name", "struct": OD.VAR, "need": False, "values":
             [{"name": "Manufacturer Device Name", "type": 0x09, "access": 'ro', "pdo": False}]},
    0x1009: {"name": "Manufacturer Hardware Version", "struct": OD.VAR, "need": False, "values":
             [{"name": "Manufacturer Hardware Version", "type": 0x09, "access": 'ro', "pdo": False}]},
    0x100A: {"name": "Manufacturer Software Version", "struct": OD.VAR, "need": False, "values":
             [{"name": "Manufacturer Software Version", "type": 0x09, "access": 'ro', "pdo": False}]},
    0x100C: {"name": "Guard Time", "struct": OD.VAR, "need": False, "values":
             [{"name": "Guard Time", "type": 0x06, "access": 'rw', "pdo": False}]},
    0x100D: {"name": "Life Time Factor", "struct": OD.VAR, "need": False, "values":
             [{"name": "Life Time Factor", "type": 0x05, "access": 'rw', "pdo": False}]},
    0x1010: {"name": "Store parameters", "struct": OD.RECORD, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Save All Parameters", "type": 0x07, "access": 'rw', "pdo": False},
              {"name": "Save Communication Parameters", "type": 0x07, "access": 'rw', "pdo": False},
              {"name": "Save Application Parameters", "type": 0x07, "access": 'rw', "pdo": False},
              {"name": "Save Manufacturer Parameters %d[(sub - 3)]", "type": 0x07, "access": 'rw', "pdo": False, "nbmax": 0x7C}]},
    0x1011: {"name": "Restore Default Parameters", "struct": OD.RECORD, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Restore All Default Parameters", "type": 0x07, "access": 'rw', "pdo": False},
              {"name": "Restore Communication Default Parameters", "type": 0x07, "access": 'rw', "pdo": False},
              {"name": "Restore Application Default Parameters", "type": 0x07, "access": 'rw', "pdo": False},
              {"name": "Restore Manufacturer Defined Default Parameters %d[(sub - 3)]", "type": 0x07, "access": 'rw', "pdo": False, "nbmax": 0x7C}]},
    0x1012: {"name": "TIME COB ID", "struct": OD.VAR, "need": False, "values":
             [{"name": "TIME COB ID", "type": 0x07, "access": 'rw', "pdo": False}]},
    0x1013: {"name": "High Resolution Timestamp", "struct": OD.VAR, "need": False, "values":
             [{"name": "High Resolution Time Stamp", "type": 0x07, "access": 'rw', "pdo": True}]},
    0x1014: {"name": "Emergency COB ID", "struct": OD.VAR, "need": False, "values":
             [{"name": "Emergency COB ID", "type": 0x07, "access": 'rw', "pdo": False, "default": '"$NODEID+0x80"'}]},
    0x1015: {"name": "Inhibit Time Emergency", "struct": OD.VAR, "need": False, "values":
             [{"name": "Inhibit Time Emergency", "type": 0x06, "access": 'rw', "pdo": False}]},
    0x1016: {"name": "Consumer Heartbeat Time", "struct": OD.ARRAY, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Consumer Heartbeat Time", "type": 0x07, "access": 'rw', "pdo": False, "nbmin": 1, "nbmax": 0x7F}]},
    0x1017: {"name": "Producer Heartbeat Time", "struct": OD.VAR, "need": False, "callback": True, "values":
             [{"name": "Producer Heartbeat Time", "type": 0x06, "access": 'rw', "pdo": False}]},
    0x1018: {"name": "Identity", "struct": OD.RECORD, "need": True, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Vendor ID", "type": 0x07, "access": 'ro', "pdo": False},
              {"name": "Product Code", "type": 0x07, "access": 'ro', "pdo": False},
              {"name": "Revision Number", "type": 0x07, "access": 'ro', "pdo": False},
              {"name": "Serial Number", "type": 0x07, "access": 'ro', "pdo": False}]},
    0x1019: {"name": "Synchronous counter overflow value", "struct": OD.VAR, "need": False, "values":
             [{"name": "Synchronous counter overflow value", "type": 0x05, "access": 'rw', "pdo": False}]},
    0x1020: {"name": "Verify Configuration", "struct": OD.RECORD, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Configuration Date", "type": 0x07, "access": 'rw', "pdo": False},
              {"name": "Configuration Time", "type": 0x07, "access": 'rw', "pdo": False}]},
    # 0x1021: {"name": "Store EDS", "struct": OD.VAR, "need": False, "values":
    #          [{"name": "Store EDS", "type": 0x0F, "access": 'rw', "pdo": False}]},
    # 0x1022: {"name": "Storage Format", "struct": OD.VAR, "need": False, "values":
    #          [{"name": "Storage Format", "type": 0x06, "access": 'rw', "pdo": False}]},
    0x1023: {"name": "OS Command", "struct": OD.RECORD, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Command", "type": 0x0A, "access": 'rw', "pdo": False},
              {"name": "Status", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Reply", "type": 0x0A, "access": 'ro', "pdo": False}]},
    0x1024: {"name": "OS Command Mode", "struct": OD.VAR, "need": False, "values":
             [{"name": "OS Command Mode", "type": 0x05, "access": 'wo', "pdo": False}]},
    0x1025: {"name": "OS Debugger Interface", "struct": OD.RECORD, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Command", "type": 0x0A, "access": 'rw', "pdo": False},
              {"name": "Status", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Reply", "type": 0x0A, "access": 'ro', "pdo": False}]},
    0x1026: {"name": "OS Prompt", "struct": OD.RECORD, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "StdIn", "type": 0x05, "access": 'wo', "pdo": True},
              {"name": "StdOut", "type": 0x05, "access": 'ro', "pdo": True},
              {"name": "StdErr", "type": 0x05, "access": 'ro', "pdo": True}]},
    0x1027: {"name": "Module List", "struct": OD.ARRAY, "need": False, "values":
             [{"name": "Number of Connected Modules", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Module %d[(sub)]", "type": 0x06, "access": 'ro', "pdo": False, "nbmin": 1, "nbmax": 0xFE}]},
    0x1028: {"name": "Emergency Consumer", "struct": OD.ARRAY, "need": False, "values":
             [{"name": "Number of Consumed Emergency Objects", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Emergency Consumer", "type": 0x07, "access": 'rw', "pdo": False, "nbmin": 1, "nbmax": 0x7F}]},
    0x1029: {"name": "Error Behavior", "struct": OD.RECORD, "need": False, "values":
             [{"name": "Number of Error Classes", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "Communication Error", "type": 0x05, "access": 'rw', "pdo": False},
              {"name": "Device Profile", "type": 0x05, "access": 'rw', "pdo": False, "nbmax": 0xFE}]},

    # -- Server SDO Parameters
    0x1200: {"name": "Server SDO Parameter", "struct": OD.RECORD, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "COB ID Client to Server (Receive SDO)", "type": 0x07, "access": 'ro', "pdo": False, "default": '"$NODEID+0x600"'},
              {"name": "COB ID Server to Client (Transmit SDO)", "type": 0x07, "access": 'ro', "pdo": False, "default": '"$NODEID+0x580"'}]},
    0x1201: {"name": "Additional Server SDO %d Parameter[(idx)]", "struct": OD.NRECORD, "incr": 1, "nbmax": 0x7F, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "COB ID Client to Server (Receive SDO)", "type": 0x07, "access": 'ro', "pdo": False},
              {"name": "COB ID Server to Client (Transmit SDO)", "type": 0x07, "access": 'ro', "pdo": False},
              {"name": "Node ID of the SDO Client", "type": 0x05, "access": 'ro', "pdo": False}]},

    # -- Client SDO Parameters
    0x1280: {"name": "Client SDO %d Parameter[(idx)]", "struct": OD.NRECORD, "incr": 1, "nbmax": 0x100, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "COB ID Client to Server (Transmit SDO)", "type": 0x07, "access": 'rw', "pdo": False},
              {"name": "COB ID Server to Client (Receive SDO)", "type": 0x07, "access": 'rw', "pdo": False},
              {"name": "Node ID of the SDO Server", "type": 0x05, "access": 'rw', "pdo": False}]},

    # -- Receive PDO Communication Parameters
    0x1400: {"name": "Receive PDO %d Parameter[(idx)]", "struct": OD.NRECORD, "incr": 1, "nbmax": 0x200, "need": False, "values":
             [{"name": "Highest SubIndex Supported", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "COB ID used by PDO", "type": 0x07, "access": 'rw', "pdo": False, "default": "{True:\"$NODEID+0x%X00\"%(base+2),False:0x80000000}[base<4]"},
              {"name": "Transmission Type", "type": 0x05, "access": 'rw', "pdo": False},
              {"name": "Inhibit Time", "type": 0x06, "access": 'rw', "pdo": False},
              {"name": "Compatibility Entry", "type": 0x05, "access": 'rw', "pdo": False},
              {"name": "Event Timer", "type": 0x06, "access": 'rw', "pdo": False},
              {"name": "SYNC start value", "type": 0x05, "access": 'rw', "pdo": False}]},

    # -- Receive PDO Mapping Parameters
    0x1600: {"name": "Receive PDO %d Mapping[(idx)]", "struct": OD.NARRAY, "incr": 1, "nbmax": 0x200, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'rw', "pdo": False},
              {"name": "PDO %d Mapping for an application object %d[(idx,sub)]", "type": 0x07, "access": 'rw', "pdo": False, "nbmin": 0, "nbmax": 0x40}]},

    # -- Transmit PDO Communication Parameters
    0x1800: {"name": "Transmit PDO %d Parameter[(idx)]", "struct": OD.NRECORD, "incr": 1, "nbmax": 0x200, "need": False, "callback": True, "values":
             [{"name": "Highest SubIndex Supported", "type": 0x05, "access": 'ro', "pdo": False},
              {"name": "COB ID used by PDO", "type": 0x07, "access": 'rw', "pdo": False, "default": "{True:\"$NODEID+0x%X80\"%(base+1),False:0x80000000}[base<4]"},
              {"name": "Transmission Type", "type": 0x05, "access": 'rw', "pdo": False},
              {"name": "Inhibit Time", "type": 0x06, "access": 'rw', "pdo": False},
              {"name": "Compatibility Entry", "type": 0x05, "access": 'rw', "pdo": False},
              {"name": "Event Timer", "type": 0x06, "access": 'rw', "pdo": False},
              {"name": "SYNC start value", "type": 0x05, "access": 'rw', "pdo": False}]},

    # -- Transmit PDO Mapping Parameters
    0x1A00: {"name": "Transmit PDO %d Mapping[(idx)]", "struct": OD.NARRAY, "incr": 1, "nbmax": 0x200, "need": False, "values":
             [{"name": "Number of Entries", "type": 0x05, "access": 'rw', "pdo": False},
              {"name": "PDO %d Mapping for a process data variable %d[(idx,sub)]", "type": 0x07, "access": 'rw', "pdo": False, "nbmin": 0, "nbmax": 0x40}]},
}


# ------------------------------------------------------------------------------
#                         Utils
# ------------------------------------------------------------------------------
def GetIndexRange(index):
    for irange in INDEX_RANGES:
        if irange["min"] <= index <= irange["max"]:
            return irange
    raise ValueError("Cannot find index range for value '0x%x'" % index)


# ------------------------------------------------------------------------------
#                         Load mapping
# ------------------------------------------------------------------------------
def ImportProfile(profilename):
    # Import profile

    # Test if the profilename is a filepath which can be used directly. If not
    # treat it as the name
    # The UI use full filenames, while all other uses use profile names
    profilepath = profilename
    if not os.path.exists(profilepath):
        fname = "%s.prf" % profilename
        try:
            profilepath = next(
                os.path.join(base, fname)
                for base in PROFILE_DIRECTORIES
                if os.path.exists(os.path.join(base, fname))
            )
        except StopIteration:
            raise_from(ValueError("Unable to load profile '%s': '%s': No such file or directory" % (profilename, fname)), None)

    # Mapping and AddMenuEntries are expected to be defined by the execfile
    # The profiles requires some vars to be set
    # pylint: disable=unused-variable
    try:
        dbg("EXECFILE %s" % (profilepath,))
        execfile(profilepath)  # FIXME: Using execfile is unsafe
        # pylint: disable=undefined-variable
        return Mapping, AddMenuEntries  # noqa: F821
    except Exception as exc:  # pylint: disable=broad-except
        dbg("EXECFILE FAILED: %s" % exc)
        raise_from(ValueError("Loading profile '%s' failed: %s" % (profilepath, exc)), exc)
        return None  # To satisfy linter only


# ------------------------------------------------------------------------------
#                         Search in a Mapping Dictionary
# ------------------------------------------------------------------------------

def FindTypeIndex(typename, mappingdictionary):
    """
    Return the index of the typename given by searching in mappingdictionary
    """
    testdic = {}
    for index, values in mappingdictionary.items():
        if index < 0x1000:
            testdic[values["name"]] = index
    return testdic.get(typename)


def FindTypeName(typeindex, mappingdictionary):
    """
    Return the name of the type by searching in mappingdictionary
    """
    if typeindex < 0x1000 and typeindex in mappingdictionary:
        return mappingdictionary[typeindex]["name"]
    return None


def FindTypeDefaultValue(typeindex, mappingdictionary):
    """
    Return the default value of the type by searching in mappingdictionary
    """
    if typeindex < 0x1000 and typeindex in mappingdictionary:
        return mappingdictionary[typeindex]["default"]
    return None


def FindTypeList(mappingdictionary):
    """
    Return the list of types defined in mappingdictionary
    """
    return [
        mappingdictionary[index]["name"]
        for index in mappingdictionary
        if index < 0x1000
    ]


def FindEntryName(index, mappingdictionary, compute=True):
    """
    Return the name of an entry by searching in mappingdictionary
    """
    base_index = FindIndex(index, mappingdictionary)
    if base_index:
        infos = mappingdictionary[base_index]
        if infos["struct"] & OD.IdenticalIndexes and compute:
            return StringFormat(infos["name"], (index - base_index) // infos["incr"] + 1, 0)
        return infos["name"]
    return None


def FindEntryInfos(index, mappingdictionary, compute=True):
    """
    Return the informations of one entry by searching in mappingdictionary
    """
    base_index = FindIndex(index, mappingdictionary)
    if base_index:
        obj = mappingdictionary[base_index].copy()
        if obj["struct"] & OD.IdenticalIndexes and compute:
            obj["name"] = StringFormat(obj["name"], (index - base_index) // obj["incr"] + 1, 0)
        obj.pop("values")
        return obj
    return None


def FindSubentryInfos(index, subindex, mappingdictionary, compute=True):
    """
    Return the informations of one subentry of an entry by searching in mappingdictionary
    """
    base_index = FindIndex(index, mappingdictionary)
    if base_index:
        struct = mappingdictionary[base_index]["struct"]
        if struct & OD.IdenticalIndexes:
            incr = mappingdictionary[base_index]["incr"]
        else:
            incr = 1
        if struct & OD.Subindex:
            infos = None
            if struct & OD.IdenticalSubindexes:
                if subindex == 0:
                    infos = mappingdictionary[base_index]["values"][0].copy()
                elif 0 < subindex <= mappingdictionary[base_index]["values"][1]["nbmax"]:
                    infos = mappingdictionary[base_index]["values"][1].copy()
            elif struct & OD.MultipleSubindexes:
                idx = 0
                for subindex_infos in mappingdictionary[base_index]["values"]:
                    if "nbmax" in subindex_infos:
                        if idx <= subindex < idx + subindex_infos["nbmax"]:
                            infos = subindex_infos.copy()
                            break
                        idx += subindex_infos["nbmax"]
                    else:
                        if subindex == idx:
                            infos = subindex_infos.copy()
                            break
                        idx += 1
            elif subindex == 0:
                infos = mappingdictionary[base_index]["values"][0].copy()
            if infos is not None and compute:
                infos["name"] = StringFormat(infos["name"], (index - base_index) // incr + 1, subindex)
            return infos
    return None


def FindMapVariableList(mappingdictionary, node, compute=True):
    """
    Return the list of variables that can be mapped defined in mappingdictionary
    """
    list_ = []
    for index in mappingdictionary:
        if node.IsEntry(index):
            for subindex, values in enumerate(mappingdictionary[index]["values"]):
                if mappingdictionary[index]["values"][subindex]["pdo"]:
                    infos = node.GetEntryInfos(mappingdictionary[index]["values"][subindex]["type"])
                    name = mappingdictionary[index]["values"][subindex]["name"]
                    if mappingdictionary[index]["struct"] & OD.IdenticalSubindexes:
                        values = node.GetEntry(index)
                        for i in range(len(values) - 1):
                            computed_name = name
                            if compute:
                                computed_name = StringFormat(computed_name, 1, i + 1)
                            list_.append((index, i + 1, infos["size"], computed_name))
                    else:
                        computed_name = name
                        if compute:
                            computed_name = StringFormat(computed_name, 1, subindex)
                        list_.append((index, subindex, infos["size"], computed_name))
    return list_


def FindMandatoryIndexes(mappingdictionary):
    """
    Return the list of mandatory indexes defined in mappingdictionary
    """
    return [
        index
        for index in mappingdictionary
        if index >= 0x1000 and mappingdictionary[index]["need"]
    ]


def FindIndex(index, mappingdictionary):
    """
    Return the index of the informations in the Object Dictionary in case of identical
    indexes
    """
    if index in mappingdictionary:
        return index
    listpluri = [
        idx for idx, mapping in mappingdictionary.items()
        if mapping["struct"] & OD.IdenticalIndexes
    ]
    for idx in sorted(listpluri):
        nb_max = mappingdictionary[idx]["nbmax"]
        incr = mappingdictionary[idx]["incr"]
        if idx < index < idx + incr * nb_max and (index - idx) % incr == 0:
            return idx
    return None


# ------------------------------------------------------------------------------
#                           Formating Name of an Entry
# ------------------------------------------------------------------------------

RE_NAME = re.compile(r'(.*)\[(.*)\]')


def StringFormat(text, idx, sub):  # pylint: disable=unused-argument
    """
    Format the text given with the index and subindex defined
    """
    result = RE_NAME.match(text)
    if result:
        fmt = result.groups()
        try:
            # dbg("EVAL StringFormat(): '%s'" % (fmt[1],))
            return fmt[0] % eval(fmt[1])  # FIXME: Using eval is not safe
        except Exception as exc:
            dbg("EVAL FAILED: %s" % (exc, ))
            raise
    else:
        return text


# ------------------------------------------------------------------------------
#                          Definition of Node Object
# ------------------------------------------------------------------------------

class Node(object):
    """
    Class recording the Object Dictionary entries. It checks at each modification
    that the structure of the Object Dictionary stay coherent
    """

    DefaultStringSize = 10

    def __init__(self, name="", type="slave", id=0, description="", profilename="DS-301", profile=None, specificmenu=None):  # pylint: disable=redefined-builtin, invalid-name
        self.Name = name
        self.Type = type
        self.ID = id
        self.Description = description
        self.ProfileName = profilename
        self.Profile = profile or ODict()
        self.SpecificMenu = specificmenu or []
        self.Dictionary = ODict()
        self.ParamsDictionary = ODict()
        self.DS302 = ODict()
        self.UserMapping = ODict()

    def GetMappings(self, userdefinedtoo=True):
        """
        Function which return the different Mappings available for this node
        """
        if userdefinedtoo:
            return [self.Profile, self.DS302, self.UserMapping]
        return [self.Profile, self.DS302]

    def AddEntry(self, index, subindex=None, value=None):
        """
        Add a new entry in the Object Dictionary
        """
        if index not in self.Dictionary:
            if not subindex:
                self.Dictionary[index] = value
                return True
            if subindex == 1:
                self.Dictionary[index] = [value]
                return True
        elif subindex > 0 and isinstance(self.Dictionary[index], list) and subindex == len(self.Dictionary[index]) + 1:
            self.Dictionary[index].append(value)
            return True
        return False

    def SetEntry(self, index, subindex=None, value=None):
        """
        Warning ! Modifies an existing entry in the Object Dictionary. Can't add a new one.
        """
        if index not in self.Dictionary:
            return False
        if not subindex:
            if value is not None:
                self.Dictionary[index] = value
            return True
        if isinstance(self.Dictionary[index], list) and 0 < subindex <= len(self.Dictionary[index]):
            if value is not None:
                self.Dictionary[index][subindex - 1] = value
            return True
        return False

    def SetParamsEntry(self, index, subindex=None, comment=None, buffer_size=None, save=None, callback=None):
        if index not in self.Dictionary:
            return False
        if (comment is not None or save is not None or callback is not None or buffer_size is not None) and index not in self.ParamsDictionary:
            self.ParamsDictionary[index] = {}
        if subindex is None or not isinstance(self.Dictionary[index], list) and subindex == 0:
            if comment is not None:
                self.ParamsDictionary[index]["comment"] = comment
            if buffer_size is not None:
                self.ParamsDictionary[index]["buffer_size"] = buffer_size
            if save is not None:
                self.ParamsDictionary[index]["save"] = save
            if callback is not None:
                self.ParamsDictionary[index]["callback"] = callback
            return True
        if isinstance(self.Dictionary[index], list) and 0 <= subindex <= len(self.Dictionary[index]):
            if (comment is not None or save is not None or callback is not None or buffer_size is not None) and subindex not in self.ParamsDictionary[index]:
                self.ParamsDictionary[index][subindex] = {}
            if comment is not None:
                self.ParamsDictionary[index][subindex]["comment"] = comment
            if buffer_size is not None:
                self.ParamsDictionary[index][subindex]["buffer_size"] = buffer_size
            if save is not None:
                self.ParamsDictionary[index][subindex]["save"] = save
            return True
        return False

    def RemoveEntry(self, index, subindex=None):
        """
        Removes an existing entry in the Object Dictionary. If a subindex is specified
        it will remove this subindex only if it's the last of the index. If no subindex
        is specified it removes the whole index and subIndexes from the Object Dictionary.
        """
        if index not in self.Dictionary:
            return False
        if not subindex:
            self.Dictionary.pop(index)
            if index in self.ParamsDictionary:
                self.ParamsDictionary.pop(index)
            return True
        if isinstance(self.Dictionary[index], list) and subindex == len(self.Dictionary[index]):
            self.Dictionary[index].pop(subindex - 1)
            if index in self.ParamsDictionary:
                if subindex in self.ParamsDictionary[index]:
                    self.ParamsDictionary[index].pop(subindex)
                if len(self.ParamsDictionary[index]) == 0:
                    self.ParamsDictionary.pop(index)
            if len(self.Dictionary[index]) == 0:
                self.Dictionary.pop(index)
                if index in self.ParamsDictionary:
                    self.ParamsDictionary.pop(index)
            return True
        return False

    def IsEntry(self, index, subindex=None):
        """
        Check if an entry exists in the Object Dictionary and returns the answer.
        """
        if index in self.Dictionary:
            if not subindex:
                return True
            return subindex <= len(self.Dictionary[index])
        return False

    def GetEntry(self, index, subindex=None, compute=True, aslist=False):
        """
        Returns the value of the entry asked. If the entry has the value "count", it
        returns the number of subindex in the entry except the first.
        """
        if index not in self.Dictionary:
            raise KeyError("Index 0x%04x does not exist" % index)
        if subindex is None:
            if isinstance(self.Dictionary[index], list):
                return [len(self.Dictionary[index])] + [
                    self.CompileValue(value, index, compute)
                    for value in self.Dictionary[index]
                ]
            if aslist:
                return [self.CompileValue(self.Dictionary[index], index, compute)]
            return self.CompileValue(self.Dictionary[index], index, compute)
        if subindex == 0:
            if isinstance(self.Dictionary[index], list):
                return len(self.Dictionary[index])
            return self.CompileValue(self.Dictionary[index], index, compute)
        if isinstance(self.Dictionary[index], list) and 0 < subindex <= len(self.Dictionary[index]):
            return self.CompileValue(self.Dictionary[index][subindex - 1], index, compute)
        raise ValueError("Invalid subindex %s for index 0x%04x" % (subindex, index))

    def GetParamsEntry(self, index, subindex=None, aslist=False):
        """
        Returns the value of the entry asked. If the entry has the value "count", it
        returns the number of subindex in the entry except the first.
        """
        if index not in self.Dictionary:
            raise KeyError("Index 0x%04x does not exist" % index)
        if subindex is None:
            if isinstance(self.Dictionary[index], list):
                if index in self.ParamsDictionary:
                    result = []
                    for i in range(len(self.Dictionary[index]) + 1):
                        line = DEFAULT_PARAMS.copy()
                        if i in self.ParamsDictionary[index]:
                            line.update(self.ParamsDictionary[index][i])
                        result.append(line)
                    return result
                return [DEFAULT_PARAMS.copy() for i in range(len(self.Dictionary[index]) + 1)]
            result = DEFAULT_PARAMS.copy()
            if index in self.ParamsDictionary:
                result.update(self.ParamsDictionary[index])
            if aslist:
                return [result]
            return result
        if subindex == 0 and not isinstance(self.Dictionary[index], list):
            result = DEFAULT_PARAMS.copy()
            if index in self.ParamsDictionary:
                result.update(self.ParamsDictionary[index])
            return result
        if isinstance(self.Dictionary[index], list) and 0 <= subindex <= len(self.Dictionary[index]):
            result = DEFAULT_PARAMS.copy()
            if index in self.ParamsDictionary and subindex in self.ParamsDictionary[index]:
                result.update(self.ParamsDictionary[index][subindex])
            return result
        raise ValueError("Invalid subindex %s for index 0x%04x" % (subindex, index))

    def HasEntryCallbacks(self, index):
        entry_infos = self.GetEntryInfos(index)
        if entry_infos and "callback" in entry_infos:
            return entry_infos["callback"]
        if index in self.Dictionary and index in self.ParamsDictionary and "callback" in self.ParamsDictionary[index]:
            return self.ParamsDictionary[index]["callback"]
        return False

    def IsMappingEntry(self, index):
        """
        Check if an entry exists in the User Mapping Dictionary and returns the answer.
        """
        return index in self.UserMapping

    def AddMappingEntry(self, index, subindex=None, name="Undefined", struct=0, size=None, nbmax=None, default=None, values=None):
        """
        Add a new entry in the User Mapping Dictionary
        """
        if index not in self.UserMapping:
            if values is None:
                values = []
            if subindex is None:
                self.UserMapping[index] = {"name": name, "struct": struct, "need": False, "values": values}
                if size is not None:
                    self.UserMapping[index]["size"] = size
                if nbmax is not None:
                    self.UserMapping[index]["nbmax"] = nbmax
                if default is not None:
                    self.UserMapping[index]["default"] = default
                return True
        elif subindex is not None and subindex == len(self.UserMapping[index]["values"]):
            if values is None:
                values = {}
            self.UserMapping[index]["values"].append(values)
            return True
        return False

    def SetMappingEntry(self, index, subindex=None, name=None, struct=None, size=None, nbmax=None, default=None, values=None):
        """
        Warning ! Modifies an existing entry in the User Mapping Dictionary. Can't add a new one.
        """
        if index not in self.UserMapping:
            return False
        if subindex is None:
            if name is not None:
                self.UserMapping[index]["name"] = name
                if self.UserMapping[index]["struct"] & OD.IdenticalSubindexes:
                    self.UserMapping[index]["values"][1]["name"] = name + " %d[(sub)]"
                elif not self.UserMapping[index]["struct"] & OD.MultipleSubindexes:
                    self.UserMapping[index]["values"][0]["name"] = name
            if struct is not None:
                self.UserMapping[index]["struct"] = struct
            if size is not None:
                self.UserMapping[index]["size"] = size
            if nbmax is not None:
                self.UserMapping[index]["nbmax"] = nbmax
            if default is not None:
                self.UserMapping[index]["default"] = default
            if values is not None:
                self.UserMapping[index]["values"] = values
            return True
        if 0 <= subindex < len(self.UserMapping[index]["values"]) and values is not None:
            if "type" in values:
                if self.UserMapping[index]["struct"] & OD.IdenticalSubindexes:
                    if self.IsStringType(self.UserMapping[index]["values"][subindex]["type"]):
                        if self.IsRealType(values["type"]):
                            for i in range(len(self.Dictionary[index])):
                                self.SetEntry(index, i + 1, 0.)
                        elif not self.IsStringType(values["type"]):
                            for i in range(len(self.Dictionary[index])):
                                self.SetEntry(index, i + 1, 0)
                    elif self.IsRealType(self.UserMapping[index]["values"][subindex]["type"]):
                        if self.IsStringType(values["type"]):
                            for i in range(len(self.Dictionary[index])):
                                self.SetEntry(index, i + 1, "")
                        elif not self.IsRealType(values["type"]):
                            for i in range(len(self.Dictionary[index])):
                                self.SetEntry(index, i + 1, 0)
                    elif self.IsStringType(values["type"]):
                        for i in range(len(self.Dictionary[index])):
                            self.SetEntry(index, i + 1, "")
                    elif self.IsRealType(values["type"]):
                        for i in range(len(self.Dictionary[index])):
                            self.SetEntry(index, i + 1, 0.)
                else:
                    if self.IsStringType(self.UserMapping[index]["values"][subindex]["type"]):
                        if self.IsRealType(values["type"]):
                            self.SetEntry(index, subindex, 0.)
                        elif not self.IsStringType(values["type"]):
                            self.SetEntry(index, subindex, 0)
                    elif self.IsRealType(self.UserMapping[index]["values"][subindex]["type"]):
                        if self.IsStringType(values["type"]):
                            self.SetEntry(index, subindex, "")
                        elif not self.IsRealType(values["type"]):
                            self.SetEntry(index, subindex, 0)
                    elif self.IsStringType(values["type"]):
                        self.SetEntry(index, subindex, "")
                    elif self.IsRealType(values["type"]):
                        self.SetEntry(index, subindex, 0.)
            self.UserMapping[index]["values"][subindex].update(values)
            return True
        return False

    def RemoveMappingEntry(self, index, subindex=None):
        """
        Removes an existing entry in the User Mapping Dictionary. If a subindex is specified
        it will remove this subindex only if it's the last of the index. If no subindex
        is specified it removes the whole index and subIndexes from the User Mapping Dictionary.
        """
        if index in self.UserMapping:
            if subindex is None:
                self.UserMapping.pop(index)
                return True
            if subindex == len(self.UserMapping[index]["values"]) - 1:
                self.UserMapping[index]["values"].pop(subindex)
                return True
        return False

    def RemoveMapVariable(self, index, subindex=None):
        model = index << 16
        mask = 0xFFFF << 16
        if subindex:
            model += subindex << 8
            mask += 0xFF << 8
        for i in self.Dictionary:  # pylint: disable=consider-using-dict-items
            if 0x1600 <= i <= 0x17FF or 0x1A00 <= i <= 0x1BFF:
                for j, value in enumerate(self.Dictionary[i]):
                    if (value & mask) == model:
                        self.Dictionary[i][j] = 0

    def UpdateMapVariable(self, index, subindex, size):
        model = index << 16
        mask = 0xFFFF << 16
        if subindex:
            model += subindex << 8
            mask = 0xFF << 8
        for i in self.Dictionary:  # pylint: disable=consider-using-dict-items
            if 0x1600 <= i <= 0x17FF or 0x1A00 <= i <= 0x1BFF:
                for j, value in enumerate(self.Dictionary[i]):
                    if (value & mask) == model:
                        self.Dictionary[i][j] = model + size

    def RemoveLine(self, index, max_, incr=1):
        i = index
        while i < max_ and self.IsEntry(i + incr):
            self.Dictionary[i] = self.Dictionary[i + incr]
            i += incr
        self.Dictionary.pop(i)

    def RemoveUserType(self, index):
        type_ = self.GetEntry(index, 1)
        for i in self.UserMapping:  # pylint: disable=consider-using-dict-items
            for value in self.UserMapping[i]["values"]:
                if value["type"] == index:
                    value["type"] = type_
        self.RemoveMappingEntry(index)
        self.RemoveEntry(index)

    def Copy(self):
        """
        Return a copy of the node
        """
        return copy.deepcopy(self)

    def GetDict(self):
        return copy.deepcopy(self.__dict__)

    def GetIndexes(self):
        """
        Return a sorted list of indexes in Object Dictionary
        """
        return list(sorted(self.Dictionary))

    def Print(self):
        """
        Print the Dictionary values
        """
        print(self.PrintString())

    def PrintString(self):
        result = ""
        for index in sorted(self.Dictionary):
            name = self.GetEntryName(index)
            values = self.Dictionary[index]
            if isinstance(values, list):
                result += "%04X (%s):\n" % (index, name)
                for subidx, value in enumerate(values):
                    subentry_infos = self.GetSubentryInfos(index, subidx + 1)
                    if index == 0x1F22 and value:
                        nb_params = BE_to_LE(value[:4])
                        data = value[4:]
                        value = "%d arg defined" % nb_params
                        i = 0
                        count = 1
                        while i < len(data):
                            value += "\n%04X %02X, arg %d: " % (index, subidx + 1, count)
                            value += "%04X" % BE_to_LE(data[i:i + 2])
                            value += " %02X" % BE_to_LE(data[i + 2:i + 3])
                            size = BE_to_LE(data[i + 3:i + 7])
                            value += " %08X" % size
                            value += (" %0" + "%d" % (size * 2) + "X") % BE_to_LE(data[i + 7:i + 7 + size])
                            i += 7 + size
                            count += 1
                    elif isinstance(value, int):
                        value = "%X" % value
                    result += "%04X %02X (%s): %s\n" % (index, subidx + 1, subentry_infos["name"], value)
            else:
                if isinstance(values, int):
                    values = "%X" % values
                result += "%04X (%s): %s\n" % (index, name, values)
        return result

    def CompileValue(self, value, index, compute=True):
        if isinstance(value, (str, unicode)) and '$NODEID' in value.upper():
            # NOTE: Don't change base, as the eval() use this
            base = self.GetBaseIndexNumber(index)  # noqa: F841  pylint: disable=unused-variable
            try:
                # dbg("EVAL CompileValue(): '%s'" % (value,))
                raw = eval(value)  # FIXME: Using eval is not safe
                if compute and isinstance(raw, (str, unicode)):
                    raw = raw.upper().replace("$NODEID", "self.ID")
                    # dbg("EVAL CompileValue() #2: '%s'" % (raw,))
                    return eval(raw)  # FIXME: Using eval is not safe
                return raw
            except Exception as exc:  # pylint: disable=broad-except
                dbg("EVAL FAILED: %s" % exc)
                raise_from(ValueError("CompileValue failed for '%s'" % (value,)), exc)
                return 0  # FIXME: Why ignore this exception?
        else:
            return value

# ------------------------------------------------------------------------------
#                         Node Informations Functions
# ------------------------------------------------------------------------------

    def GetBaseIndex(self, index):
        """ Return the index number of the base object """
        for mapping in self.GetMappings():
            result = FindIndex(index, mapping)
            if result:
                return result
        return FindIndex(index, MAPPING_DICTIONARY)

    def GetBaseIndexNumber(self, index):
        """ Return the index number from the base object """
        for mapping in self.GetMappings():
            result = FindIndex(index, mapping)
            if result is not None:
                return (index - result) // mapping[result].get("incr", 1)
        result = FindIndex(index, MAPPING_DICTIONARY)
        if result is not None:
            return (index - result) // MAPPING_DICTIONARY[result].get("incr", 1)
        return 0

    def GetCustomisedTypeValues(self, index):
        values = self.GetEntry(index)
        customisabletypes = self.GetCustomisableTypes()
        return values, customisabletypes[values[1]][1]

    def GetEntryName(self, index, compute=True):
        result = None
        mappings = self.GetMappings()
        i = 0
        while not result and i < len(mappings):
            result = FindEntryName(index, mappings[i], compute)
            i += 1
        if result is None:
            result = FindEntryName(index, MAPPING_DICTIONARY, compute)
        return result

    def GetEntryInfos(self, index, compute=True):
        result = None
        mappings = self.GetMappings()
        i = 0
        while not result and i < len(mappings):
            result = FindEntryInfos(index, mappings[i], compute)
            i += 1
        r301 = FindEntryInfos(index, MAPPING_DICTIONARY, compute)
        if r301:
            if result is not None:
                r301.update(result)
            return r301
        return result

    def GetSubentryInfos(self, index, subindex, compute=True):
        result = None
        mappings = self.GetMappings()
        i = 0
        while not result and i < len(mappings):
            result = FindSubentryInfos(index, subindex, mappings[i], compute)
            if result:
                result["user_defined"] = i == len(mappings) - 1 and index >= 0x1000
            i += 1
        r301 = FindSubentryInfos(index, subindex, MAPPING_DICTIONARY, compute)
        if r301:
            if result is not None:
                r301.update(result)
            else:
                r301["user_defined"] = False
            return r301
        return result

    def GetTypeIndex(self, typename):
        result = None
        mappings = self.GetMappings()
        i = 0
        while not result and i < len(mappings):
            result = FindTypeIndex(typename, mappings[i])
            i += 1
        if result is None:
            result = FindTypeIndex(typename, MAPPING_DICTIONARY)
        return result

    def GetTypeName(self, typeindex):
        result = None
        mappings = self.GetMappings()
        i = 0
        while not result and i < len(mappings):
            result = FindTypeName(typeindex, mappings[i])
            i += 1
        if result is None:
            result = FindTypeName(typeindex, MAPPING_DICTIONARY)
        return result

    def GetTypeDefaultValue(self, typeindex):
        result = None
        mappings = self.GetMappings()
        i = 0
        while not result and i < len(mappings):
            result = FindTypeDefaultValue(typeindex, mappings[i])
            i += 1
        if result is None:
            result = FindTypeDefaultValue(typeindex, MAPPING_DICTIONARY)
        return result

    def GetMapVariableList(self, compute=True):
        list_ = FindMapVariableList(MAPPING_DICTIONARY, self, compute)
        for mapping in self.GetMappings():
            list_.extend(FindMapVariableList(mapping, self, compute))
        list_.sort()
        return list_

    def GetMandatoryIndexes(self, node=None):  # pylint: disable=unused-argument
        list_ = FindMandatoryIndexes(MAPPING_DICTIONARY)
        for mapping in self.GetMappings():
            list_.extend(FindMandatoryIndexes(mapping))
        return list_

    def GetCustomisableTypes(self):
        dic = {}
        for index, valuetype in CUSTOMISABLE_TYPES:
            name = self.GetTypeName(index)
            dic[index] = [name, valuetype]
        return dic

# ------------------------------------------------------------------------------
#                            Type helper functions
# ------------------------------------------------------------------------------

    def IsStringType(self, index):
        if index in (0x9, 0xA, 0xB, 0xF):
            return True
        if 0xA0 <= index < 0x100:
            result = self.GetEntry(index, 1)
            if result in (0x9, 0xA, 0xB):
                return True
        return False

    def IsRealType(self, index):
        if index in (0x8, 0x11):
            return True
        if 0xA0 <= index < 0x100:
            result = self.GetEntry(index, 1)
            if result in (0x8, 0x11):
                return True
        return False

# ------------------------------------------------------------------------------
#                            Type and Map Variable Lists
# ------------------------------------------------------------------------------

    def GetTypeList(self):
        list_ = FindTypeList(MAPPING_DICTIONARY)
        for mapping in self.GetMappings():
            list_.extend(FindTypeList(mapping))
        return ",".join(sorted(list_))

    def GenerateMapName(self, name, index, subindex):  # pylint: disable=unused-argument
        return "%s (0x%4.4X)" % (name, index)

    def GetMapValue(self, mapname):
        if mapname == "None":
            return 0

        list_ = self.GetMapVariableList()
        for index, subindex, size, name in list_:
            if mapname == self.GenerateMapName(name, index, subindex):
                if self.UserMapping[index]["struct"] == OD.ARRAY:  # array type, only look at subindex 1 in UserMapping
                    if self.IsStringType(self.UserMapping[index]["values"][1]["type"]):
                        try:
                            if int(self.ParamsDictionary[index][subindex]["buffer_size"]) <= 8:
                                return (index << 16) + (subindex << 8) + size * int(self.ParamsDictionary[index][subindex]["buffer_size"])
                            raise ValueError("String size too big to fit in a PDO")
                        except KeyError:
                            raise_from(ValueError("No string length found and default string size too big to fit in a PDO"), None)
                else:
                    if self.IsStringType(self.UserMapping[index]["values"][subindex]["type"]):
                        try:
                            if int(self.ParamsDictionary[index][subindex]["buffer_size"]) <= 8:
                                return (index << 16) + (subindex << 8) + size * int(self.ParamsDictionary[index][subindex]["buffer_size"])
                            raise ValueError("String size too big to fit in a PDO")
                        except KeyError:
                            raise_from(ValueError("No string length found and default string size too big to fit in a PDO"), None)
                return (index << 16) + (subindex << 8) + size
        return None

    def GetMapIndex(self, value):
        if value:
            index = value >> 16
            subindex = (value >> 8) % (1 << 8)
            size = (value) % (1 << 8)
            return index, subindex, size
        return 0, 0, 0

    def GetMapName(self, value):
        index, subindex, _ = self.GetMapIndex(value)
        if value:
            result = self.GetSubentryInfos(index, subindex)
            if result:
                return self.GenerateMapName(result["name"], index, subindex)
        return "None"

    def GetMapList(self):
        """
        Return the list of variables that can be mapped for the current node
        """
        list_ = ["None"] + [self.GenerateMapName(name, index, subindex) for index, subindex, size, name in self.GetMapVariableList()]
        return ",".join(list_)

    def GetAllParameters(self):

        dictionary = set(self.UserMapping.keys())
        dictionary.update(self.Dictionary.keys())
        dictionary.update(self.ParamsDictionary.keys())
        if self.Profile:
            dictionary.update(self.Profile.keys())
        if self.DS302:
            dictionary.update(self.DS302.keys())
        return dictionary


# ------------------------------------------------------------------------------
#                            Comparison and checks
# ------------------------------------------------------------------------------

    def Compare(self, other):

        changes = []
        for attr in (
            "Name", "Type", "ID", "Description", "ProfileName", "SpecificMenu",
            "DefaultStringSize"
        ):
            if getattr(self, attr) != getattr(other, attr):
                changes.append("%s differ. '%s' in LEFT, '%s' in RIGHT" %(attr, getattr(self, attr), getattr(other, attr)))

        def compare(a, b, changes, name):
            for k in set(a.keys()) | set(b.keys()):
                if k not in a:
                    changes.append("%s for 0x%04X not in LEFT" % (name, k))
                if k not in b:
                    changes.append("%s for 0x%04X not in RIGHT" % (name, k))
                if k in a and k in b and a[k] != b[k]:
                    pa = ["        " + t for t in pprint.pformat(a[k]).splitlines()]
                    pb = ["        " + t for t in pprint.pformat(b[k]).splitlines()]
                    changes.append("""%s for 0x%04X differ
    In LEFT:
%s

    In RIGHT:
%s
""" % (name, k, "\n".join(pa), "\n".join(pb)))

        compare(self.Dictionary, other.Dictionary, changes, 'Value')
        compare(self.DS302, other.DS302, changes, 'DS302 entry')
        compare(self.Profile, other.Profile, changes, 'Profile entry')
        compare(self.ParamsDictionary, other.ParamsDictionary, changes, 'Parameter')
        compare(self.UserMapping, other.UserMapping, changes, 'User mapping')

        return changes


    def Validate(self, correct=False):

        params = set(sorted(self.Dictionary.keys()))
        params.update(self.ParamsDictionary.keys())

        for k in sorted(params):

            name = self.GetEntryName(k)
            if k not in self.Dictionary:
                warning("WARNING: 0x%04x (%d) '%s': Parameter without any value" % (k, k, name))
                if correct:
                    del self.ParamsDictionary[k]
                continue

            values = self.GetEntry(k, aslist=True)
            entries = self.GetParamsEntry(k, aslist=True)

            for i, (value, entry) in enumerate(zip(values, entries)):
                info = self.GetSubentryInfos(k, i)
                info.update(entry)

                if not info['name']:
                    warning("WARNING: 0x%04x (%d) '%s': Sub-parameter %02d has no name" % (k, k, name, i))
                    if correct:
                        self.UserMapping[k]['values'][i]['name'] = 'Subindex %02x' %(i, )


def diff_dict(name, a, b):
    diff = []
    for k in set(a.keys()) | set(b.keys()):
        kn = "%s['%s']" %(name, k)
        if k not in a:
            diff.append(('only_right', kn, b[k]))
        elif k not in b:
            diff.append(('only_left', kn, a[k]))
        elif a[k] != b[k]:
            if isinstance(a, dict) and isinstance(b, dict):
                diff.append(diff_dict(kn, a[k], b[k]))
            else:
                diff.append(('differ', kn, a[k], b[k]))
    return diff


def BE_to_LE(value):
    """
    Convert Big Endian to Little Endian
    @param value: value expressed in Big Endian
    @param size: number of bytes generated
    @return: a string containing the value converted
    """

    return int("".join(["%2.2X" % ord(char) for char in reversed(value)]), 16)


def LE_to_BE(value, size):
    """
    Convert Little Endian to Big Endian
    @param value: value expressed in integer
    @param size: number of bytes generated
    @return: a string containing the value converted
    """

    data = ("%" + str(size * 2) + "." + str(size * 2) + "X") % value
    list_car = [data[i:i + 2] for i in range(0, len(data), 2)]
    list_car.reverse()
    return "".join([chr(int(car, 16)) for car in list_car])


# Register node with gnosis
nosis.add_class_to_store('Node', Node)
