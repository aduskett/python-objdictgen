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
import traceback
from past.builtins import execfile
from future.utils import raise_from
import colorama

from .nosis import pickle as nosis
from . import PROFILE_DIRECTORIES
from . import dbg, warning
from . import maps
from .maps import OD, MAPPING_DICTIONARY

if sys.version_info[0] >= 3:
    unicode = str  # pylint: disable=invalid-name
    ODict = dict
else:
    ODict = OrderedDict

Fore = colorama.Fore
Style = colorama.Style


# ------------------------------------------------------------------------------
#                         Utils
# ------------------------------------------------------------------------------

def GetIndexRange(index):
    for irange in maps.INDEX_RANGES:
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
        dbg(traceback.format_exc())
        raise_from(ValueError("Loading profile '%s' failed: %s" % (profilepath, exc)), exc)
        return None  # To satisfy linter only


# ------------------------------------------------------------------------------
#                         Search in a Mapping Dictionary
# ------------------------------------------------------------------------------

def FindTypeIndex(typename, mappingdictionary):
    """
    Return the index of the typename given by searching in mappingdictionary
    """
    return {
        values["name"]: index
        for index, values in mappingdictionary.items()
        if index < 0x1000
    }.get(typename)


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
                            yield (index, i + 1, infos["size"], computed_name)
                    else:
                        computed_name = name
                        if compute:
                            computed_name = StringFormat(computed_name, 1, subindex)
                        yield (index, subindex, infos["size"], computed_name)


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
        self.IndexOrder = []

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
            result = self.CompileValue(self.Dictionary[index], index, compute)
            # This option ensures that the function consistently returns a list
            if aslist:
                return [result]
            return result
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
                        line = maps.DEFAULT_PARAMS.copy()
                        if i in self.ParamsDictionary[index]:
                            line.update(self.ParamsDictionary[index][i])
                        result.append(line)
                    return result
                return [maps.DEFAULT_PARAMS.copy() for i in range(len(self.Dictionary[index]) + 1)]
            result = maps.DEFAULT_PARAMS.copy()
            if index in self.ParamsDictionary:
                result.update(self.ParamsDictionary[index])
            # This option ensures that the function consistently returns a list
            if aslist:
                return [result]
            return result
        if subindex == 0 and not isinstance(self.Dictionary[index], list):
            result = maps.DEFAULT_PARAMS.copy()
            if index in self.ParamsDictionary:
                result.update(self.ParamsDictionary[index])
            return result
        if isinstance(self.Dictionary[index], list) and 0 <= subindex <= len(self.Dictionary[index]):
            result = maps.DEFAULT_PARAMS.copy()
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

    # FIXME: Unused. Delete this?
    # def RemoveUserType(self, index):
    #     type_ = self.GetEntry(index, 1)
    #     for i in self.UserMapping:  # pylint: disable=consider-using-dict-items
    #         for value in self.UserMapping[i]["values"]:
    #             if value["type"] == index:
    #                 value["type"] = type_
    #     self.RemoveMappingEntry(index)
    #     self.RemoveEntry(index)

    def Copy(self):
        """
        Return a copy of the node
        """
        return copy.deepcopy(self)

    def GetDict(self):
        return copy.deepcopy(self.__dict__)

    def GetIndexDict(self, index):
        ''' Return a dict representation of the index '''
        obj = {}
        if index in self.Dictionary:
            obj['dictionary'] = self.Dictionary[index]
        if index in self.ParamsDictionary:
            obj['params'] = self.ParamsDictionary[index]
        if index in self.Profile:
            obj['profile'] = self.Profile[index]
        if index in self.DS302:
            obj['ds302'] = self.DS302[index]
        if index in self.UserMapping:
            obj['user'] = self.UserMapping[index]
        if index in maps.MAPPING_DICTIONARY:
            obj['built-in'] = maps.MAPPING_DICTIONARY[index]
        obj['base'] = self.GetBaseIndex(index)
        obj['groups'] = tuple(g for g in ('profile', 'ds302', 'user', 'built-in') if g in obj)
        return copy.deepcopy(obj)

    def GetIndexes(self):
        """
        Return a sorted list of indexes in Object Dictionary
        """
        return list(sorted(self.Dictionary))

    def PrintParams(self, keys=None, short=False, compact=False, unused=False, verbose=False, raw=False):
        """
        Generator for printing the dictionary values
        """

        # Get the indexes to print and determine the order
        keys = keys or self.GetAllParameters(sort=True)

        index_range = None
        for k in keys:

            obj = self.GetEntryInfos(k)
            if not obj:
                continue

            # Get the node flags
            flags = self.GetEntryFlags(k)
            if 'Unused' in flags and not unused:
                continue

            # Print the parameter range header
            ir = GetIndexRange(k)
            if index_range != ir:
                index_range = ir
                if not compact:
                    yield (Fore.YELLOW + ir["description"] + Style.RESET_ALL)

            # Replace flags for formatting
            for i, flag in enumerate(flags):
                if flag == 'Missing':
                    flags[i] = Fore.RED + ' *MISSING* ' + Style.RESET_ALL

            # Print formattings
            fmt = {
                'key': "%s0x%04x (%d)%s" %(Fore.GREEN, k, k, Style.RESET_ALL),
                'name': self.GetEntryName(k),
                'struct': maps.ODStructTypes.to_string(obj.get('struct'), '???').upper(),
                'flags': "  %s%s%s" %(Fore.CYAN, ', '.join(flags), Style.RESET_ALL) if flags else '',
                'pre': '    ' if not compact else '',
            }

            # ** PRINT PARAMETER **
            yield ("{pre}{key}  {name}   [{struct}]{flags}".format(**fmt))

            # Omit printing sub index data if:
            if short or k not in self.Dictionary:
                continue

            infos = []
            for info in self.GetAllSubentryInfos(k, compute=not raw):

                # Prepare data for printing

                i = info['subindex']
                typename = self.GetTypeName(info['type'])
                value = info['value']

                # Special formatting on value
                if isinstance(value, str):
                    value = '"' + value + '"'
                elif i and index_range and index_range["name"] in ('rpdom', 'tpdom'):
                    index, subindex, _ = self.GetMapIndex(value)
                    pdo = self.GetSubentryInfos(index, subindex)
                    suffix = '???' if value else ''
                    if pdo:
                        suffix = '%s' % (pdo["name"],)
                    value = "0x%x  %s" % (value, suffix)
                elif i and value and (k in (4120, ) or 'COB ID' in info["name"]):
                    value = "0x%x" % (value)
                else:
                    value = str(value)

                comment = info['comment'] or ''
                if comment:
                    comment = Fore.LIGHTBLACK_EX + ('/* %s */' % info.get('comment')) + Style.RESET_ALL

                # Omit printing this subindex if:
                if not verbose and i == 0 and fmt['struct'] in ('RECORD', 'NRECORD', 'ARRAY', 'NARRAY') and not comment:
                    continue

                # Print formatting
                infos.append({
                    'i': "%02d" % i,
                    'access': info['access'],
                    'pdo': 'P' if info['pdo'] else ' ',
                    'name': info['name'],
                    'type': typename,
                    'value': value,
                    'comment': comment,
                    'pre': fmt['pre'],
                })

            if not infos:
                continue

            # Calculate the max width for each of the columns
            w = {
                col: max(len(str(row[col])) for row in infos) or ''
                for col in infos[0]
            }

            # Generate a format string based on the calculcated column widths
            fmt = "{pre}    {i:%ss}  {access:%ss}  {pdo:%ss}  {name:%ss}  {type:%ss}  {value:%ss}  {comment}" % (
                         w["i"],  w["access"],  w["pdo"],  w["name"],  w["type"],  w["value"]  # noqa: E126, E241
            )

            # Print each line using the generated format string
            for info in infos:
                yield (fmt.format(**info))

            if not compact and infos:
                yield ("")

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

    def GetEntryFlags(self, index):
        flags = []
        info = self.GetEntryInfos(index)
        if not info:
            return flags

        if info.get('need'):
            flags.append("Mandatory")
        if index in self.UserMapping:
            flags.append("User")
        if index in self.DS302:
            flags.append("DS-302")
        if index in self.Profile:
            flags.append("Profile")
        if self.HasEntryCallbacks(index):
            flags.append('CB')
        if index not in self.Dictionary:
            if index in self.DS302 or index in self.Profile:
                flags.append("Unused")
            else:
                flags.append("Missing")
        return flags

    def GetAllSubentryInfos(self, index, compute=True):
        values = self.GetEntry(index, compute=compute, aslist=True)
        entries = self.GetParamsEntry(index, aslist=True)
        for i, (value, entry) in enumerate(zip(values, entries)):
            info = {
                'subindex': i,
                'value': value,
            }
            info.update(self.GetSubentryInfos(index, i))
            info.update(entry)
            yield info

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
        list_ = list(FindMapVariableList(MAPPING_DICTIONARY, self, compute))
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
        return {
            index: (self.GetTypeName(index), valuetype)
            for index, valuetype in maps.CUSTOMISABLE_TYPES
        }

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

    def GetAllParameters(self, sort=False):
        """ Get a list of all the parameters """

        order = list(self.UserMapping.keys())
        order += [k for k in self.Dictionary.keys() if k not in order]
        order += [k for k in self.ParamsDictionary.keys() if k not in order]
        if self.Profile:
            order += [k for k in self.Profile.keys() if k not in order]
        if self.DS302:
            order += [k for k in self.DS302.keys() if k not in order]

        if sort:
            order = sorted(order)

        # Is there a recorded order that should supersede the above sequence?
        # Node might not contain IndexOrder if read from legacy od file
        elif hasattr(self, 'IndexOrder'):
            # Pick k from IndexOrder which is present in order
            keys = [k for k in self.IndexOrder if k in order]
            # Append any missing k from order that is not in IndexOrder
            keys += (k for k in order if k not in keys)
            order = keys

        return order


