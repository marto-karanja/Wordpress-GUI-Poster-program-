import os
import sys
from turtle import delay, title
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
from engine.db_remote_ssh import Db
from engine.posta import Posta
from engine.reports_gui import ReportBotFrame
from engine.category_post import CategoryPostFrame
from engine.gui.banned_strings_gui import BannedStringsFrame
#from engine.gui.bulk_settings_gui import BulkPostsFrame
from engine.models import BannedStrings, PublishedPosts, ProcessingPosts, Base
from engine.local_db import connect_to_db, create_threaded_session, remove_session, save_published_posts, save_short_posts,get_connection, create_session, fetch_published_posts, update_post, get_title_length, set_title_length, count_published_posts, delete_multiple_posts, fetch_short_posts, delete_multiple_short_posts, get_content_length, set_content_length, delete_all_tables, save_references_to_db

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session




from charts.CrawlingReportsFrame import CrawlingReportsFrame
from engine.gui_grids import GenericTable


engine = connect_to_db()

        # now all calls to Session() will create a thread-local session
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


class PostaPanel(wx.Panel):
    #----------------------------------------------------------------------
    def __init__(self, parent, tables_summary= None,db = None, logger = None):
        wx.Panel.__init__(self, parent)
        self.tables_summary= tables_summary
        self.wildcard = "Setting files (*.csv)|*.csv|All files (*.*)|*.*"

        # get a logger
        self.logger = logger or logging.getLogger(__name__)
        self.db = db
        session = Session()
        self.update_post_count = str(count_published_posts(session))
        session.close()
        self.logger.info(self.update_post_count)



        
        self.posta = Posta(logger = self.logger)
        self.active_threads = []

        self.engine = False

        self.connection = None


               
        self.layout()

    #---------------------------------------------------------
    def layout(self):
        # create main horizontal sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.top_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottom_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_left_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_right_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        self.bottom_left_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        self.bottom_right_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        #self.buttonSizer = wx.BoxSizer(wx.VERTICAL)
        self.reportSizer = wx.BoxSizer(wx.HORIZONTAL)

        

        # create combobox
        self.control_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.display_database_tables(self.control_panel_sizer)

        control_button_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Publish")
        update_button_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Reconcile Database")

        # add date sizer
        date_button_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Bot Settings")

        delay_label = wx.StaticText(self,-1,label="Delay in seconds")

        self.delay_settings = {
            "10 Seconds" : 10,
            "20 Seconds" : 20,
            "30 Seconds" : 30,
            "60 Seconds" : 60, 
            "2 Minutes" : 120,
            "3 Minutes" : 180,
            "4 Minutes" : 240,
            "5 Minutes" : 300,
            "10 Minutes" : 600,
            "15 minutes" : 900,
            "30 Minutes" : 450,

        }

        self.years = ["None","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]

        self.months = ["None,","January","February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

        delay_label = wx.StaticText(self,-1,label="Delay in seconds")
        self.delay_combo_box = wx.ComboBox(self,-1,value="3 Minutes", choices = list(self.delay_settings.keys()))

        delay_box_sizer = wx.BoxSizer(wx.VERTICAL)
        delay_box_sizer.Add(delay_label, flag=wx.ALIGN_CENTER, border=5)
        delay_box_sizer.Add(self.delay_combo_box, flag=wx.ALIGN_CENTER, border=5)

        date_label = wx.StaticText(self,-1,label="Publishing Year")
        self.date_combo_box = wx.ComboBox(self,-1,value="None", choices = self.years)

        date_box_sizer = wx.BoxSizer(wx.VERTICAL)
        date_box_sizer.Add(date_label, flag=wx.ALIGN_CENTER, border=5)
        date_box_sizer.Add(self.date_combo_box, flag=wx.ALIGN_CENTER, border=5)

        month_label = wx.StaticText(self,-1,label="Publishing Month")
        self.month_combo_box = wx.ComboBox(self,-1,value="None", choices = self.months)

        month_box_sizer = wx.BoxSizer(wx.VERTICAL)
        month_box_sizer.Add(month_label, flag=wx.ALIGN_CENTER, border=5)
        month_box_sizer.Add(self.month_combo_box, flag=wx.ALIGN_CENTER, border=5)

        #control_button_sizer.Add(delay_label, flag=wx.ALIGN_CENTER, border=5)
        date_button_sizer.Add(delay_box_sizer, flag=wx.ALIGN_CENTER | wx.ALL, border=5)


        date_button_sizer.Add(date_box_sizer, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        date_button_sizer.Add(month_box_sizer, flag=wx.ALIGN_CENTER | wx.ALL, border=5)

        self.abstract_checkbox = wx.CheckBox(self, -1, "Add Abstract while publishing", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name="checkBox")
        control_button_sizer.Add(self.abstract_checkbox, flag=wx.ALIGN_LEFT, border=5)
        
        
        self.updated_posts_label = wx.StaticText(self,-1, label= f"{self.update_post_count} posts need to be updated")
        update_button_sizer.Add(self.updated_posts_label, flag=wx.ALIGN_LEFT, border=5)
        
        btnData = [("Update Posts to remote Db", self.updatePostsDb)]
        self.create_buttons(update_button_sizer, btnData, flag=wx.ALL|wx.EXPAND)



        # create main controluttons
        btnData = [
            #("Post via XML-RPC", self.beginPosting),
            ("Publish Posts", self.beginRestPosting),
            ("Stop Posting",  self.stopPosting),
            ("Post By Category", self.postByCategory)]
        self.create_buttons(control_button_sizer, btnData, flag=wx.ALL|wx.EXPAND)
        
        



        # Create grid
        self.grid_panel = wx.Panel(self)
        #self.scroll_grid = wx.ScrolledWindow(self, -1)
        #self.scroll_grid.SetScrollbars(1, 1, 600, 400)

        self.createGrid(self.grid_panel, data=None)
      

        #create grid buttons
        btnData = [
            ("Load Websites", self.loadWebsites),
            ("Connect To Remote Database", self.connectRemoteDb),
            ("Set Title Length", self.OnSetTitleLength),
            ("Set Content Length", self.OnSetContentLength)]

        self.grid_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.create_buttons(self.grid_button_sizer, btnData, flag = wx.EXPAND|wx.ALL)


        # create text area
        self.logTxtField = wx.TextCtrl(self, -1, "", style=wx.TE_RICH|wx.TE_MULTILINE)
        self.reportTxtField = wx.TextCtrl(self, -1, "", style=wx.TE_RICH|wx.TE_MULTILINE)

        
        
        #--------------------------
        # Add sizers
        
        #self.buttonSizer.Add(control_button_sizer)


        self.reportSizer.Add(self.grid_panel)
        #self.reportSizer.SetMinSize((-1,250))

        self.top_left_vertical_sizer.Add(self.reportSizer, 0 , flag = wx.EXPAND)
        self.top_left_vertical_sizer.Add(self.grid_button_sizer, 0, flag = wx.EXPAND)

        

        
        self.top_right_vertical_sizer.Add(self.control_panel_sizer, 0 , flag = wx.EXPAND)
        
        self.top_right_vertical_sizer.Add(update_button_sizer, 0, flag = wx.EXPAND)
        self.top_right_vertical_sizer.Add(date_button_sizer, 0 , flag = wx.EXPAND)
        
        self.top_right_vertical_sizer.Add(control_button_sizer, 0 , flag = wx.EXPAND)
        
        

        self.top_horizontal_sizer.Add(self.top_left_vertical_sizer, 2, flag = wx.EXPAND)
        self.top_horizontal_sizer.Add(self.top_right_vertical_sizer, 1, flag = wx.EXPAND)

        #-----
        self.bottom_left_vertical_sizer.Add(self.reportTxtField, 1, wx.EXPAND | wx.ALL, 5)
        self.bottom_right_vertical_sizer.Add(self.logTxtField, 1, wx.EXPAND | wx.ALL, 5)
        
        self.bottom_horizontal_sizer.Add(self.bottom_left_vertical_sizer,2,flag = wx.EXPAND | wx.ALL)
        self.bottom_horizontal_sizer.Add(self.bottom_right_vertical_sizer ,3,flag = wx.EXPAND | wx.ALL)




        self.mainSizer.Add(self.top_horizontal_sizer, 1, flag = wx.EXPAND | wx.ALL)
        self.mainSizer.Add(self.bottom_horizontal_sizer, 2, flag = wx.EXPAND | wx.ALL)
        

        self.SetAutoLayout(True)
        
        self.SetSizer(self.mainSizer)
        self.Layout()

    def connectRemoteDb(self, evt):
        
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
        connection = {}
        connection["host"] = config["database"]["remote"]["host"]
        connection["database"] = config["database"]["remote"]["database"]
        connection["user"] = config["database"]["remote"]["user"]
        connection["password"] = config["database"]["remote"]["password"]


        # close existing db connection
        self.db.close_conn()
        self.connection = connection        
        self.db = Db(logger = self.logger, connection = connection)
        self.db.start_conn()
        self.tables_summary = self.db.fetch_tables_summary()
        self.databaseListBox.Destroy()
        self.databaseListBox = wx.CheckListBox(parent = self, id = -1, choices=list(self.tables_summary.keys()), style=wx.LB_MULTIPLE, name="databaseListBox")

        self.control_panel_sizer.Add(self.databaseListBox, 1, wx.EXPAND)

        
        #self.Hide()
        self.Refresh()
        self.Update()
        self.Layout()
        self.Fit()
        #self.Show()



    #-----------------------------------------------------
    def create_buttons(self, sizer, btnData, flag = None):

            
        for data in btnData:
            label, handler = data
            self.btnBuilder(label, sizer, handler, flag)

    
    # def display_database_tables
    def display_database_tables(self, sizer):
            self.databaseListBox = wx.CheckListBox(parent = self, id = -1, choices=list(self.tables_summary.keys()), style=wx.LB_MULTIPLE, name="databaseListBox")
            sizer.Add(self.databaseListBox, 1, wx.EXPAND)


    #-----------------------------------------------------------------
    def updatePostsDb(self, evt):
        self.log_message_to_report_txt_field("[Begining database update process]")
        update_thread = threading.Thread(target = self.update_db_thread)
        self.logger.info("Starting the update thread")
        update_thread.start()

    def update_db_thread(self):
        session = Session()
        db = Db()
        posts = True
        #offset = 0
        cursor = 1
        
        posts = []
        while posts is not False:
            results = {}
            #posts = fetch_published_posts(session, 800, offset)
            posts = fetch_published_posts(session, 800)
            self.logger.info("Updating posts attempt %s", cursor)
            #offset += 800
            cursor +=1
            processed_posts = []
            if posts is not False:
                for post in posts:
                    if not post[2] in results:
                        results[post[2]] = []
                    results[post[2]].append(post)
                for item in results.keys():
                    self.logger.info("%s : %s", item, len(results[item]))
                    self.log_message_to_txt_field("Updating database....")
                    if db.update_multiple_posts(results[item]):
                        self.log_message_to_txt_field("Updated Posts in online database: [{}]".format(len(results[item])))
                        if db.insert_multiple_posts(results[item]):
                            self.log_message_to_txt_field("Inserted Posts in online database: [{}]".format(len(results[item])))
                            for post in results[item]:
                                processed_posts.append(post[0])
                        else:
                            self.log_message_to_txt_field("Failed to Update Posts in online database: [{}]".format(len(results[item])))

                    else:
                        self.log_message_to_txt_field("Failed to Update Posts in online database: [{}]".format(len(results[item])))

                    if delete_multiple_posts(session, processed_posts):
                        self.logger.info("%s posts deleted in local db", len(processed_posts))
                        self.update_post_count = str(count_published_posts(session))
                        self.updated_posts_label.SetLabel(f"{self.update_post_count} posts need to be updated")
                        
                    else:
                        self.logger.error("Unable to update local db")
                    processed_posts = []
        
                # update local sqllite db
                ## to do change to delete post
                #self.logger.info(processed_posts)
                
            else:
                posts = False        # fetch ids where processed = false
        # insert into published

        # update short posts
        self.update_short_posts()

        # update shprt posts
        self.log_message_to_report_txt_field("[Completing database process]")
        self.log_message_to_report_txt_field("*****************************")
        self.log_message_to_report_txt_field("[All processes completed]")
        self.log_message_to_report_txt_field("*****************************")
        self.update_post_count = str(count_published_posts(session))
        self.updated_posts_label.SetLabel(f"{self.update_post_count} posts need to be updated")
        self.log_message_to_txt_field("Finished updating database process")
        self.log_message_to_txt_field("**********************************")
        self.log_message_to_txt_field("----------------------------------")


    def update_short_posts(self):
        session = Session()
        db = Db()
        short_posts = True
        cursor = 0       

        while short_posts is not False:
            results = {}
            short_posts = fetch_short_posts(session, 800)
            self.logger.info("Updating short posts attempt %s", cursor)
            #offset += 800
            cursor +=1
            processed_posts = []
            if short_posts is not False:
                for post in short_posts:
                    if not post[1] in results:
                        results[post[1]] = []
                    results[post[1]].append(post)
                for item in results.keys():
                    self.logger.info("%s : %s", item, len(results[item]))
                    self.log_message_to_txt_field("Updating database....")
                    if db.update_multiple_short_posts(results[item]):
                        self.log_message_to_txt_field("Updated short Posts in online database: [{}]".format(len(results[item])))
                        for post in results[item]:
                                processed_posts.append(post[0])

                    else:
                        self.log_message_to_txt_field("Failed to Update Posts in online database: [{}]".format(len(results[item])))

                    if delete_multiple_short_posts(session, processed_posts):
                        self.logger.info("%s posts deleted in local db", len(processed_posts))
                        
                        
                    else:
                        self.logger.error("Unable to update local db")
                    processed_posts = []
        
                # update local sqllite db
                ## to do change to delete post
                #self.logger.info(processed_posts)
                
            else:
                short_posts = False


                    


           

    #-------------------------------------------------------------------
    def createGrid(self, grid, data = None):
        self.grid = wx.grid.Grid(grid)
        

        self.grid.ShowScrollbars(wx.SHOW_SB_NEVER,wx.SHOW_SB_DEFAULT)
      
        
        if data is None:
            data = [["https://onlinetutorglobal.com/", "***********", "***********", "**********",  "********", "1" ],["********", "***********", "***********", "***********","***********", "" ], ["********", "***********", "***********", "***********","***********", "" ], ["********", "***********", "***********", "***********","***********", "" ], ["********", "***********", "***********", "***********","***********", "" ],["********", "***********", "***********", "***********","***********", "" ],["********", "***********", "***********", "***********","***********", "" ], ["********", "***********", "***********", "***********","***********", "" ], ["********", "***********", "***********", "***********","***********", "" ], ["********", "***********", "***********", "***********","***********", "" ], ["********", "***********", "***********", "***********","***********", "" ], ["********", "***********", "***********", "***********","***********", "" ], ["********", "***********", "***********", "***********","***********", "" ], ["********", "***********", "***********", "***********","***********", "" ]]
        colLabels = ("site", "posts", "username", "password", "Application Password", "Crawl (Yes/No)", "Status", ) 
        self.data_table = GenericTable(data, colLabels = colLabels) 
        self.grid.SetTable(self.data_table, True)
        self.grid.SetColFormatBool(5)
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

                single_setting['table'] = [self.tables_summary[x] for x in tables_choosen]
                single_setting['username'] = site[2]
                single_setting['password'] = site[3]
                single_setting['application_password'] = site[4]

                if site[5] == "1":

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



    def get_publishing_date(self):
        """Returns publishing date choosen by user"""
        month = self.month_combo_box.GetSelection()
        if month == -1:
            month = None
        else:
            month = self.months[int(month)]
        year = self.date_combo_box.GetSelection()
        if year == -1:
            year = None
        else:
            year = self.years[int(year)]
        return (month, year)

#--------------------------------------------------------------
    def fetch_engine(self):
        return connect_to_db()

    #-------------------------------------------------------------
    def OnSetTitleLength(self, evt):
        # get title length
        session = Session()
        title_length = get_title_length(session)
        
            

        message = "Set title length. current length {}".format(title_length)
        title_length = wx.GetTextFromUser(message, caption="Input text", default_value="", parent=None)

        if title_length != "":
            try:
                title_length = int(title_length)

            except:
                wx.MessageBox("Input needs to be a number", "Success", wx.OK | wx.ICON_ERROR)

            else:
                try:
                    set_title_length(session, title_length)
                except Exception as e:
                    self.logger.error("Unable to add string to database [%s]", title_length, exc_info=1)
                else:
                    wx.MessageBox("Successfully saved to database", "Success", wx.OK | wx.ICON_INFORMATION)
                
        # close session
        session.close()

    #-------------------------------------------------------------
    def OnSetContentLength(self, evt):
        # get title length
        session = Session()
        content_length = get_content_length(session)
        
            

        message = "Set content length. Current length {}".format(content_length)
        content_length = wx.GetTextFromUser(message, caption="Input text", default_value="", parent=None)

        if content_length != "":
            try:
                content_length = int(content_length)

            except:
                wx.MessageBox("Input needs to be a number", "Success", wx.OK | wx.ICON_ERROR)

            else:
                try:
                    set_content_length(session, content_length)
                except Exception as e:
                    self.logger.error("Unable to add string to database [%s]", content_length, exc_info=1)
                else:
                    wx.MessageBox("Successfully saved to database", "Success", wx.OK | wx.ICON_INFORMATION)
                
        # close session
        session.close()


#-------------------------------------------------------------------
    def beginRestPosting(self, evt):
        
         #launch thread 
        launch_thread = threading.Thread(target = self.launch_child_threads)
        self.logger.info("Launching the launcher thread")
        launch_thread.start()
    
    def launch_child_threads(self):

        delay = self.delay_combo_box.GetSelection()
        if delay == -1:
            delay = self.delay_settings["2 Minutes"]
        else:
            delay = self.delay_settings[self.delay_combo_box.GetString(delay)]

        publishing_date = self.get_publishing_date()
            
        

        self.logger.debug(self.data_table.data)

        # launch threads 
        self.order_queue = Queue(maxsize = 500)
        self.quit_event = threading.Event()

        self.db.start_conn()

        offset = 0

        content_length = int(get_content_length(Session()))



        # remove database object from loop
        for site in self.data_table.data:

            single_setting = {}
            single_setting['site'] = site[0]
            single_setting['posts'] = site[1]
            # change table to list of tables

            # fetch from table combo box
            tables_choosen = self.fetch_tables()
            # fetch bot delay combo box


            
            
            if len(tables_choosen) != 0:

                single_setting['table'] = [self.tables_summary[x] for x in tables_choosen]
                single_setting['username'] = site[2]
                single_setting['password'] = site[3]
                single_setting['application_password'] = site[4]

                if site[5] == "1":            
                    # fetch posts

                    # thread to launch main thread
                    # abstract
                    # upload database count

                    posts = self.db.fetch_posts_from_tables( no_of_posts = single_setting['posts'], offset= offset, tables = single_setting['table'], content_length = content_length )
                    #update offset value 
                    offset = offset + int(single_setting['posts'])

                    self.logger.debug("Beginning posting process.....")
                    # launch threads
                                        
                    self.log_message_to_report_txt_field(f"Fetching {len(posts)} from database")
        
                    posta = threading.Thread(target= self.posta.post_content_rest_method, args=(self.connection, Session, publishing_date, delay, posts, single_setting, self.order_queue, self.quit_event, self), daemon=True)
                    self.active_threads.append(posta)
                    posta.start()
            else:
                wx.MessageBox("You have not choosen any database to populate", "Error Publishing", wx.OK | wx.ICON_ERROR)
                # break out of the loop
                break

        self.db.close_conn()

        #add summary thread
        final_thread = threading.Thread(target = self.wait_for_thread_completion, args=(self.order_queue, self.quit_event, self.db, self.active_threads))
        self.logger.info("Starting the summary thread")
        final_thread.start()
        

    def wait_for_thread_completion(self, thread_queue, event, db, active_threads):
        # retrieve queue
        self.logger.info("Waiting for all threads to complete")

        for t in self.active_threads:
            t.join()
        results  = []
        while not thread_queue.empty() or event.isSet():
            self.logger.info("Waiting for queue input")
            results.append(self.order_queue.get())
            time.sleep(5)
            
        self.log_message_to_report_txt_field("----"*15)
        print("All threads have completed running")
        self.log_message_to_report_txt_field("All threads have completed running")
        self.log_message_to_report_txt_field("==================================")
        for result in results:
            for key, value in result.items():
                if key in ['Posts Published','Short Posts']:
                    msg = "{}: {}".format(key, len(value))
                else:
                    msg = "{}: {}".format(key, value)
                self.log_message_to_report_txt_field(msg)


        ### update database connection
        """
        # open sqllite
        self.log_message_to_report_txt_field("[Updating database records]")
        session = Session()
        posts = True
        offset = 0
        cursor = 1
        db.start_conn()
        while posts is not False:
            posts = fetch_published_posts(session, 1000, offset)
            self.logger.info("Updating posts attempt %s", cursor)
            offset += 1000
            cursor +=1
            
            if posts is not False:
                for post in posts:
                    # update published tables and processed posts
                    if db.update_db_posts(post):
                        self.log_message_to_txt_field("Updated Post in online database. Link No: [{}]".format(post[0]))
                    else:
                        self.log_message_to_txt_field("Failed to Updated Post in online database [{}]".format(post[0]))
                    # update local sqllite db
                    ## to do change to delete post
                    delete_post(session, post[0])
        # fetch ids where processed = false
        # insert into published
        # update shprt posts
        self.log_message_to_report_txt_field("[Completing database process]")
        self.log_message_to_report_txt_field("*****************************")
        self.log_message_to_report_txt_field("[All processes completed]")
        self.log_message_to_report_txt_field("*****************************")
        self.log_message_to_txt_field("Finished updating database process")
        self.update_post_count = str(count_published_posts(session))
        self.updated_posts_label.SetLabel(f"{self.update_post_count} posts need to be updated")
        db.close_conn()
        Session.remove()"""
        self.log_message_to_report_txt_field("[Begining database update process]")
        update_thread = threading.Thread(target = self.update_db_thread)
        self.logger.info("Starting the update thread")
        update_thread.start()
        return
        

#-------------------------------------------------------------------
    def beginCategoryRestPosting(self, evt, categories):

        launch_thread = threading.Thread(target = self.launch_child_category_threads, args=(categories,))
        self.logger.info("Launching the launcher thread")
        launch_thread.start()


    def launch_child_category_threads(self, categories):
        self.logger.info("Child thread categories")
        self.logger.info(categories)
        
        delay = self.delay_combo_box.GetSelection()
        if delay == -1:
            delay = self.delay_settings["2 Minutes"]
        else:
            delay = self.delay_settings[self.delay_combo_box.GetString(delay)]
        
        

        self.logger.debug(self.data_table.data)
        publishing_date = self.get_publishing_date()

        # launch threads 
        self.order_queue = Queue(maxsize = 500)
        self.quit_event = threading.Event()
        
        self.db.start_conn()

        offset = 0

        content_length = int(get_content_length(Session()))

        for site in self.data_table.data:

            single_setting = {}
            single_setting['site'] = site[0]
            single_setting['posts'] = site[1]
            # change table to list of tables

            # fetch from table combo box
            tables_choosen = self.fetch_tables()
            # fetch bot delay combo box
            
            

            posts = self.db.fetch_category_posts_from_tables( no_of_posts = single_setting['posts'], offset=offset, table_names = categories, content_length = content_length )

            #update offset value 
            offset = offset + int(single_setting['posts'])

            if len(tables_choosen) != 0:

                single_setting['table'] = [self.tables_summary[x] for x in tables_choosen]
                single_setting['username'] = site[2]
                single_setting['password'] = site[3]
                single_setting['application_password'] = site[4]

                if site[5] == "1":

                    self.logger.debug("Beginning posting process.....")
                    

                    # launch threads
        
                    posta = threading.Thread(target= self.posta.post_category_rest_method, args=(self.connection, Session, publishing_date, delay, posts, single_setting, self.order_queue, self.quit_event, self, categories), daemon=True)
                    self.active_threads.append(posta)
                    posta.start()
            else:
                wx.MessageBox("You have not choosen any database to populate", "Error Publishing", wx.OK | wx.ICON_ERROR)
                # break out of the loop
                break

        self.db.close_conn()
         #add summary thread
        final_thread = threading.Thread(target = self.wait_for_thread_completion, args=(self.order_queue, self.quit_event, self.db, self.active_threads))
        self.logger.info("Starting the summary thread")
        final_thread.start()

                

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
    def postByCategory(self, evt):
        tables_choosen = self.fetch_tables()
        # check if tables are selected
        if len(tables_choosen) != 0:
            # get table names
            tables_choosen = self.fetch_tables()
            table_names = [self.tables_summary[x] for x in tables_choosen]
            print(table_names)

            # launch categories panel
            frame = CategoryPostFrame(self, table_names, self.db)
            frame.SetWindowStyle(style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
            frame.Show(True)

        else:
            wx.MessageBox("You have not choosen any database.", "Error Publishing", wx.OK | wx.ICON_ERROR)
            
            


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

            colLabels = ("site", "posts",  "username", "password", "Application password","crawl (Yes/No)")

            for row in reader:
                single_site = [row[colLabels[0]],row[colLabels[1]], row[colLabels[2]], row[colLabels[3]], row["application_password"], "1"]
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



class PostaBotFrame(wx.Frame):
    """Whatsapp GUI Frame"""
    def __init__(self, parent, logger = None):
        self.title = "Posta publishing Bot"
        wx.Frame.__init__(self, parent, -1, self.title)
        self.setup_local_db()
        self.parent = parent
        
        self.createMenuBar()

        self.logger = logger or logging.getLogger(__name__)

        self.db = Db(self.logger)
        self.db.start_conn()
        tables_summary = self.db.fetch_tables_summary()
        # include available posts

        self.createPanel(tables_summary)


        #--------------------------------
        self.icons_dir = wx.GetApp().GetIconsDir()

        
        frameIcon = wx.Icon(os.path.join(self.icons_dir, "posta.ico"),   type=wx.BITMAP_TYPE_ICO)
        self.SetIcon(frameIcon)
        self.Center(wx.BOTH)

    def setup_local_db(self):
        database_url = "{}\{}".format(os.getcwd(), "settings.db")
        try:        
            # GET THE CONNECTION OBJECT (ENGINE) FOR THE DATABASE
            self.engine = get_connection(f"sqlite:///{database_url}")
        except Exception as ex:
            print("Connection could not be made due to the following error: \n", ex)
        else:
            print("Connection created successfully.")
        Base.metadata.create_all(self.engine)


    def createPanel(self, table):
        self.mainPanel = PostaPanel(self, tables_summary =table, db = self.db, logger = self.logger)
        self.box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_sizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.box_sizer.SetSizeHints(self)
        self.SetSizer(self.box_sizer)


    def menuData(self):
        return [("&File", (

                    ("About...", "Show about window", self.OnAbout),
                    ("Manage Banned Strings", "Create/Delete Banned Strings", self.OnManageBanned),
                    ("Upload References", "Add References", self.UploadReferences),                    
                    ("&Quit", "Quit", self.OnCloseWindow))
                ),
                ("&Bulk Options",(
                    ("Export Settings", "Export Database", self.OnExport),
                    ("Import Settings", "Import Database", self.OnImport),
                )),
                ("&Reports",(
                    ("View Posting Reports", "Show posts reports", self.OnPostReports),
                    ("View Crawling Reports", "Show crawling reports", self.OnCrawlReports),
                    ("Table Summary", "Show crawling reports", self.OnTableSummary)
                ))]

    def createMenuBar(self):
        menuBar = wx.MenuBar()
        for eachMenuData in self.menuData():
            menuLabel = eachMenuData[0]
            menuItems = eachMenuData[1]
            menuBar.Append(self.createMenu(menuItems), menuLabel)
        self.SetMenuBar(menuBar)

    def createMenu(self, menuData):
        menu = wx.Menu()
        for eachItem in menuData:
            if len(eachItem) == 2:
                label = eachItem[0]
                subMenu = self.createMenu(eachItem[1])
                menu.AppendMenu(wx.NewId(), label, subMenu)
            else:
                self.createMenuItem(menu, *eachItem)
        return menu

    def createMenuItem(self, menu, label, status, handler, kind=wx.ITEM_NORMAL):
        if not label:
            menu.AppendSeparator()
            return
        menuItem = menu.Append(-1, label, status, kind)
        self.Bind(wx.EVT_MENU, handler, menuItem)

    def OnCloseWindow(self, event):
        if self.engine:
            self.engine.dispose()
        self.db.close_conn()
        self.Destroy()

    def OnAbout(self, event):
        dlg = PostaAbout(self)
        dlg.ShowModal()
        dlg.Destroy()

    def BulkPost(self, event):
        frame = BulkPostsFrame(parent=wx.GetTopLevelParent(self), title = "Publish posts in Bulk", logger = self.logger, db = self.db)
        frame.SetWindowStyle(style=wx.DEFAULT_FRAME_STYLE)
        frame.Show(True)
        #self.Hide()

    
    #-----------------------------------------------------------------------

    def OnCrawlReports(self, event):
        frame = CrawlingReportsFrame("Crawling reports", parent=wx.GetTopLevelParent(self))
        frame.SetWindowStyle(style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        frame.Show(True)

    def OnTableSummary(self, event):
        frame = ReportBotFrame(title = "Crawling reports", parent=wx.GetTopLevelParent(self), logger = self.logger)
        frame.SetWindowStyle(style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        frame.Show(True)


    #------------------------------------------------------------
    def OnManageBanned(self, event):
        frame = BannedStringsFrame(parent=wx.GetTopLevelParent(self), title = "Banned Strings")
        frame.SetWindowStyle(style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        frame.Show(True)




    # to do
    # launch banned strings frame
    # delete or create strings







    #----------------------------------------------------------



    def OnPostReports(self, event):
        pass



    #-------------------------------------------------------------------------


    def OnExport(self, event):
        dlg = wx.FileDialog(self, "Export Bot settings to", os.getcwd(), style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, wildcard=self.wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            if not os.path.splitext(filename)[1]:
                filename = filename + '.bot'
            self.filename = filename
            print(self.filename)
            self.export_database()
        dlg.Destroy()

    def export_database(self):
        import sqlite3
        con = sqlite3.connect('settings.db')
        with open(self.filename, 'w', encoding="utf-8") as f:
            for line in con.iterdump():
                f.write('%s\n' % line)
        wx.MessageBox("The export has been completed successfully.", caption="Export was successful", style=wx.OK | wx.ICON_INFORMATION)



    wildcard = "Database files (*.bot)|*.bot|All files (*.*)|*.*"
    def OnImport(self, event):
        dlg = wx.FileDialog(self, "Import Bot Settings", os.getcwd(), style=wx.FD_OPEN, wildcard=self.wildcard)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPath()
            self.import_database()
            dlg.Destroy()

    def import_database(self):
        retCode = wx.MessageBox("Are you sure? This action is irreversible and will erase your current settings", caption="Confirm Import", style=wx.YES_NO | wx.ICON_INFORMATION)
        if (retCode == wx.YES):
            import sqlite3
            
            con = sqlite3.connect('settings.db')
            delete_all_tables(con)
            # delete all tables in the db
            f = open(self.filename,'r', encoding="utf-8")
            str = f.read()
            con.executescript(str)
            wx.MessageBox("The import has been completed successfully.",caption="Successful import", style=wx.OK| wx.ICON_INFORMATION)
            
            return

    
    def UploadReferences(self, event):
        wildcard = "Database files (*.csv)|*.csv|All files (*.*)|*.*"
        dlg = wx.FileDialog(self, "Upload References", os.getcwd(), style=wx.FD_OPEN, wildcard=wildcard)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.references_filename = dlg.GetPath()
            self.import_references()
            dlg.Destroy()

    def import_references(self):
        with open(self.references_filename, 'r') as file:
            csvreader = csv.reader(file)
            references = []
            for row in csvreader:
                print(row[0])
                references.append(row[0])
        if save_references_to_db(self.engine, references):
            wx.MessageBox("References saved successfully", "Success", wx.ICON_INFORMATION)
        else:
            wx.MessageBox("Saving operation failed", "ERROR", wx.ICON_ERROR)


    








    


#---------------------------------------------------------------------

class PostaAbout(wx.Dialog):
    text = '''
<html>
<body bgcolor="#ACAA60">
<center><table bgcolor="#455481" width="100%" cellspacing="0"
cellpadding="0" border="1">
<tr>
    <td align="center"><h1>Posta Posting Bot</h1></td>
</tr>
</table>
</center>
<p><b>Posta Bot</b> is a an automated blog poster for the <b>Wordpress Blogging platform
</p>
<p><b>Whatsapp Bot</b> is brought to you by
<b>Martin Karanja</b> and <b>Kushmart Technologies Limited</b>, Copyright
&copy; 2021-2022.</p>
</body>
</html>
'''

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About Posta Wordpress Posting Framework',
                          size=(440, 400) )

        html = wx.html.HtmlWindow(self)
        html.SetPage(self.text)
        button = wx.Button(self, wx.ID_OK, "Okay")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(button, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()