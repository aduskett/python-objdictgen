from __future__ import absolute_import
from builtins import object
from builtins import range

import sys

import wx

from . import commondialogs as cdia
from .. import node as nod

if sys.version_info[0] >= 3:
    unicode = str  # pylint: disable=invalid-name


class NodeEditorTemplate(object):

    EDITMENU_ID = None

    def __init__(self, manager, frame, mode_solo):
        self.Manager = manager
        self.Frame = frame
        self.ModeSolo = mode_solo

        self.BusId = None
        self.Closing = False

    def SetBusId(self, bus_id):
        self.BusId = bus_id

    def GetBusId(self):
        return self.BusId

    def IsClosing(self):
        return self.Closing

    def OnAddSDOServerMenu(self, event):  # pylint: disable=unused-argument
        self.Manager.AddSDOServerToCurrent()
        self.RefreshBufferState()
        self.RefreshCurrentIndexList()

    def OnAddSDOClientMenu(self, event):  # pylint: disable=unused-argument
        self.Manager.AddSDOClientToCurrent()
        self.RefreshBufferState()
        self.RefreshCurrentIndexList()

    def OnAddPDOTransmitMenu(self, event):  # pylint: disable=unused-argument
        self.Manager.AddPDOTransmitToCurrent()
        self.RefreshBufferState()
        self.RefreshCurrentIndexList()

    def OnAddPDOReceiveMenu(self, event):  # pylint: disable=unused-argument
        self.Manager.AddPDOReceiveToCurrent()
        self.RefreshBufferState()
        self.RefreshCurrentIndexList()

    def OnAddMapVariableMenu(self, event):  # pylint: disable=unused-argument
        self.AddMapVariable()

    def OnAddUserTypeMenu(self, event):  # pylint: disable=unused-argument
        self.AddUserType()

    def OnRefreshMenu(self, event):  # pylint: disable=unused-argument
        self.RefreshCurrentIndexList()

    def RefreshCurrentIndexList(self):
        pass

    def RefreshStatusBar(self):
        pass

    def SetStatusBarText(self, selection, manager):
        if selection:
            index, subindex = selection
            if manager.IsCurrentEntry(index):
                self.Frame.HelpBar.SetStatusText("Index: 0x%04X" % index, 0)
                self.Frame.HelpBar.SetStatusText("Subindex: 0x%02X" % subindex, 1)
                entryinfos = manager.GetEntryInfos(index)
                name = entryinfos["name"]
                category = "Optional"
                if entryinfos["need"]:
                    category = "Mandatory"
                struct = "VAR"
                number = ""
                if entryinfos["struct"] & nod.OD.IdenticalIndexes:
                    number = " possibly defined %d times" % entryinfos["nbmax"]
                if entryinfos["struct"] & nod.OD.IdenticalSubindexes:
                    struct = "ARRAY"
                elif entryinfos["struct"] & nod.OD.MultipleSubindexes:
                    struct = "RECORD"
                text = "%s: %s entry of struct %s%s." % (name, category, struct, number)
                self.Frame.HelpBar.SetStatusText(text, 2)
            else:
                for i in range(3):
                    self.Frame.HelpBar.SetStatusText("", i)
        else:
            for i in range(3):
                self.Frame.HelpBar.SetStatusText("", i)

    def RefreshProfileMenu(self):
        if self.EDITMENU_ID is not None:
            profile = self.Manager.GetCurrentProfileName()
            edititem = self.Frame.EditMenu.FindItemById(self.EDITMENU_ID)
            if edititem:
                length = self.Frame.AddMenu.GetMenuItemCount()
                for _ in range(length - 6):
                    additem = self.Frame.AddMenu.FindItemByPosition(6)
                    self.Frame.AddMenu.Delete(additem.GetId())
                if profile not in ("None", "DS-301"):
                    edititem.SetText("%s Profile" % profile)
                    edititem.Enable(True)
                    self.Frame.AddMenu.AppendSeparator()
                    for text, _ in self.Manager.GetCurrentSpecificMenu():
                        new_id = wx.NewId()
                        self.Frame.AddMenu.Append(help='', id=new_id, kind=wx.ITEM_NORMAL, text=text)
                        self.Frame.Bind(wx.EVT_MENU, self.GetProfileCallBack(text), id=new_id)
                else:
                    edititem.SetText("Other Profile")
                    edititem.Enable(False)

