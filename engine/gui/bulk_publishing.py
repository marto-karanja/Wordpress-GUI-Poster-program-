import os
import sys
import wx
import csv
import random
import string
import wx.adv
import wx.html
import wx.lib.inspection
import queue
import logging
import threading
import time
import datetime
from datetime import datetime, timedelta
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from engine.cleaner import Cleaner
from queue import Queue
from datetime import date
from sys import maxsize
from engine.db_remote_ssh import Db as questions_db
from engine.models import BannedStrings, PublishedPosts, ProcessingPosts, Base
from engine.local_db import connect_to_db, create_threaded_session, remove_session, save_published_posts, save_short_posts,get_connection, create_session, fetch_published_posts, update_post, get_title_length, set_title_length, count_published_posts, delete_multiple_posts, fetch_short_posts, delete_multiple_short_posts, get_content_length, set_content_length, delete_all_tables, save_references_to_db





from engine.local_db import connect_to_db, create_session, get_banned_strings, add_banned_string, delete_banned_string, save_website_records, get_website_records, fetch_connection_details

SENTINEL = object()

from engine.db_remote import Db

class BulkPublishingFrame(wx.Frame):
    """Whatsapp GUI Frame"""
    def __init__(self, parent, title = None, panel = None,logger = None, tables_summary = None, website_records= None, db = None):
        self.title = title
        
        wx.Frame.__init__(self, parent, -1, self.title)
        self.parent  = parent

        self.window = panel

        self.logger = logger or logging.getLogger(__name__)

        self.filename = ""

        self.db = questions_db(self.logger)
        self.db.start_conn()

        tables_summary = self.db.fetch_total_tables_summary()

        self.db.close_conn()

        


        self.createPanel(tables_summary, website_records, self.db)


        #--------------------------------
    def createPanel(self, tables_summary, website_records, db):
        self.mainPanel = BulkPublishingPanel(self, logger = self.logger, tables_summary = tables_summary, website_records = website_records, db = db)
        self.box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_sizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.box_sizer.SetSizeHints(self)
        self.SetSizer(self.box_sizer)
        self.Layout()


    

    def OnCloseWindow(self, event):
        self.Destroy()






