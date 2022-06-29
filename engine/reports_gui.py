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

from engine.gui_grids import GenericTable

class ReportBotFrame(wx.Frame):
    """Whatsapp GUI Frame"""
    def __init__(self,  parent, title = None, logger = None):
        self.title = title or "Posta publishing Bot"
        wx.Frame.__init__(self, parent, -1, self.title, size=(700,400))

        self.logger = logger or logging.getLogger(__name__)

        self.db = Db(self.logger)
        tables = self.db.fetch_tables()
        summary_statistics = self.db.fetch_table_statistics()

        self.createPanel(tables, summary_statistics)


        #--------------------------------
        

    def createPanel(self, table, summary_statistics):
        self.mainPanel = ReportPanel(self, table, summary_statistics, self.logger)
        self.box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_sizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.SetSizer(self.box_sizer)



    def OnCloseWindow(self, event):
        self.db.close_conn()
        self.Destroy()


class ReportPanel(wx.Panel):
    #----------------------------------------------------------------------
    def __init__(self, parent, tables, summary_statistics, logger = None):
        wx.Panel.__init__(self, parent)
        self.table_names = [x[0] for x in tables ]
        self.summary_statistics = summary_statistics
        self.wildcard = "Setting files (*.csv)|*.csv|All files (*.*)|*.*"

        # get a logger
        self.logger = logger or logging.getLogger(__name__) 
        self.posta = Posta()
        self.active_threads = []  


               
        self.layout()

    #---------------------------------------------------------
    def layout(self):
        # create main horizontal sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.top_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #self.bottom_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_left_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_right_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        #self.bottom_left_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        #self.bottom_right_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        #self.buttonSizer = wx.BoxSizer(wx.VERTICAL)
        self.reportSizer = wx.BoxSizer(wx.HORIZONTAL)

        

        # create combobox
        control_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.display_database_tables(control_panel_sizer)

        control_button_sizer = wx.BoxSizer(wx.VERTICAL)

        # create main controluttons
        btnData = [
            ("Begin Posting", self.beginPosting),
            ("Stop Posting",  self.stopPosting),
            ("Create Schedule", self.schedulePosts)]
        self.create_buttons(control_button_sizer, btnData, flag=wx.ALL|wx.CENTER)



        # Create grid
        self.grid_panel = wx.Panel(self)
        #self.scroll_grid = wx.ScrolledWindow(self, -1)
        #self.scroll_grid.SetScrollbars(1, 1, 600, 400)

        self.createGrid(self.grid_panel, data=None)
      

        #create grid buttons
        btnData = [
            ("Load Websites", self.loadWebsites),
            ("Save Settings",  self.saveSettings)]

        self.grid_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.create_buttons(self.grid_button_sizer, btnData)


        # create text area
        """
        self.logTxtField = wx.TextCtrl(self, -1, "", style=wx.TE_RICH|wx.TE_MULTILINE)
        self.reportTxtField = wx.TextCtrl(self, -1, "", style=wx.TE_RICH|wx.TE_MULTILINE)"""

        
        
        #--------------------------
        # Add sizers
        
        #self.buttonSizer.Add(control_button_sizer)


        self.reportSizer.Add(self.grid_panel)
        #self.reportSizer.SetMinSize((-1,250))

        self.top_left_vertical_sizer.Add(self.reportSizer, 0 , flag = wx.EXPAND)
        self.top_left_vertical_sizer.Add(self.grid_button_sizer, 0, flag = wx.EXPAND)

        self.top_right_vertical_sizer.Add(control_panel_sizer)
        self.top_right_vertical_sizer.Add(control_button_sizer)

        self.top_horizontal_sizer.Add(self.top_left_vertical_sizer, 3, flag = wx.EXPAND)
        self.top_horizontal_sizer.Add(self.top_right_vertical_sizer, 1, flag = wx.EXPAND)

        #-----
        """
        self.bottom_left_vertical_sizer.Add(self.reportTxtField, 1, wx.EXPAND | wx.ALL, 5)
        self.bottom_right_vertical_sizer.Add(self.logTxtField, 1, wx.EXPAND | wx.ALL, 5)
        
        self.bottom_horizontal_sizer.Add(self.bottom_left_vertical_sizer,1,flag = wx.EXPAND | wx.ALL)
        self.bottom_horizontal_sizer.Add(self.bottom_right_vertical_sizer ,2,flag = wx.EXPAND | wx.ALL)"""




        self.mainSizer.Add(self.top_horizontal_sizer, 1, flag = wx.EXPAND | wx.ALL)
        #self.mainSizer.Add(self.bottom_horizontal_sizer, 2, flag = wx.EXPAND | wx.ALL)
        

        self.SetAutoLayout(True)
        self.SetSizer(self.mainSizer)
        self.Layout()



    #-----------------------------------------------------
    def create_buttons(self, sizer, btnData, flag = None):

            
        for data in btnData:
            label, handler = data
            self.btnBuilder(label, sizer, handler, flag)

    
    # def display_database_tables
    def display_database_tables(self, sizer):
            self.databaseListBox = wx.CheckListBox(parent = self, id = -1, choices=self.table_names, style=wx.LB_MULTIPLE, name="databaseListBox")
            sizer.Add(self.databaseListBox, 1, wx.EXPAND)

           

    #-------------------------------------------------------------------
    def createGrid(self, grid, data = None):
        self.grid = wx.grid.Grid(grid)
        

        self.grid.ShowScrollbars(wx.SHOW_SB_NEVER,wx.SHOW_SB_DEFAULT)
      
        
        if data is None:
            data = self.summary_statistics
        colLabels = ("Database Name", "Published posts", "Unpublished posts", "Rejected posts(short content)", "Crawled Links", "Total Website Links") 
        self.data_table = GenericTable(data, colLabels = colLabels) 
        self.grid.SetTable(self.data_table, True)
        self.grid.AutoSize()
        #self.grid.AutoSizeColumns(setAsMin=True)
   
        

    
    
    
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

    #-------------------------------------------------------------------
    def beginPosting(self, evt):
        self.logger.debug(self.data_table.data)

        # launch threads 
        self.order_queue = Queue(maxsize = 100)
        self.quit_event = threading.Event()

        for site in self.data_table.data:

            single_setting = {}
            single_setting['site'] = site[0]
            single_setting['posts'] = site[1]
            # change table to list of tables
            # fetch from table combo box
            tables_choosen = self.fetch_tables()
            if len(tables_choosen) != 0:

                single_setting['table'] = tables_choosen
                single_setting['username'] = site[2]
                single_setting['password'] = site[3]

                if site[4] == "1":

                    self.logger.debug("Beginning posting process.....")
                    #self.posta.post_content(single_setting)
                    # launch threads
        
                    posta = threading.Thread(target= self.posta.post_threaded_content, args=(single_setting, self.order_queue, self.quit_event, self), daemon=True)
                    self.active_threads.append(posta)
                    posta.start()
            else:
                wx.MessageBox("You have not choosen any database to populate", "Error Publishing", wx.OK | wx.ICON_ERROR)
                # break out of the loop
                break

        
        # join threads
        """
        for t in self.active_threads:
            t.join()"""

        # retrieve queue
        results  = []
        while not self.order_queue.empty() or self.quit_event.isSet():
            results.appaend(self.order_queue.get())
            self.log_message_to_report_txt_field("----"*15)
        for result in results:
            for key, value in result.items():
                if key in ['Posts Published','Short Posts']:
                    msg = "{}: {}".format(key, len(value))
                else:
                    msg = "{}: {}".format(key, value)
                self.log_message_to_report_txt_field(msg)



                

    ####----------------------------------
    def fetch_tables(self):
        return self.databaseListBox.GetCheckedStrings()



    #-------------------------------------------------------------------
    def stopPosting(self, evt):
        self.log_message_to_report_txt_field("...."*15)
        self.log_message_to_report_txt_field("Stopping Bots....")
        self.log_message_to_report_txt_field("...."*15)
        self.quit_event.set()

    #-------------------------------------------------------------------
    def schedulePosts(self, evt):
        pass


    #-------------------------------------------------------------------
    def loadWebsites(self, evt):
        dlg = wx.FileDialog(self, "Import Bot Settings", os.getcwd(), style=wx.FD_OPEN, wildcard=self.wildcard)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPath()
            self.process_csv()
            dlg.Destroy()


    #---------------------------------------------------------------
    def process_csv(self):

        with open(self.filename) as csvfile:
            reader = csv.DictReader(csvfile)
            # tuple to hold data
            csv_data = list()

            colLabels = ("site", "posts",  "username", "password","crawl (Yes/No)", "Status")

            for row in reader:
                single_site = [row[colLabels[0]],row[colLabels[1]], row[colLabels[2]], row[colLabels[3]], "1", "Idle"]
                csv_data.append(single_site)
            #csv_data = tuple(csv_data)
            # assign a new table to the grid
            self.grid.ClearGrid()
            self.grid.ForceRefresh()
            #print(self.data_table.data)
            self.data_table.data = None
            #print(self.data_table.data)
            self.data_table.data = csv_data
            rows_affected = len(csv_data)

            msg = wx.grid.GridTableMessage(self.data_table,wx.grid.GRIDTABLE_NOTIFY_ROWS_INSERTED,1,  rows_affected)


            self.grid.GetTable().GetView().ProcessTableMessage(msg)

            self.grid.ForceRefresh()
            

            self.Layout()




    #-------------------------------------------------------------------
    def saveSettings(self, evt):
        pass


    #------------------------------------------------------------------
    def log_message_to_txt_field(self, msg):
        self.logTxtField.AppendText(msg)
        self.logTxtField.AppendText("\n")


    def log_message_to_report_txt_field(self, msg):
        self.reportTxtField.AppendText(msg)
        self.reportTxtField.AppendText("\n")



#-------------------------------------------------------------------
#-------------------------------------------------------------------
