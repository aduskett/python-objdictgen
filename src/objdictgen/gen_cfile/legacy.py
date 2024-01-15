# -*- coding: utf-8 -*-
#
#    This file is based on objdictgen from CanFestival
#
#    Copyright (C) 2022-2023  Svein Seldal, Laerdal Medical AS
#    Copyright (C): Edouard TISSERANT, Francis DUPIN and Laurent BESSARD
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#    USA
from objdictgen.gen_cfile.common import *
from objdictgen.maps import OD


def GenerateLegacyFileContent(node, headerfilepath, pointers_dict=None):
    """
    pointers_dict = {(Idx,Sidx):"VariableName",...}
    """

    # FIXME: Too many camelCase vars in here
    # pylint: disable=invalid-name

    context = CFileContext()
    pointers_dict = pointers_dict or {}
    texts = {}
    texts["maxPDOtransmit"] = 0
    texts["NodeName"] = node.Name
    texts["NodeID"] = node.ID
    texts["NodeType"] = node.Type
    texts["Description"] = node.Description or ""
    texts["iam_a_slave"] = 0
    if texts["NodeType"] == "slave":
        texts["iam_a_slave"] = 1

    context.default_string_size = node.DefaultStringSize
    # Compiling lists of indexes
    rangelist = [idx for idx in node.GetIndexes() if 0 <= idx <= 0x260]
    listindex = [idx for idx in node.GetIndexes() if 0x1000 <= idx <= 0xFFFF]
    communicationlist = [idx for idx in node.GetIndexes() if 0x1000 <= idx <= 0x11FF]
    variablelist = [idx for idx in node.GetIndexes() if 0x2000 <= idx <= 0xBFFF]

    # ------------------------------------------------------------------------------
    #                       Declaration of the value range types
    # ------------------------------------------------------------------------------

    valueRangeContent = ""
    strDefine = "\n#define valueRange_EMC 0x9F /* Type for index 0x1003 subindex 0x00 (only set of value 0 is possible) */"
    strSwitch = """    case valueRange_EMC:
      if (*(UNS8*)value != (UNS8)0) return OD_VALUE_RANGE_EXCEEDED;
      break;\n"""
    context.internal_types["valueRange_EMC"] = ("UNS8", "", "valueRange_EMC", True)
    num = 0
    for index in rangelist:
        rangename = node.GetEntryName(index)
        result = RE_RANGE.match(rangename)
        if result:
            num += 1
            typeindex = node.GetEntry(index, 1)
            typename = node.GetTypeName(typeindex)
            typeinfos = GetValidTypeInfos(context, typename)
            context.internal_types[rangename] = (
                typeinfos[0],
                typeinfos[1],
                f"valueRange_{num:d}",
            )
            minvalue = node.GetEntry(index, 2)
            maxvalue = node.GetEntry(index, 3)
            strDefine += f"\n#define valueRange_{num:d} 0x{index:02X} /* Type {typeinfos[0]}, {str(minvalue)} < value < {str(maxvalue)} */"
            strSwitch += f"    case valueRange_{num:d}:\n"
            if typeinfos[3] and minvalue <= 0:
                strSwitch += "      /* Negative or null low limit ignored because of unsigned type */;\n"
            else:
                strSwitch += f"      if (*({typeinfos[0]}*)value < ({typeinfos[0]}){str(minvalue)}) return OD_VALUE_TOO_LOW;\n"
            strSwitch += f"      if (*({typeinfos[0]}*)value > ({typeinfos[0]}){str(maxvalue)}) return OD_VALUE_TOO_HIGH;\n"
            strSwitch += "    break;\n"

    valueRangeContent += strDefine
    valueRangeContent += (
        "\nUNS32 {NodeName}_valueRangeTest (UNS8 typeValue, void * value)\n{{".format(
            **texts
        )
    )
    valueRangeContent += "\n  switch (typeValue) {\n"
    valueRangeContent += strSwitch
    valueRangeContent += "  }\n  return 0;\n}\n"

    # ------------------------------------------------------------------------------
    #            Creation of the mapped variables and object dictionary
    # ------------------------------------------------------------------------------

    mappedVariableContent = ""
    pointedVariableContent = ""
    strDeclareHeader = ""
    indexContents = {}
    index_callbacks = {}
    headerObjectDefinitionContent = ""
    for index in listindex:
        texts["index"] = index
        strindex = ""
        entry_infos = node.GetEntryInfos(index)
        params_infos = node.GetParamsEntry(index)
        texts["EntryName"] = entry_infos["name"]
        values = node.GetEntry(index)
        callbacks = node.HasEntryCallbacks(index)
        if index in variablelist:
            strindex += (
                "\n/* index 0x{index:04X} :   Mapped variable {EntryName} */\n".format(
                    **texts
                )
            )
        else:
            strindex += "\n/* index 0x{index:04X} :   {EntryName}. */\n".format(**texts)

        # Entry type is VAR
        if not isinstance(values, list):
            subentry_infos = node.GetSubentryInfos(index, 0)
            typename = GetTypeName(node, subentry_infos["type"])
            typeinfos = GetValidTypeInfos(context, typename, [values])
            if typename == "DOMAIN" and index in variablelist:
                if not typeinfos[1]:
                    raise ValueError(
                        f"Domain variable not initialized, index: 0x{index:04X}, subindex: 0x00"
                    )
            texts["subIndexType"] = typeinfos[0]
            if typeinfos[1] is not None:
                if params_infos["buffer_size"]:
                    texts["suffixe"] = f"[{params_infos['buffer_size']}]"
                else:
                    texts["suffixe"] = f"[{typeinfos[1]:d}]"
            else:
                texts["suffixe"] = ""
            texts["value"], texts["comment"] = ComputeValue(typeinfos[2], values)
            if index in variablelist:
                texts["name"] = RE_STARTS_WITH_DIGIT.sub(
                    r"_\1", FormatName(subentry_infos["name"])
                )
                strDeclareHeader += "extern {subIndexType} {name}{suffixe};\t\t/* Mapped at index 0x{index:04X}, subindex 0x00*/\n".format(
                    **texts
                )
                mappedVariableContent += "{subIndexType} {name}{suffixe} = {value};\t\t/* Mapped at index 0x{index:04X}, subindex 0x00 */\n".format(
                    **texts
                )
            else:
                strindex += "                    {subIndexType} {NodeName}_obj{index:04X}{suffixe} = {value};{comment}\n".format(
                    **texts
                )
            values = [values]
        else:
            subentry_infos = node.GetSubentryInfos(index, 0)
            typename = GetTypeName(node, subentry_infos["type"])
            typeinfos = GetValidTypeInfos(context, typename)
            if index == 0x1003:
                texts["value"] = 0
            else:
                texts["value"] = values[0]
            texts["subIndexType"] = typeinfos[0]
            strindex += "                    {subIndexType} {NodeName}_highestSubIndex_obj{index:04X} = {value:d}; /* number of subindex - 1*/\n".format(
                **texts
            )

            # Entry type is ARRAY
            if entry_infos["struct"] & OD.IdenticalSubindexes:
                subentry_infos = node.GetSubentryInfos(index, 1)
                typename = node.GetTypeName(subentry_infos["type"])
                typeinfos = GetValidTypeInfos(context, typename, values[1:])
                texts["subIndexType"] = typeinfos[0]
                if typeinfos[1] is not None:
                    texts["suffixe"] = f"[{typeinfos[1]:d}]"
                    texts["type_suffixe"] = "*"
                else:
                    texts["suffixe"] = ""
                    texts["type_suffixe"] = ""
                texts["length"] = values[0]
                if index in variablelist:
                    texts["name"] = RE_STARTS_WITH_DIGIT.sub(
                        r"_\1", FormatName(entry_infos["name"])
                    )
                    texts["values_count"] = str(len(values) - 1)
                    strDeclareHeader += "extern {subIndexType} {name}[{values_count}]{suffixe};\t\t/* Mapped at index 0x{index:04X}, subindex 0x01 - 0x{length:02X} */\n".format(
                        **texts
                    )
                    mappedVariableContent += "{subIndexType} {name}[]{suffixe} =\t\t/* Mapped at index 0x{index:04X}, subindex 0x01 - 0x{length:02X} */\n  {{\n".format(
                        **texts
                    )
                    for subindex, value in enumerate(values):
                        sep = ","
                        if subindex > 0:
                            if subindex == len(values) - 1:
                                sep = ""
                            value, comment = ComputeValue(typeinfos[2], value)
                            if len(value) == 2 and typename == "DOMAIN":
                                raise ValueError(
                                    "Domain variable not initialized, index : 0x{:04X}, subindex : 0x{:02X}".format(
                                        index, subindex
                                    )
                                )
                            mappedVariableContent += f"    {value}{sep}{comment}\n"
                    mappedVariableContent += "  };\n"
                else:
                    strindex += "                    {subIndexType}{type_suffixe} {NodeName}_obj{index:04X}[] = \n                    {{\n".format(
                        **texts
                    )
                    for subindex, value in enumerate(values):
                        sep = ","
                        if subindex > 0:
                            if subindex == len(values) - 1:
                                sep = ""
                            value, comment = ComputeValue(typeinfos[2], value)
                            strindex += f"                      {value}{sep}{comment}\n"
                    strindex += "                    };\n"
            else:
                texts["parent"] = RE_STARTS_WITH_DIGIT.sub(
                    r"_\1", FormatName(entry_infos["name"])
                )
                # Entry type is RECORD
                for subindex, value in enumerate(values):
                    texts["subindex"] = subindex
                    params_infos = node.GetParamsEntry(index, subindex)
                    if subindex > 0:
                        subentry_infos = node.GetSubentryInfos(index, subindex)
                        typename = GetTypeName(node, subentry_infos["type"])
                        typeinfos = GetValidTypeInfos(
                            context, typename, [values[subindex]]
                        )
                        texts["subIndexType"] = typeinfos[0]
                        if typeinfos[1] is not None:
                            if params_infos["buffer_size"]:
                                texts["suffixe"] = f"[{params_infos['buffer_size']}]"
                            else:
                                texts["suffixe"] = f"[{typeinfos[1]:d}]"
                        else:
                            texts["suffixe"] = ""
                        texts["value"], texts["comment"] = ComputeValue(
                            typeinfos[2], value
                        )
                        texts["name"] = FormatName(subentry_infos["name"])
                        if index in variablelist:
                            strDeclareHeader += "extern {subIndexType} {parent}_{name}{suffixe};\t\t/* Mapped at index 0x{index:04X}, subindex 0x{subindex:02X} */\n".format(
                                **texts
                            )
                            mappedVariableContent += "{subIndexType} {parent}_{name}{suffixe} = {value};\t\t/* Mapped at index 0x{index:04X}, subindex 0x{subindex:02X} */\n".format(
                                **texts
                            )
                        else:
                            strindex += "                    {subIndexType} {NodeName}_obj{index:04X}_{name}{suffixe} = {value};{comment}\n".format(
                                **texts
                            )
        headerObjectDefinitionContent += (
            f"\n#define {RE_NOTW.sub('_', texts['NodeName'])}_"
            f"{RE_NOTW.sub('_', texts['EntryName'])}_Idx "
            f"{str(format(texts['index'], '#04x'))}\n"
        )

        # Generating Dictionary C++ entry
        if callbacks:
            if index in variablelist:
                name = FormatName(entry_infos["name"])
            else:
                name = "{NodeName}_Index{index:04X}".format(**texts)
            name = RE_STARTS_WITH_DIGIT.sub(r"_\1", name)
            strindex += f"                    ODCallback_t {name}_callbacks[] = \n                     {{\n"
            for subindex in range(len(values)):
                strindex += "                       NULL,\n"
            strindex += "                     };\n"
            index_callbacks[index] = f"*callbacks = {name}_callbacks; "
        else:
            index_callbacks[index] = ""
        strindex += "                    subindex {NodeName}_Index{index:04X}[] = \n                     {{\n".format(
            **texts
        )
        generateSubIndexArrayComment = True

        for i in range(0, len(values)):
            if isinstance(values[i], str):
                values[i] = values[i].replace("\\x00", chr(0))

        for subindex, _ in enumerate(values):
            subentry_infos = node.GetSubentryInfos(index, subindex)
            params_infos = node.GetParamsEntry(index, subindex)
            if subindex < len(values) - 1:
                sep = ","
            else:
                sep = ""
            typename = node.GetTypeName(subentry_infos["type"])
            if entry_infos["struct"] & OD.IdenticalSubindexes:
                typeinfos = GetValidTypeInfos(context, typename, values[1:])
            else:
                typeinfos = GetValidTypeInfos(context, typename, [values[subindex]])
            if subindex == 0:
                if index == 0x1003:
                    typeinfos = GetValidTypeInfos(context, "valueRange_EMC")
                if entry_infos["struct"] & OD.MultipleSubindexes:
                    name = "{NodeName}_highestSubIndex_obj{index:04X}".format(**texts)
                elif index in variablelist:
                    name = FormatName(subentry_infos["name"])
                else:
                    name = FormatName(f"{texts['NodeName']}_obj{texts['index']:04X}")
            elif entry_infos["struct"] & OD.IdenticalSubindexes:
                if index in variablelist:
                    name = f"{FormatName(entry_infos['name'])}[{subindex - 1:d}]"
                else:
                    name = (
                        f"{texts['NodeName']}_obj{texts['index']:04X}[{subindex - 1:d}]"
                    )
            else:
                if index in variablelist:
                    name = FormatName(f"{entry_infos['name']}_{subentry_infos['name']}")
                else:
                    name = f"{texts['NodeName']}_obj{texts['index']:04X}_{FormatName(subentry_infos['name'])}"
            if typeinfos[2] == "visible_string":
                if params_infos["buffer_size"]:
                    sizeof = params_infos["buffer_size"]
                else:
                    sizeof = str(
                        max(len(values[subindex]), context.default_string_size)
                    )
            elif typeinfos[2] == "domain":
                sizeof = str(len(values[subindex]))
            else:
                sizeof = f"sizeof ({typeinfos[0]})"
            params = node.GetParamsEntry(index, subindex)
            if params["save"]:
                save = "|TO_BE_SAVE"
            else:
                save = ""
            strindex += (
                "                       {{ {}{}, {}, {}, (void*)&{} }}{}\n".format(
                    subentry_infos["access"].upper(),
                    save,
                    typeinfos[2],
                    sizeof,
                    RE_STARTS_WITH_DIGIT.sub(r"_\1", name),
                    sep,
                )
            )
            pointer_name = pointers_dict.get((index, subindex), None)
            if pointer_name is not None:
                pointedVariableContent += f"{typeinfos[0]}* {pointer_name} = &{name};\n"
            if not entry_infos["struct"] & OD.IdenticalSubindexes:
                generateSubIndexArrayComment = True
                headerObjectDefinitionContent += (
                    f"#define {RE_NOTW.sub('_', texts['NodeName'])}_"
                    f"{RE_NOTW.sub('_', texts['EntryName'])}_"
                    f"{RE_NOTW.sub('_', subentry_infos['name'])}_sIdx "
                    f"{str(format(subindex, '#04x'))}"
                )

                if params_infos["comment"]:
                    headerObjectDefinitionContent += (
                        f"    /* {params_infos['comment']}\n"
                    )

                else:
                    headerObjectDefinitionContent += "\n"
            elif generateSubIndexArrayComment:
                generateSubIndexArrayComment = False
                # Generate Number_of_Entries_sIdx define and write comment
                # about not generating defines for the rest of the array objects
                headerObjectDefinitionContent += (
                    f"#define {RE_NOTW.sub('_', texts['NodeName'])}_"
                    f"{RE_NOTW.sub('_', texts['EntryName'])}_"
                    f"{RE_NOTW.sub('_', subentry_infos['name'])}_sIdx "
                    f"{str(format(subindex, '#04x'))}\n"
                )

                headerObjectDefinitionContent += (
                    "/* subindex define not generated for array objects */\n"
                )
        strindex += "                     };\n"
        indexContents[index] = strindex

    # ------------------------------------------------------------------------------
    #                     Declaration of Particular Parameters
    # ------------------------------------------------------------------------------

    if 0x1003 not in communicationlist:
        entry_infos = node.GetEntryInfos(0x1003)
        texts["EntryName"] = entry_infos["name"]
        indexContents[
            0x1003
        ] = """\n/* index 0x1003 :   {EntryName} */
                    UNS8 {NodeName}_highestSubIndex_obj1003 = 0; /* number of subindex - 1*/
                    UNS32 {NodeName}_obj1003[] =
                    {{
                      0x0	/* 0 */
                    }};
                    ODCallback_t {NodeName}_Index1003_callbacks[] =
                     {{
                       NULL,
                       NULL,
                     }};
                    subindex {NodeName}_Index1003[] =
                     {{
                       {{ RW, valueRange_EMC, sizeof (UNS8), (void*)&{NodeName}_highestSubIndex_obj1003 }},
                       {{ RO, uint32, sizeof (UNS32), (void*)&{NodeName}_obj1003[0] }}
                     }};
""".format(
            **texts
        )

    if 0x1005 not in communicationlist:
        entry_infos = node.GetEntryInfos(0x1005)
        texts["EntryName"] = entry_infos["name"]
        indexContents[
            0x1005
        ] = """\n/* index 0x1005 :   {EntryName} */
                    UNS32 {NodeName}_obj1005 = 0x0;   /* 0 */
""".format(
            **texts
        )

    if 0x1006 not in communicationlist:
        entry_infos = node.GetEntryInfos(0x1006)
        texts["EntryName"] = entry_infos["name"]
        indexContents[
            0x1006
        ] = """\n/* index 0x1006 :   {EntryName} */
                    UNS32 {NodeName}_obj1006 = 0x0;   /* 0 */
""".format(
            **texts
        )

    if 0x1014 not in communicationlist:
        entry_infos = node.GetEntryInfos(0x1014)
        texts["EntryName"] = entry_infos["name"]
        indexContents[
            0x1014
        ] = """\n/* index 0x1014 :   {EntryName} */
                    UNS32 {NodeName}_obj1014 = 0x80 + 0x{NodeID:02X};   /* 128 + NodeID */
""".format(
            **texts
        )

    if 0x1016 in communicationlist:
        texts["heartBeatTimers_number"] = node.GetEntry(0x1016, 0)
    else:
        texts["heartBeatTimers_number"] = 0
        entry_infos = node.GetEntryInfos(0x1016)
        texts["EntryName"] = entry_infos["name"]
        indexContents[
            0x1016
        ] = """\n/* index 0x1016 :   {EntryName} */
                    UNS8 {NodeName}_highestSubIndex_obj1016 = 0;
                    UNS32 {NodeName}_obj1016[]={{0}};
""".format(
            **texts
        )

    if 0x1017 not in communicationlist:
        entry_infos = node.GetEntryInfos(0x1017)
        texts["EntryName"] = entry_infos["name"]
        indexContents[
            0x1017
        ] = """\n/* index 0x1017 :   {EntryName} */
                    UNS16 {NodeName}_obj1017 = 0x0;   /* 0 */
""".format(
            **texts
        )

    if 0x100C not in communicationlist:
        entry_infos = node.GetEntryInfos(0x100C)
        texts["EntryName"] = entry_infos["name"]
        indexContents[
            0x100C
        ] = """\n/* index 0x100C :   {EntryName} */
                    UNS16 {NodeName}_obj100C = 0x0;   /* 0 */
""".format(
            **texts
        )

    if 0x100D not in communicationlist:
        entry_infos = node.GetEntryInfos(0x100D)
        texts["EntryName"] = entry_infos["name"]
        indexContents[
            0x100D
        ] = """\n/* index 0x100D :   {EntryName} */
                    UNS8 {NodeName}_obj100D = 0x0;   /* 0 */
""".format(
            **texts
        )

    # ------------------------------------------------------------------------------
    #               Declaration of navigation in the Object Dictionary
    # ------------------------------------------------------------------------------

    strDeclareIndex = ""
    strDeclareSwitch = ""
    strQuickIndex = ""
    quick_index = {}
    for index_cat in INDEX_CATEGORIES:
        quick_index[index_cat] = {}
        for cat, idx_min, idx_max in CATEGORIES:
            quick_index[index_cat][cat] = 0
    maxPDOtransmit = 0
    for i, index in enumerate(listindex):
        texts["index"] = index
        strDeclareIndex += "  {{ (subindex*){NodeName}_Index{index:04X},sizeof({NodeName}_Index{index:04X})/sizeof({NodeName}_Index{index:04X}[0]), 0x{index:04X}}},\n".format(
            **texts
        )
        strDeclareSwitch += (
            f"       case 0x{index:04X}: i = {i:d};{index_callbacks[index]}break;\n"
        )
        for cat, idx_min, idx_max in CATEGORIES:
            if idx_min <= index <= idx_max:
                quick_index["lastIndex"][cat] = i
                if quick_index["firstIndex"][cat] == 0:
                    quick_index["firstIndex"][cat] = i
                if cat == "PDO_TRS":
                    maxPDOtransmit += 1
    texts["maxPDOtransmit"] = max(1, maxPDOtransmit)
    for index_cat in INDEX_CATEGORIES:
        strQuickIndex += f"\nconst quick_index {texts['NodeName']}_{index_cat} = {{\n"
        sep = ","
        for i, (cat, idx_min, idx_max) in enumerate(CATEGORIES):
            if i == len(CATEGORIES) - 1:
                sep = ""
            strQuickIndex += f"  {quick_index[index_cat][cat]:d}{sep} /* {cat} */\n"
        strQuickIndex += "};\n"

    # ------------------------------------------------------------------------------
    #                            Write File Content
    # ------------------------------------------------------------------------------

    fileContent = (
        FILE_HEADER
        + f"""
#include "{headerfilepath}"
"""
    )

    fileContent += f"""
/**************************************************************************/
/* Declaration of mapped variables                                        */
/**************************************************************************/
{mappedVariableContent}
"""

    fileContent += f"""
/**************************************************************************/
/* Declaration of value range types                                       */
/**************************************************************************/
{valueRangeContent}
"""

    fileContent += """
/**************************************************************************/
/* The node id                                                            */
/**************************************************************************/
/* node_id default value.*/
UNS8 {NodeName}_bDeviceNodeId = 0x{NodeID:02X};

/**************************************************************************/
/* Array of message processing information */

const UNS8 {NodeName}_iam_a_slave = {iam_a_slave:d};

""".format(
        **texts
    )
    if texts["heartBeatTimers_number"] > 0:
        declaration = "TIMER_HANDLE {NodeName}_heartBeatTimers[{heartBeatTimers_number:d}]".format(
            **texts
        )
        initializer = (
            "{TIMER_NONE" + ",TIMER_NONE" * (texts["heartBeatTimers_number"] - 1) + "}"
        )

        fileContent += f"{declaration} = {initializer};\n"
    else:
        fileContent += "TIMER_HANDLE {NodeName}_heartBeatTimers[1];\n".format(**texts)

    fileContent += """
/*
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

                               OBJECT DICTIONARY

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
*/
"""
    for index in sorted(indexContents):
        fileContent += indexContents[index]

    fileContent += f"""
/**************************************************************************/
/* Declaration of pointed variables                                       */
/**************************************************************************/
{pointedVariableContent}
"""

    fileContent += """
const indextable {NodeName}_objdict[] =
{{
""".format(
        **texts
    )
    fileContent += strDeclareIndex
    fileContent += """}};

const indextable * {NodeName}_scanIndexOD (UNS16 wIndex, UNS32 * errorCode, ODCallback_t **callbacks)
{{
    int i;
    *callbacks = NULL;
    switch(wIndex){{
""".format(
        **texts
    )
    fileContent += strDeclareSwitch
    fileContent += """       default:
            *errorCode = OD_NO_SUCH_OBJECT;
            return NULL;
    }}
    *errorCode = OD_SUCCESSFUL;
    return &{NodeName}_objdict[i];
}}

/*
 * To count at which received SYNC a PDO must be sent.
 * Even if no pdoTransmit are defined, at least one entry is computed
 * for compilations issues.
 */
s_PDO_status {NodeName}_PDO_status[{maxPDOtransmit:d}] = {{""".format(
        **texts
    )

    fileContent += (
        f"""{",".join(["s_PDO_status_Initializer"] * texts["maxPDOtransmit"])}}};\n"""
    )

    fileContent += strQuickIndex
    fileContent += """
const UNS16 {NodeName}_ObjdictSize = sizeof({NodeName}_objdict)/sizeof({NodeName}_objdict[0]);

CO_Data {NodeName}_Data = CANOPEN_NODE_DATA_INITIALIZER({NodeName});

""".format(
        **texts
    )

    # ------------------------------------------------------------------------------
    #                          Write Header File Content
    # ------------------------------------------------------------------------------

    texts["file_include_name"] = headerfilepath.replace(".", "_").upper()
    headerFileContent = (
        FILE_HEADER
        + """
#ifndef {file_include_name}
#define {file_include_name}

#include "data.h"

/* Prototypes of function provided by object dictionnary */
UNS32 {NodeName}_valueRangeTest (UNS8 typeValue, void * value);
const indextable * {NodeName}_scanIndexOD (UNS16 wIndex, UNS32 * errorCode, ODCallback_t **callbacks);

/* Master node data struct */
extern CO_Data {NodeName}_Data;
""".format(
            **texts
        )
    )
    headerFileContent += strDeclareHeader

    headerFileContent += "\n#endif // {file_include_name}\n".format(**texts)
    # ------------------------------------------------------------------------------
    #                          Write Header Object Defintions Content
    # ------------------------------------------------------------------------------
    texts["file_include_objdef_name"] = headerfilepath.replace(
        ".", "_OBJECTDEFINES_"
    ).upper()
    headerObjectDefinitionContent = (
        FILE_HEADER
        + """
#ifndef {file_include_objdef_name}
#define {file_include_objdef_name}

/*
    Object defines naming convention:
    General:
        * All characters in object names that does not match [a-zA-Z0-9_] will be replaced by '_'.
        * Case of object dictionary names will be kept as is.
    Index : Node object dictionary name +_+ index name +_+ Idx
    SubIndex : Node object dictionary name +_+ index name +_+ subIndex name +_+ sIdx
*/
""".format(
            **texts
        )
        + headerObjectDefinitionContent
        + """
#endif /* {file_include_objdef_name} */
""".format(
            **texts
        )
    )

    return fileContent, headerFileContent, headerObjectDefinitionContent