# ------------------------------------------------------------------------------
#                            Buffer Functions
# ------------------------------------------------------------------------------

    def RefreshBufferState(self):
        pass

    def OnUndoMenu(self, event):  # pylint: disable=unused-argument
        self.Manager.LoadCurrentPrevious()
        self.RefreshCurrentIndexList()
        self.RefreshBufferState()

    def OnRedoMenu(self, event):  # pylint: disable=unused-argument
        self.Manager.LoadCurrentNext()
        self.RefreshCurrentIndexList()
        self.RefreshBufferState()

# ------------------------------------------------------------------------------
#                          Editing Profiles functions
# ------------------------------------------------------------------------------

    def OnCommunicationMenu(self, event):  # pylint: disable=unused-argument
        dictionary, current = self.Manager.GetCurrentCommunicationLists()
        self.EditProfile("Edit DS-301 Profile", dictionary, current)

    def OnOtherCommunicationMenu(self, event):  # pylint: disable=unused-argument
        dictionary, current = self.Manager.GetCurrentDS302Lists()
        self.EditProfile("Edit DS-302 Profile", dictionary, current)

    def OnEditProfileMenu(self, event):  # pylint: disable=unused-argument
        title = "Edit %s Profile" % self.Manager.GetCurrentProfileName()
        dictionary, current = self.Manager.GetCurrentProfileLists()
        self.EditProfile(title, dictionary, current)

    def EditProfile(self, title, dictionary, current):
        dialog = cdia.CommunicationDialog(self.Frame)
        dialog.SetTitle(title)
        dialog.SetIndexDictionary(dictionary)
        dialog.SetCurrentList(current)
        dialog.RefreshLists()
        if dialog.ShowModal() == wx.ID_OK:
            new_profile = dialog.GetCurrentList()
            addinglist = []
            removinglist = []
            for index in new_profile:
                if index not in current:
                    addinglist.append(index)
            for index in current:
                if index not in new_profile:
                    removinglist.append(index)
            self.Manager.ManageEntriesOfCurrent(addinglist, removinglist)
            self.Manager.BufferCurrentNode()
            self.RefreshBufferState()

        dialog.Destroy()

    def GetProfileCallBack(self, text):
        def ProfileCallBack(event):  # pylint: disable=unused-argument
            self.Manager.AddSpecificEntryToCurrent(text)
            self.RefreshBufferState()
            self.RefreshCurrentIndexList()
        return ProfileCallBack

# ------------------------------------------------------------------------------
#                         Edit Node informations function
# ------------------------------------------------------------------------------

    def OnNodeInfosMenu(self, event):  # pylint: disable=unused-argument
        dialog = cdia.NodeInfosDialog(self.Frame)
        name, id_, type_, description = self.Manager.GetCurrentNodeInfos()
        defaultstringsize = self.Manager.GetCurrentNodeDefaultStringSize()
        dialog.SetValues(name, id_, type_, description, defaultstringsize)
        if dialog.ShowModal() == wx.ID_OK:
            name, id_, type_, description, defaultstringsize = dialog.GetValues()
            self.Manager.SetCurrentNodeInfos(name, id_, type_, description)
            self.Manager.SetCurrentNodeDefaultStringSize(defaultstringsize)
            self.RefreshBufferState()
            self.RefreshCurrentIndexList()
            self.RefreshProfileMenu()

# ------------------------------------------------------------------------------
#                           Add User Types and Variables
# ------------------------------------------------------------------------------

    def AddMapVariable(self):
        index = self.Manager.GetCurrentNextMapIndex()
        if index:
            dialog = cdia.MapVariableDialog(self.Frame)
            dialog.SetIndex(index)
            if dialog.ShowModal() == wx.ID_OK:
                try:
                    self.Manager.AddMapVariableToCurrent(*dialog.GetValues())
                    self.RefreshBufferState()
                    self.RefreshCurrentIndexList()
                except Exception as exc:  # pylint: disable=broad-except
                    self.ShowErrorMessage(exc)
            dialog.Destroy()
        else:
            self.ShowErrorMessage("No map variable index left!")

    def AddUserType(self):
        dialog = cdia.UserTypeDialog(self)
        dialog.SetTypeList(self.Manager.GetCustomisableTypes())
        if dialog.ShowModal() == wx.ID_OK:
            try:
                self.Manager.AddUserTypeToCurrent(*dialog.GetValues())
                self.RefreshBufferState()
                self.RefreshCurrentIndexList()
            except Exception as exc:  # pylint: disable=broad-except
                self.ShowErrorMessage(exc)
        dialog.Destroy()

    def ShowErrorMessage(self, message):
        message = wx.MessageDialog(self.Frame, message, "Error", wx.OK | wx.ICON_ERROR)
        message.ShowModal()
        message.Destroy()