# ------------------------------------------------------------------------------
#                            Comparison and checks
# ------------------------------------------------------------------------------

    def Validate(self, fix=False):
        ''' Verify any inconsistencies when loading an OD. The function will
            attempt to fix the data if the correct flag is enabled.
        '''

        # Because the sorted() is used below, using set() here is of no importance
        params = set(self.Dictionary.keys())
        params.update(self.ParamsDictionary.keys())

        for k in sorted(params):

            name = self.GetEntryName(k)
            if k not in self.Dictionary:
                warning("WARNING: 0x%04x (%d) '%s': Parameter without any value" % (k, k, name))
                if fix:
                    del self.ParamsDictionary[k]
                continue

            values = self.GetEntry(k, aslist=True)
            entries = self.GetParamsEntry(k, aslist=True)

            for i, (value, entry) in enumerate(zip(values, entries)):
                info = self.GetSubentryInfos(k, i)
                info.update(entry)

                if not info['name']:
                    warning("WARNING: 0x%04x (%d) '%s': Sub-parameter %02d has no name" % (k, k, name, i))
                    if fix:
                        self.UserMapping[k]['values'][i]['name'] = 'Subindex %02x' %(i, )


def BE_to_LE(value):
    """
    Convert Big Endian to Little Endian
    @param value: value expressed in Big Endian
    @param size: number of bytes generated
    @return: a string containing the value converted
    """

    # FIXME: The function title is confusing as the input data type (str) is
    # different than the output (int)
    return int("".join(["%2.2X" % ord(char) for char in reversed(value)]), 16)


def LE_to_BE(value, size):
    """
    Convert Little Endian to Big Endian
    @param value: value expressed in integer
    @param size: number of bytes generated
    @return: a string containing the value converted
    """

    # FIXME: The function title is confusing as the input data type (int) is
    # different than the output (str)
    data = ("%" + str(size * 2) + "." + str(size * 2) + "X") % value
    list_car = [data[i:i + 2] for i in range(0, len(data), 2)]
    list_car.reverse()
    return "".join([chr(int(car, 16)) for car in list_car])


# Register node with gnosis
nosis.add_class_to_store('Node', Node)
