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
from engine.db import Db
from engine.posta import Posta

class CategoryPostFrame(wx.Frame):
    """Whatsapp GUI Frame"""
    def __init__(self,  parent, table_list, db, title = None, logger = None):
        self.title = title or "Category Breakdown"
        wx.Frame.__init__(self, parent, -1, self.title)
        self.parent  = parent

        self.logger = logger or logging.getLogger(__name__)

        self.db = db
        # fetch database as a list of categories and count
        self.category_summary = self.db.fetch_category_statistics(table_list)


        self.createPanel()


        #--------------------------------
        

    def createPanel(self):
        self.mainPanel = CategoryPostPanel(self, self.category_summary, self.parent, self.logger)
        self.box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_sizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.box_sizer.SetSizeHints(self)
        self.SetSizer(self.box_sizer)
        self.Layout()




    def OnCloseWindow(self, event):
        self.db.close_conn()
        self.Destroy()




class CategoryPostPanel(wx.Panel):
    def __init__(self, parent, category_summary, parent_window, logger = None):
        wx.Panel.__init__(self, parent)

        self.parent_window = parent_window


        self.category_summary = category_summary
        
        # get a logger
        self.logger = logger or logging.getLogger(__name__) 
        self.posta = Posta()
          


               
        self.layout()

    #---------------------------------------------------------
    def layout(self):

        # create main horizontal sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        control_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # create main control buttons
        btnData = [
            ("Begin Posting", self.beginPosting),
            ("Stop Posting",  self.stopPosting)]
        self.create_buttons(control_button_sizer, btnData, flag=wx.ALL)

        self.mainSizer.Add(control_button_sizer, 0)

        # create combo box
        self.create_combo()


        
        #self.SetAutoLayout(True)
        self.mainSizer.SetSizeHints(self)
        self.SetSizer(self.mainSizer)
        self.Layout()
    
    
    #-----------------------------------------------------
    def create_buttons(self, sizer, btnData, flag = None):

            
        for data in btnData:
            label, handler = data
            self.btnBuilder(label, sizer, handler, flag)


        #----------------------------------------------------------------------
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

    ##helper function to create combo box
    def create_combo(self):
        """
        Iterates through categories_combo box
        # add to sizer
        """
        self.return_category_combos()
        for table in self.category_combos.keys():
            combo_sizer= wx.StaticBoxSizer(wx.VERTICAL, self, table)
            if self.category_summary[table] != []:
                combo_sizer.Add(self.category_combos[table], 1, wx.EXPAND|wx.ALL, 2)
                self.mainSizer.Add(combo_sizer, 1, wx.EXPAND|wx.ALL, 2)
            else:
                combo_sizer.Add(wx.StaticText(self, -1, "No posts for this database"), 0, wx.ALIGN_CENTER)
                self.mainSizer.Add(combo_sizer, 0, wx.ALL, 2)
        



    def return_category_combos(self):
        
        self.category_combos = {}
        self.combo_dictionary = {}

        for table in self.category_summary.keys():
            """
            Iterates through categories
            Output combobox for each category
            """
            combo_choices = {}
            
            for counter,item in enumerate(self.category_summary[table]):
                if item[2] == "False":
                    if self.category_summary[table][counter - 1][2] == "True":
                        published = self.category_summary[table][counter - 1][0]
                    else:
                        published = 0
                    combo_choices["{posts} Posts available for {category}. {published} aleardy published".format(posts = item[0], category = item[1], published = published )] = item[1]

            self.combo_dictionary[table] = combo_choices

            if self.category_summary[table] != []:
                self.category_combos[table] = wx.CheckListBox(parent = self, id = -1, choices = list(combo_choices.keys()), style=wx.LB_MULTIPLE)
            else:
                self.category_combos[table] = None
        
        



    def beginPosting(self, evt):
        # refer to parent object
        # pass category names
        categories = {}
        for k,combo in self.category_combos.items():
            if combo is not None:
                categories[k] = combo.GetCheckedStrings()
        print(categories)
        processed_categories = {}
        for category in categories.keys():
            category_list = []
            for l in categories[category]:
                category_list.append(self.combo_dictionary[category][l])
            processed_categories[category] = category_list
        print(processed_categories)
        self.parent_window.beginCategoryRestPosting(evt, processed_categories)
        self.Hide()



    def stopPosting(self, evt):
        self.parent_window.stopPosting(evt)
