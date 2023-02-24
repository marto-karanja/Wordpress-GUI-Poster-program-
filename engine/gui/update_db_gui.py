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
from engine.db_remote_ssh import Db as questions_db
from engine.local_db import connect_to_db, create_session, get_banned_strings, add_banned_string, delete_banned_string

class UpdateDbFrame(wx.Frame):
    """Whatsapp GUI Frame"""
    def __init__(self, parent, title = None, logger = None, db = None):
        self.title = title or "Update Database Tables"
        wx.Frame.__init__(self, parent, -1, self.title)
        self.parent  = parent

        self.logger = logger or logging.getLogger(__name__)

        
        



        self.createPanel(db)


        #--------------------------------
    def createPanel(self, db):
        self.mainPanel = UpdateDbPanel(self, self.logger, db)
        self.box_sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_sizer.Add(self.mainPanel, 1, wx.EXPAND)


    def OnCloseWindow(self, event):
        self.Destroy()


class UpdateDbPanel(wx.Panel):
    def __init__(self, parent, logger = None, db = None):
        wx.Panel.__init__(self, parent)

        self.parent = parent

        self.SetMinSize((800,800))
        
        # get a logger
        self.logger = logger or logging.getLogger(__name__)
        self.db = questions_db(self.logger)

        self.layout()


    def layout(self):

        # create main horizontal sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        control_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # create main control buttons
        btnData = [
            ("update Tables", self.updateDb),
            ("Update New Entries",  self.updateDb)]
        self.create_buttons(control_button_sizer, btnData, flag=wx.EXPAND, vertical = True)

        self.logTxtField = wx.TextCtrl(self, -1, "", style=wx.TE_RICH|wx.TE_MULTILINE)


        self.mainSizer.Add(control_button_sizer, 3, wx.EXPAND|wx.ALL)
        self.mainSizer.Add(self.logTxtField,8, wx.EXPAND|wx.ALL)

        #self.SetAutoLayout(True)
        
        self.mainSizer.SetSizeHints(self)
        self.SetSizer(self.mainSizer)
        self.Layout()


    #-----------------------------------------------------
    

    #-----------------------------------------------------
    def create_buttons(self, sizer, btnData, flag = None, vertical = None):

            
        for data in btnData:
            label, handler = data

            if vertical is not None:
                self.btnBuilder(label, sizer, handler, flag, vertical = True)
            else:
                self.btnBuilder(label, sizer, handler, flag)

    
    #--------------------------------------------
    def btnBuilder(self, label, sizer, handler, flag = None, vertical = None):
        """
        Builds a button, binds it to an event handler and adds it to a sizer
        """
        btn = wx.Button(self, label=label)
        btn.Bind(wx.EVT_BUTTON, handler)
        if flag is None:
            if vertical is not None:
                sizer.Add(btn, 1, 3)
            else:
                sizer.Add(btn, 0, 3)
        else:
            if vertical is not None:
                sizer.Add(btn, 1,flag , 3)
            else:
                sizer.Add(btn, 0,flag , 3)
        return btn
    

    def updateDb(self, evt):
        # launch thread
        update_thread = threading.Thread(target = self.update_tables)
        update_thread.start()

    def update_tables(self):
        self.db.update_all_tables_word_count(window = self)

    def log_message_to_txt_field(self, msg):
        self.logTxtField.AppendText(msg)
        self.logTxtField.AppendText("\n") 

