import os
import sys
import wx
import csv
import wx.adv
import wx.html
import wx.lib.inspection
import logging
import threading
import time
import datetime
from datetime import datetime
from queue import Queue
from datetime import date
from sys import maxsize
from engine.local_db import connect_to_db, create_session, get_banned_strings, add_banned_string, delete_banned_string

class BannedStringsFrame(wx.Frame):
    """Whatsapp GUI Frame"""
    def __init__(self, parent, title = None, logger = None):
        self.title = title or "Banned Strings"
        wx.Frame.__init__(self, parent, -1, self.title)
        self.parent  = parent

        self.logger = logger or logging.getLogger(__name__)

        stop_words = self.fetch_stop_words()



        self.createPanel(stop_words)


        #--------------------------------
    def createPanel(self, stop_words):
        self.mainPanel = BannedStringsPanel(self, self.logger, stop_words)
        self.box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_sizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.box_sizer.SetSizeHints(self)
        self.SetSizer(self.box_sizer)
        self.Layout()

    def fetch_engine(self):
        return connect_to_db()


    def fetch_stop_words(self):
        self.engine = self.fetch_engine()
        
        stop_words = []
        if self.engine is False:
            self.logger.error("Unable to connect to database")
            return []
        else:
            session = create_session(self.engine)
            stop_words = get_banned_strings(session)
            session.close()
            self.logger.info("Fetched %s stopwords successfully", len(stop_words))
            return stop_words




    def OnCloseWindow(self, event):
        self.Destroy()


    
class BannedStringsPanel(wx.Panel):
    def __init__(self, parent, logger = None, stop_words = None):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.stop_words = stop_words

        # get a logger
        self.logger = logger or logging.getLogger(__name__)               
        self.layout()

    #---------------------------------------------------------
    def layout(self):

        # create main horizontal sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        control_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # create main control buttons
        btnData = [
            ("Add String", self.addString),
            ("Remove String",  self.removeString)]
        self.create_buttons(control_button_sizer, btnData, flag=wx.ALL)

        
        # create combo box
        self.create_combo()


        self.mainSizer.Add(control_button_sizer, 0)

        #self.SetAutoLayout(True)
        self.mainSizer.SetSizeHints(self)
        self.SetSizer(self.mainSizer)
        self.Layout()

    def create_combo(self):
        self.banned_string_combos = wx.CheckListBox(parent = self, id = -1, choices = list(self.stop_words.keys()), style=wx.LB_MULTIPLE)
        self.combo_sizer= wx.StaticBoxSizer(wx.VERTICAL, self, "Banned Strings to be filtered")
        self.combo_sizer.Add(self.banned_string_combos, 1, wx.EXPAND|wx.ALL, 2)
        self.mainSizer.Add(self.combo_sizer, 1, wx.EXPAND|wx.ALL, 2)
        #self.mainSizer.Add(combo_sizer, 1, wx.EXPAND|wx.ALL, 2)


    #-----------------------------------------------------
    def create_buttons(self, sizer, btnData, flag = None):

            
        for data in btnData:
            label, handler = data
            self.btnBuilder(label, sizer, handler, flag)

    
    #--------------------------------------------
    def btnBuilder(self, label, sizer, handler, flag = None):
        """
        Builds a button, binds it to an event handler and adds it to a sizer
        """
        btn = wx.Button(self, label=label)
        btn.Bind(wx.EVT_BUTTON, handler)
        if flag is None:
            sizer.Add(btn, 0, 3)
        else:
            sizer.Add(btn, 0,flag , 3)
        return btn


    

    def addString(self, evt):
        message = "Enter name of group to message"
        dialog_message = wx.GetTextFromUser(message, caption="Input text", default_value="", parent=None)
        if dialog_message != "":
            if dialog_message not in self.stop_words:

                # save string in database
                session = self.get_session()
                try:
                    
                    add_banned_string(session, dialog_message)
                except Exception as e:
                    self.logger.error("Unable to add string to database [%s]", dialog_message, exc_info=1)
                else:
                    self.refresh_display()

                    wx.MessageBox("Successfully added to database", "Success", wx.OK | wx.ICON_INFORMATION)
                finally:
                    session.close()
            else:
                wx.MessageBox("Group Name already in the list", "Error", wx.OK | wx.ICON_ERROR)
    def refresh_display(self):
            self.stop_words = self.parent.fetch_stop_words()
            self.banned_string_combos.Destroy()
            self.banned_string_combos = wx.CheckListBox(parent = self, id = -1, choices = list(self.stop_words.keys()), style=wx.LB_MULTIPLE)

            self.combo_sizer.Add(self.banned_string_combos, 1, wx.EXPAND|wx.ALL, 2)

            
            #self.Hide()
            self.Refresh()
            self.Update()
            self.Layout()
            self.Fit()

    def get_session(self):
        if self.parent.engine is False:
            self.logger.error("Unable to connect to database")
            return False
        else:
            session = create_session(self.parent.engine)
            return session


    def removeString(self, evt):
        selected_strings = self.banned_string_combos.GetCheckedStrings()
        if len(selected_strings) > 0:
            # delete string'# get string ids
            string_ids = [self.stop_words[word] for word in selected_strings]
            session = self.get_session()
            try:
                if session is not False:
                    delete_banned_string(session, string_ids )
            except Exception as e:
                self.logger.error("Unable to delete string", exc_info=1)
            else:
                self.refresh_display()

                wx.MessageBox("Successfully deleted from database", "Delete Success", wx.OK | wx.ICON_INFORMATION)
            finally:
                if session:
                    session.close()
            
            # refresh database
        else:
            wx.MessageBox("You have not selected anything", "Error", wx.OK | wx.ICON_ERROR)