###------------------------------------------------------------------
class BulkPublishingPanel(wx.Panel):
    def __init__(self, parent, tables_summary = None, logger = None, website_records = None, db = None):
        self.tables_summary = tables_summary
        wx.Panel.__init__(self, parent)

        self.parent = parent

        self.database_breakdown_showing = False
        self.database_choosen = None
        
        # get a logger
        self.logger = logger or logging.getLogger(__name__) 

        self.website_records = website_records
        self.db = db
        
        self.logger.info(f"Preparing {self.website_records} for production run ")

        self.cleaner = Cleaner()

        self.delay = 5

        self.threads_per_batch = 10

        self.question_load = 700

        self.order_queue = Queue()
        self.quit_event = threading.Event()  

                      
        self.layout()

    #---------------------------------------------------------
    def layout(self):

        # create main horizontal sizer
        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        control_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

       
        # create combo box
        self.display_database_tables()

        batch_size_lbl = wx.StaticText(self, -1, "Batch Size")
        self.offset_combo_box = wx.ComboBox(self,-1,value="None", choices = ['100','1000','10000', '100000','200000','300000','500000'])
        self.offset_combo_box.SetValue('200000')

        content_size_lbl = wx.StaticText(self, -1, "Min content size:")
        self.content_length_combo_box = wx.ComboBox(self,-1,value="None", choices = ['100','80','75','60','50', '40','30','20'])
        self.content_length_combo_box.SetValue('75')

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(batch_size_lbl, border = 5)
        sizer1.Add(self.offset_combo_box, border = 5, flag= wx.ALL)

        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer2.Add(content_size_lbl)
        sizer2.Add(self.content_length_combo_box,border = 5, flag= wx.ALL)


        control_button_sizer.Add(sizer1)
        control_button_sizer.Add(sizer2)

        sizer3 = wx.BoxSizer(wx.HORIZONTAL)

        # create main control buttons
        btnData = [
            ("View DataBase Breakdown", self.viewDatabaseDetails)
            ]
        self.create_buttons(sizer3, btnData, flag=wx.ALIGN_CENTER_VERTICAL)

        control_button_sizer.Add(sizer3, flag = wx.EXPAND)


        self.combo_sizer.Add(control_button_sizer, 0)

        # create form sizer
        form_button_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Set Settings for production batch")

        questions_lbl = wx.StaticText(self, -1, "No Of Questions to post:")
        self.questions_value = wx.TextCtrl(self, -1, "")

        random_prefix_lbl = wx.StaticText(self, -1, "Add a random string to end of url:")
        self.random_prefix_value = wx.CheckBox(self, -1, label ="e.g https://xxx.com/new-post-233dffsfe345/", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name="checkBox")
        
        include_abstract_lbl = wx.StaticText(self, -1, "Add excerpt to body:")
        self.include_abstract_value = wx.CheckBox(self, -1, "Add Abstract while publishing", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name="checkBox")

        abstract_value_lbl = wx.StaticText(self, -1, "Abstract Length")
        self.abstract_value = wx.TextCtrl(self, -1, "45")

        include_category_lbl = wx.StaticText(self, -1, "Publish post category")
        self.include_category_value = wx.CheckBox(self, -1, "Add category to question body", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name="checkBox")

        include_references_lbl = wx.StaticText(self, -1, "Add references list to post body")
        self.include_references_value = wx.CheckBox(self, -1, "", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name="checkBox")

        title_prefix_lbl = wx.StaticText(self, -1, "Add Prefix to Title:")
        self.title_prefix_value = wx.TextCtrl(self, -1, "")

        title_postfix_lbl = wx.StaticText(self, -1, "Add Postfix to title:")
        self.title_postfix_value = wx.TextCtrl(self, -1, "")

        randomize_title_lbl = wx.StaticText(self, -1, "Choose Title From body content:")
        #self.choicesList = {'1st Sentence':1, '2nd Sentence':2, '3rd Sentence':3, '4th Sentence':4, '5th sentence':5, '6th Sentence':6,'7th Sentence':7, '8th Sentence':8, '9th Sentence':9, '10th Sentence':10, '1st Quarter':0.25, '2nd Quarter':0.5, '3rd Quarter':0.75, '4th Quarter':0, 'Randomize':-1}
        self.choicesList = {'1st Sentence':1, '2nd Sentence':2, '3rd Sentence':3, '4th Sentence':4, '5th sentence':5, '6th Sentence':6,'7th Sentence':7, '8th Sentence':8, '9th Sentence':9, '10th Sentence':10, '1st Quarter':0.25, '2nd Quarter':0.5, '3rd Quarter':0.75, '4th Quarter':0}
        self.randomize_title_value = wx.Choice(self, -1, choices=list(self.choicesList.keys()))
        self.randomize_title_value.SetSelection(1)

        title_length_lbl = wx.StaticText(self, -1, "Set the Title Length(Words):")
        self.title_length_value = wx.TextCtrl(self, -1, "15")
        
        body_length_lbl = wx.StaticText(self, -1, "Set Minimum Body Length (Words):")
        self.body_length_value = wx.TextCtrl(self, -1, "75")


        formSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        formSizer.AddGrowableCol(1)

        formSizer.Add(questions_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.questions_value, 0, wx.EXPAND)
        formSizer.Add(random_prefix_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.random_prefix_value, 0, wx.EXPAND)
        
        formSizer.Add(include_abstract_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.include_abstract_value, 0, wx.EXPAND)

        formSizer.Add(abstract_value_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.abstract_value, 0, wx.EXPAND)

        formSizer.Add(include_category_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.include_category_value, 0, wx.EXPAND)

        formSizer.Add(include_references_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.include_references_value, 0, wx.EXPAND)

        formSizer.Add(title_prefix_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.title_prefix_value, 0, wx.EXPAND)
        formSizer.Add(title_postfix_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.title_postfix_value, 0, wx.EXPAND)
        formSizer.Add(randomize_title_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.randomize_title_value, 0, wx.EXPAND)
        formSizer.Add(title_length_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.title_length_value, 0, wx.EXPAND)
        formSizer.Add(body_length_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.body_length_value, 0, wx.EXPAND)


        btnData = [
                    ("Begin Publishing",  self.beginPublishing),
                    ("Clear Form",  self.clearForm)]
        self.create_buttons(formSizer, btnData, flag=wx.ALL)

        # add date settins
        form_button_sizer.Add(self.add_date_controls(), 0, wx.EXPAND)


        form_button_sizer.Add(formSizer, 0 , wx.EXPAND|wx.TOP|wx.BOTTOM,5)

        

        # Add form sizer to main sizer
        self.mainSizer.Add(form_button_sizer, 0)

        #self.SetAutoLayout(True)
        self.mainSizer.SetSizeHints(self)
        self.SetSizer(self.mainSizer)
        self.Layout()

    def add_date_controls(self):
        date_button_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Bot Settings")
        self.start_date_calendar_control = wx.adv.CalendarCtrl(self, id=-1, date=wx.DateTime.Now(), style= wx.adv.CAL_SHOW_HOLIDAYS)

        start_date_box_sizer = wx.BoxSizer(wx.VERTICAL)
        date_label = wx.StaticText(self,-1,label="Start Date")
        start_date_box_sizer.Add(date_label, flag=wx.ALIGN_CENTER, border=5)
        start_date_box_sizer.Add(self.start_date_calendar_control, flag=wx.ALIGN_CENTER, border=5)

        self.end_date_calendar_control = wx.adv.CalendarCtrl(self, id=-1, date=wx.DateTime.Now(), style= wx.adv.CAL_SHOW_HOLIDAYS)

        end_date_box_sizer = wx.BoxSizer(wx.VERTICAL)
        date_label = wx.StaticText(self,-1,label="End Date")
        end_date_box_sizer.Add(date_label, flag=wx.ALIGN_CENTER, border=5)
        end_date_box_sizer.Add(self.end_date_calendar_control, flag=wx.ALIGN_CENTER, border=5)



        self.years = ["None","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022", "2023", "2024", "2025","2026"]

        self.months = ["None,","January","February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

        self.days = [*range(0,31)]
        self.days = [str(x) for x in self.days] 

        #day_label = wx.StaticText(self,-1,label="Publishing Day")
        #self.day_combo_box = wx.ComboBox(self,-1,value="None", choices = self.days)

        """

        day_box_sizer = wx.BoxSizer(wx.VERTICAL)
        day_box_sizer.Add(day_label, flag=wx.ALIGN_CENTER, border=5)
        day_box_sizer.Add(self.day_combo_box, flag=wx.ALIGN_CENTER, border=5)"""


        """
        date_label = wx.StaticText(self,-1,label="Publishing Year")
        self.date_combo_box = wx.ComboBox(self,-1,value="None", choices = self.years)

        date_box_sizer = wx.BoxSizer(wx.VERTICAL)
        date_box_sizer.Add(date_label, flag=wx.ALIGN_CENTER, border=5)
        date_box_sizer.Add(self.date_combo_box, flag=wx.ALIGN_CENTER, border=5)

        month_label = wx.StaticText(self,-1,label="Publishing Month")
        self.month_combo_box = wx.ComboBox(self,-1,value="None", choices = self.months)

        month_box_sizer = wx.BoxSizer(wx.VERTICAL)
        month_box_sizer.Add(month_label, flag=wx.ALIGN_CENTER, border=5)
        month_box_sizer.Add(self.month_combo_box, flag=wx.ALIGN_CENTER, border=5)"""

        #control_button_sizer.Add(delay_label, flag=wx.ALIGN_CENTER, border=5)


        #date_button_sizer.Add(day_box_sizer,1, flag = wx.EXPAND)
        date_button_sizer.Add(start_date_box_sizer,1, flag= wx.EXPAND)
        date_button_sizer.Add(end_date_box_sizer,1, flag = wx.EXPAND)

        return date_button_sizer

    def viewDatabaseDetails(self, evt):
        if self.database_breakdown_showing:
            self.refresh_display()
            self.database_choosen = None
            self.database_breakdown_showing = False
        else:

            tables_choosen = self.databaseListComboBox.GetCheckedStrings()
            if len(tables_choosen) > 0:

                table_name = self.tables_summary[tables_choosen[0]]

                batch_size = int(self.offset_combo_box.GetValue())
                

                content_length = int(self.content_length_combo_box.GetValue())
                self.body_length_value.SetValue(str(content_length))


                self.db.start_conn()
                available_posts = self.db.fetch_available_posts(table_name, content_length)
                self.db.close_conn()
                remainder_posts = available_posts[0]['count'] % batch_size

                choices = {}

                counter = 0
                
                for batch in range(int(available_posts[0]['count']/batch_size)):
                    choices[f"Batch -{batch + 1} - [{batch_size}] posts available"] = str(batch)
                    counter = counter + batch_size

                if remainder_posts > 0:
                    choices[f"Batch {len(choices)+1} -[{remainder_posts}] posts available"] =  str(len(choices))

                if len(choices) > 0:
                    self.display_database_breakdown(choices)
                    self.database_breakdown_showing = True
                    self.database_choosen = {}
                    self.table_name_choosen = (table_name, batch_size)
                    self.database_choosen[table_name] = choices
                else:
                    wx.MessageBox("Selected database has no posts", "Error", wx.ICON_ERROR)

                # generate new combo box


            else:
                wx.MessageBox("Choose one database", "Error!", wx.ICON_ERROR)

    def display_database_breakdown(self, database_breakdown):
        self.databaseListComboBox.Destroy()
        self.databaseListComboBox = wx.CheckListBox(parent = self, id = -1, choices = list(database_breakdown.keys()), style=wx.LB_SINGLE)

        self.combo_sizer.Add(self.databaseListComboBox, 1, wx.EXPAND|wx.ALL, 2)

            
            #self.Hide()
        self.Refresh()
        self.Update()
        self.Layout()
        self.Fit()

        


    def display_database_tables(self):
        self.databaseListComboBox = wx.CheckListBox(parent = self, id = -1, choices=list(self.tables_summary.keys()), style=wx.LB_MULTIPLE, name="databaseListBox")
        self.combo_sizer= wx.StaticBoxSizer(wx.VERTICAL, self, "Database Summary")
        self.combo_sizer.Add(self.databaseListComboBox, 1, wx.EXPAND, 2)
        self.mainSizer.Add(self.combo_sizer, 1, wx.EXPAND|wx.ALL, 2)




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

    

    #-----------------------------------------------------------
    def savePrivateKey(self, evt):
        
        dlg = wx.FileDialog(self, "Import Bot Settings", os.getcwd(), style=wx.FD_OPEN)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPath()
            self.savePrivateKeyFile()
            dlg.Destroy()

    def savePrivateKeyFile(self):
        if self.filename == "":
            return
        else:
            import shutil
            key_directory = os.getcwd()+"//keys"
            file_name = os.path.split(self.filename)[-1]
            file_exts = os.path.splitext(file_name)
            
            if file_exts[1] != "":
                self.certificate_path_lbl.SetLabelText("Error! [Wrong file type]")
                return
            else:
                key_file_name = key_directory + "//" + file_name
                if os.path.isdir(key_directory):
                    shutil.copy(self.filename, key_file_name )
                else:
                    os.makedirs(key_directory)
                    shutil.copy(self.filename, key_file_name )
                if os.path.isfile (key_file_name):
                    self.certificate_path_lbl.SetLabelText("Success: [Security File Uploaded]")
                    self.filename = key_file_name
                else:
                    self.certificate_path_lbl.SetLabelText("Error! [Security File Not uploaded]")

        

    #------------------------------------------------------------
    def refresh_display(self):
            self.databaseListComboBox.Destroy()
            self.databaseListComboBox = wx.CheckListBox(parent = self, id = -1, choices = list(self.tables_summary.keys()), style=wx.LB_MULTIPLE)

            self.combo_sizer.Add(self.databaseListComboBox, 1, wx.EXPAND|wx.ALL, 2)

            
            #self.Hide()
            self.Refresh()
            self.Update()
            self.Layout()
            self.Fit()

    def beginPublishing(self, evt):

        self.start_date = datetime.strptime(self.start_date_calendar_control.GetDate().Format('%d/%m/%y %H:%M:%S'), '%d/%m/%y %H:%M:%S')
        self.end_date = datetime.strptime(self.end_date_calendar_control.GetDate().Format('%d/%m/%y %H:%M:%S'), '%d/%m/%y %H:%M:%S')

        print(self.get_publishing_time())


        # for website in selected websites
        settings = {}
        settings['questions'] = self.questions_value.GetValue()
        settings['random_prefix'] = self.random_prefix_value.GetValue()
        settings['include_excerpt'] = self.include_abstract_value.GetValue()
        settings['abstract_value'] = int(self.abstract_value.GetValue())
        settings['include_category'] = self.include_category_value.GetValue()
        settings['include_references'] = self.include_references_value.GetValue()
        settings['title_prefix'] = self.title_prefix_value.GetValue()
        settings['title_postfix'] = self.title_postfix_value.GetValue()
        settings['randomize_title'] = self.randomize_title_value.GetStringSelection()
        settings['title_length'] = int(self.title_length_value.GetValue())
        settings['body_length'] = int(self.body_length_value.GetValue())

        tables_choosen = self.databaseListComboBox.GetCheckedStrings()

        self.start_date = datetime.strptime(self.start_date_calendar_control.GetDate().Format('%d/%m/%y %H:%M:%S'), '%d/%m/%y %H:%M:%S')
        self.end_date = datetime.strptime(self.end_date_calendar_control.GetDate().Format('%d/%m/%y %H:%M:%S'), '%d/%m/%y %H:%M:%S')

        #print(self.get_publishing_time())

        
        if self.end_date < self.start_date:
            wx.MessageBox("Ensure that the end date is greater than today", "Error", wx.ICON_ERROR)
            return

        
          

        if settings['questions'] == "" or len(tables_choosen) == 0:
            wx.MessageBox("Ensure you have set a valid number of questions or you have choosen a database", "Error!", wx.ICON_ERROR)
        else:
            settings['questions'] = int(settings['questions'])
            self.logger.info(f"Begin publishing posts [{settings['questions']}]")

            if not self.database_choosen:
                launch_thread = threading.Thread(target = self.post_questions, args=(settings, tables_choosen))
            
                self.logger.info("Launching the launcher thread")
                launch_thread.start()

                self.parent.Hide()
            else:
                if settings['questions'] > self.table_name_choosen[1]:
                    wx.MessageBox("Questions have to be lesser than batch size. change question or batch size.", "Error", wx.ICON_ERROR)
                    return
                launch_thread = threading.Thread(target = self.post_question_from_single_table, args=(settings,))
            
                self.logger.info("Launching the launcher thread")
                launch_thread.start()

                self.parent.Hide()

    def post_question_from_single_table(self, settings):
        #get offset
        offset_choosen = self.databaseListComboBox.GetCheckedStrings()
        print (offset_choosen)

        table_name = self.table_name_choosen[0]
        batch_size = self.table_name_choosen[1]

        workload = []


        offset = int(self.database_choosen[table_name][offset_choosen[0]]) * batch_size
        self.logger.info("Initial offset {offset}")

        for website in self.website_records:

            self.display_user_settings(settings) 
            
            self.update_gui(f"Publishing to [{website}]")

            connection_details = fetch_connection_details(connect_to_db(), website)
            self.logger.info(f"Fetched connection details for {connection_details.website_name}")
            self.update_gui(f"Fetched connection details for {connection_details.website_name}")

            self.remote_database = Db(logger=self.logger, connection_details= connection_details)

            

            self.logger.info(f"Begin processing for: [{website}]")
            self.update_gui(f"Begin processing for: [{website}]")
            # get table names

            no_of_questions_per_db = settings['questions']

            self.logger.info(f"[{no_of_questions_per_db}] Posts fetched from each database")
            self.update_gui(f"[{no_of_questions_per_db}] Posts fetched from each database")

            questions_fetched = 0
            questions_remaining = no_of_questions_per_db
            
            while questions_remaining > 0:

                
                
                if questions_remaining > self.question_load:
                    limit = self.question_load
                else:
                    limit = questions_remaining


                thread = threading.Thread(target=self.process_posts_table_thread, args = (limit, offset, table_name, settings['body_length'], settings, website, self.quit_event, self.order_queue))
                workload.append(thread)

                offset = offset + limit

                questions_fetched = questions_fetched + limit
                self.logger.info(f"{questions_fetched} questions fetched in total")
                self.update_gui(f"{questions_fetched} prepared for processing")
                questions_remaining = questions_remaining - limit
                self.logger.info(f"{questions_remaining} questions remaining")
                self.update_gui(f"{questions_remaining} remaining")

            job_length = len(workload)

            self.logger.info(workload)

            

            
            num_batches = job_length // self.threads_per_batch

            with ThreadPoolExecutor(max_workers=self.threads_per_batch) as executor:
                remote_thread = False

                

                task_queue = queue.Queue()
                for i, t in enumerate(workload):
                    task_queue.put(t)

                futures = []
                batch_counter = 0
                while not task_queue.empty():
                    batch = []
                    for _ in range(min(task_queue.qsize(), self.threads_per_batch - len(futures))):
                        batch.append(task_queue.get())

                    self.update_gui(f"Running batch {batch_counter + 1}")
                    self.logger.info(f"Running batch {batch_counter + 1}")

                    for t in batch:
                        self.update_gui(f"Fetching questions for task {t.name}")                     
                        
                        futures.append(executor.submit(t.start))
                        self.update_gui(f"Pausing for {self.delay} seconds")
                        time.sleep(self.delay)

                    for future in concurrent.futures.as_completed(futures):
                        future.result()


                    futures.clear()
 

                    for i,t in enumerate(batch):
                        self.update_gui(f"Waiting for batch {[batch_counter]}: Thread no {i}-{t.name} to complete...")
                        self.logger.info(f"Waiting for batch {[batch_counter]}: Thread no {i}-{t.name} to complete...")
                        t.join()

                    if not remote_thread:
                        remote_db_thread = threading.Thread(target=self.insert_posts, args = (self.quit_event, self.order_queue, workload))
                        remote_db_thread.daemon = True # Set the thread as a daemon, if necessary
                        remote_db_thread.priority = 8
                        remote_db_thread.start()
                        remote_thread = True

                    

                    self.update_gui(f"Ending batch {batch_counter + 1}")
                    self.logger.info(f"Ending batch {batch_counter + 1}")
                    batch_counter = batch_counter + 1
                
                #self.quit_event.set()
                
            self.logger.info("Sending sentinel object....")
            self.update_gui("Finishing processing.....")
            self.order_queue.put(SENTINEL)
            return
            
            

        # get current position and calculate offset



    def update_gui(self, msg):
        wx.CallAfter(self.parent.window.log_message_to_txt_field,msg)

    def display_user_settings(self, settings):

        self.update_gui(f"****User settings****")

        self.update_gui(f"Start Date: [{self.start_date}]")
        self.update_gui(f"End Date: [{self.end_date}]")

        self.update_gui(f"No.of questions: [{settings['questions'] }]")
        self.update_gui(f"Include prefix to url: [{'Yes' if settings['random_prefix'] else 'No'}]")
        self.update_gui(f"Include excerpt [{'Yes' if settings['include_excerpt'] else 'No'}]")
        self.update_gui(f"Include abstract: [{'Yes' if settings['abstract_value'] else 'No'}]")
        self.update_gui(f"Include category: [{'Yes' if settings['include_category'] else 'No'}]")
        self.update_gui(f"Include references: [{'Yes' if settings['include_references'] else 'No'}]")
        self.update_gui(f"Title postfix set:[{'Yes' if settings['title_postfix'] else 'No'}]")
        self.update_gui(f"Title prefix set: [{'Yes' if settings['title_prefix'] else 'No'}]")
        self.update_gui(f"Random string selection [{settings['randomize_title']}]")
        self.update_gui(f"Title length: [{settings['title_length']}]")
        self.update_gui(f"Body length: [{settings['body_length']}]")
        self.update_gui(f"****User settings****")


    def post_questions(self, settings, tables_choosen):

        self.display_user_settings(settings)

     

        for website in self.website_records:
            
            self.update_gui(f"Publishing to [{website}]")

            connection_details = fetch_connection_details(connect_to_db(), website)
            self.logger.info(f"Fetched connection details for {connection_details.website_name}")
            self.update_gui(f"Fetched connection details for {connection_details.website_name}")

            self.remote_database = Db(logger=self.logger, connection_details= connection_details)

            

            self.logger.info(f"Begin processing for: [{website}]")
            self.update_gui(f"Begin processing for: [{website}]")
            # get table names

            no_of_questions_per_db = int(settings['questions'] / len(tables_choosen))

            self.logger.info(f"[{no_of_questions_per_db}] Posts fetched from each database")
            self.update_gui(f"[{no_of_questions_per_db}] Posts fetched from each database")

            workload = []

            questions_remaining = int(no_of_questions_per_db)
            questions_fetched = 0
                   

            for table in tables_choosen:
                offset = 0
                
                while questions_remaining > 0:
                    
                    self.logger.info(f"[{questions_remaining}] Questions remaining to be published")

                                     

                    if questions_remaining > self.question_load:
                        limit = self.question_load
                    else:
                        limit = questions_remaining

                    table_name = self.tables_summary[table]

                    if settings['body_length'] == '':
                        body_length = 35
                    else:
                        body_length = settings['body_length']

                    questions_remaining = questions_remaining - limit


                    thread = threading.Thread(target=self.process_posts_thread, args = (limit, offset, table_name, body_length, settings, website, self.quit_event, self.order_queue))
                    workload.append(thread)

                    questions_fetched = questions_fetched + limit

                    self.logger.info(f"{questions_fetched} questions fetched in total")
                    self.update_gui(f"{questions_fetched} prepared for processing")
                    
                    self.logger.info(f"{questions_remaining} questions remaining")
                    self.update_gui(f"{questions_remaining} remaining")
                                           
                    

                    offset = offset + limit

            job_length = len(workload)

            self.logger.info(workload)
            

            
            if job_length > self.threads_per_batch:
                num_batches = job_length // self.threads_per_batch
            else:
                num_batches = job_length

        self.update_gui(f"Attempting to process workload in {num_batches} batches")
            

        with ThreadPoolExecutor(max_workers=self.threads_per_batch) as executor:
            # launch post to remote databse thread
            remote_thread = False



            task_queue = queue.Queue()
            for i, t in enumerate(workload):
                task_queue.put(t)

            batch_counter = 0

            futures = []
            while not task_queue.empty() or self.quit_event.isSet():
                batch = []
                for _ in range(min(task_queue.qsize(), self.threads_per_batch - len(futures))):
                    batch.append(task_queue.get())

                self.update_gui(f"Running batch {batch_counter + 1}")

                for t in batch:
                    self.update_gui(f"Fetching questions for task {t.name}")
                    
                    futures.append(executor.submit(t.start))
                    self.update_gui(f"Pausing for {self.delay} seconds")
                    time.sleep(self.delay)

                

                for future in concurrent.futures.as_completed(futures):
                    future.result()

                futures.clear()
                    

                for i,t in enumerate(batch):
                    self.update_gui(f"Waiting for batch {[batch_counter]}: Thread no {i}-{t.name} to complete...")
                    self.logger.info(f"Waiting for batch {[batch_counter]}: Thread no {i}-{t.name} to complete...")
                    t.join()

                if not remote_thread:
                    remote_db_thread = threading.Thread(target=self.insert_posts, args = (self.quit_event, self.order_queue, workload))
                    remote_db_thread.daemon = True # Set the thread as a daemon, if necessary
                    remote_db_thread.priority = 8
                    remote_db_thread.start()
                    remote_db_thread.start()
                    remote_thread = True
                    
                

                self.update_gui(f"Ending batch {batch_counter + 1}")
                batch_counter = batch_counter + 1

        self.logger.info("Sending sentinel object....")
        self.update_gui("Finishing processing.....")
        self.order_queue.put(SENTINEL)

            


    def insert_posts(self, quit_event, job_queue, active_threads):
        while not quit_event.isSet():
            

            self.logger.info("Waiting for queue input")
            

            if job_queue.empty():
                time.sleep(5)
                results = None
                continue
            else:
                results = job_queue.get()

             
            if results is SENTINEL:
                # Do any necessary cleanup
                self.logger.info("Insert thread completed execution - Exiting loop....")
                self.update_gui(f"Insert thread completed execution - Exiting loop.... ")
                break

            if results is not None:


                self.update_gui(f"Inserting posts {len(results)} into website db ")

                if self.remote_database.bulk_insert_posts(results, window= self):
                    self.update_gui("Posts have been successfully inserted in the database")
                else:
                    self.update_gui("Unable to insert posts in the database")


        self.update_gui(f"Completing execution")
        self.update_gui("--------------End--------------")





    def process_posts_table_thread(self, limit, offset, table_name, body_length, settings, website, quit_event, job_queue ):
        #time.sleep(self.delay)
        if not quit_event.isSet():

            posts = self.db.fetch_all_posts_from_table( no_of_posts = limit, offset= offset, table_name = table_name, content_length = settings['body_length'])
            if posts is None:
                return None

            

            self.logger.info(f"{len(posts)} questions fetched")
            self.update_gui(f"{len(posts)} questions fetched")

            # itearate through posts
            processed_posts = self.process_posts(posts, settings, website)
            self.update_gui(f"{len(processed_posts)} questions cleaned and processed")


            # start connection to remote db
            job_queue.put(processed_posts)

            return


    def process_posts_thread(self, limit, offset, table_name, body_length, settings, website, quit_event, job_queue):
        if not quit_event.isSet():
            
            #time.sleep(self.delay)
            posts = self.db.fetch_all_posts_from_table( no_of_posts = limit, offset= offset, table_name = table_name, content_length = body_length)
            if posts is None:
                return None

            self.logger.info(f"{len(posts)} questions fetched")
            self.update_gui(f"{len(posts)} questions fetched")

            # itearate through posts
            processed_posts = self.process_posts(posts, settings, website)
            self.update_gui(f"{len(processed_posts)} questions cleaned and processed")

            job_queue.put(processed_posts)

            return

                    
    
    def get_publishing_time(self):
        
        difference_days = self.end_date - self.start_date

        days = difference_days.days

        random_day  = random.randint(0, days)        
        random_hour = random.randint(0,12)
        random_minute = random.randint(0,59)
        random_second = random.randint(0,59)

        if days == 0:
            choosen_date = self.start_date + timedelta(days = days, hours = random_hour, minutes = random_minute, seconds = random_second, microseconds=random.randint(0,99), milliseconds = random.randint(0,29000)  )

            if choosen_date > datetime.now():
                publishing_status = 'future'
            else:
                publishing_status = 'publish'
            return choosen_date.strftime("%Y-%m-%d %H:%M:%S"), publishing_status



        additional_days = timedelta(days = random_day, hours = random_hour, minutes = random_minute, seconds = random_second, microseconds=random.randint(0,99), milliseconds = random.randint(0,29000))


        choosen_date = self.start_date + additional_days


        if choosen_date > datetime.now():
            publishing_status = 'future'
        else:
            publishing_status = 'publish'

        print(publishing_status)

        publishing_date = choosen_date.strftime("%Y-%m-%d %H:%M:%S")

        return publishing_date, publishing_status
    


    def process_posts(self, posts, settings, website):
        # initialize cleaner
        cleaner = self.cleaner

        short_content = []
        processed_content = []
        for post in posts:
            self.logger.debug("Cleaning content: %s", post['link_no'])
            content = cleaner.clean_content(post['content'], settings["body_length"])
            if content:
                self.logger.debug("Cleaning title: %s", post['link_no'])
                
                title = cleaner.generate_title(content, settings['title_length'], randomize_title = self.choicesList[settings['randomize_title']])
                
                if settings['include_excerpt']:
                    content = cleaner.add_abstract(content, settings['abstract_value'])
                
                if settings["title_prefix"] != "":
                    title = cleaner.add_prefix(title, settings["title_prefix"])

                if settings["title_postfix"] != "":
                    title = cleaner.add_postfix(title, settings["title_postfix"])

                category = [post['category']]
                if settings['include_category']:
                    
                    content = cleaner.add_meta_content(content, category)

                if settings['include_references']:
                    content = cleaner.add_references_content(content)

                excerpt = cleaner.get_excerpt(content)


                publishing_date, publishing_status = self.get_publishing_time()
                
                               
                
                #self.logger.info(f"Final clean Title: [{title}] ")
                #self.logger.info(f"Final clean Content: [{content}] ")
                self.update_gui(f"Final clean Title: [{title[0:85]}] ")

                post_name_title = cleaner.clean_title(title)

                post_name = "-".join(post_name_title.split())
                if settings['random_prefix']:
                    letters = string.digits
                    random_string = ''.join(random.choice(letters) for i in range(9))
                    post_name = f"{post_name}-{random_string}"

                website.rstrip("/")
                guid = f"{website}/{post_name}"
                
                processed_content.append((title, post_name, content, excerpt, publishing_status, 'closed', publishing_date, publishing_date , publishing_date, publishing_date, guid, 1))
        return processed_content

    def publish_to_remote(self, records_to_update):
        
        result = self.remote_database.bulk_insert_posts(records_to_update, window= self)

        return result

                   
        

    def clearForm(self, evt):
        self.questions_value.SetValue("")
        self.random_prefix_value.SetValue(0)
        self.include_abstract_value.SetValue(0)
        self.include_category_value.SetValue(0)
        self.title_prefix_value.SetValue("")
        self.title_postfix_value.SetValue("")
        self.randomize_title_value.SetSelection(1)
        self.title_length_value.SetValue("15")
        self.body_length_value.SetValue("75")
            
        

    def get_session(self):
        if self.parent.engine is False:
            self.logger.error("Unable to connect to database")
            return False
        else:
            session = create_session(self.parent.engine)
            return session