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
from engine.db import Db
from engine.posta import Posta
from engine.reports_gui import ReportBotFrame
from engine.category_post import CategoryPostFrame
from engine.gui.banned_strings_gui import BannedStringsFrame
from engine.gui.bulk_settings_gui import BulkPostsFrame
from engine.gui.drip_posting_gui import PostaBotFrame
from engine.models import BannedStrings, PublishedPosts, ProcessingPosts, Base
from engine.local_db import connect_to_db, create_threaded_session, remove_session, save_published_posts, save_short_posts,get_connection, create_session, fetch_published_posts, update_post, get_title_length, set_title_length, count_published_posts, delete_multiple_posts, fetch_short_posts, delete_multiple_short_posts, get_content_length, set_content_length, delete_all_tables, save_references_to_db, create_session,save_website_records, get_website_records, remove_website_records

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session




from charts.CrawlingReportsFrame import CrawlingReportsFrame
from engine.gui_grids import GenericTable


engine = connect_to_db()

        # now all calls to Session() will create a thread-local session
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)



class LaunchBotFrame(wx.Frame):
    """Whatsapp GUI Frame"""
    def __init__(self, parent, logger = None):
        self.title = "Launch Publisher"
        wx.Frame.__init__(self, parent, -1, self.title)
        self.setup_local_db()
        
        self.logger = logger or logging.getLogger(__name__)

        #self.db = Db(self.logger)
        #self.db.start_conn()
        #tables_summary = self.db.fetch_tables_summary()
        # include available posts

        self.createPanel()


        #--------------------------------
        self.icons_dir = wx.GetApp().GetIconsDir()

        
        self.frameIcon = wx.Icon(os.path.join(self.icons_dir, "posta.ico"),   type=wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.frameIcon)
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


    def createPanel(self):
        self.mainPanel = LaunchPanel(self, logger = self.logger)
        self.box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_sizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.box_sizer.SetSizeHints(self)
        self.SetSizer(self.box_sizer)



    def OnCloseWindow(self, event):
        if self.engine:
            self.engine.dispose()
        self.Destroy()


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

    def fetch_website_records(self):
        self.engine = connect_to_db()
        
        website_words = []
        if self.engine is False:
            self.logger.error("Unable to connect to database")
            return []
        else:
            website_records = get_website_records(self.engine)
            self.logger.info("Fetched %s stopwords successfully", len(website_records))
            return website_records



class LaunchPanel(wx.Panel):
    def __init__(self, parent, logger = None, website_records = None):
        wx.Panel.__init__(self, parent)
        self.logger = logger or logging.getLogger(__name__)  
        self.parent = parent
        #self.parent_frame = parent_frame
        self.website_records = self.parent.fetch_website_records()

        self.logger.info(f"Setting up bulk posts Settings and websites")

        
        self.filename = ""

        # get a logger
                     
        self.layout()

    

    #---------------------------------------------------------
    def layout(self):

        # create main horizontal sizer
        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.parentSizer = wx.BoxSizer(wx.VERTICAL)

        #control_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # create main control buttons
        """btnData = [
            ("Delete Website Settings",  self.removeString),
            ("View Website Settings",  self.removeString)
            ]"""
        #self.create_buttons(control_button_sizer, btnData, flag=wx.ALL)

        
        # create combo box
        #self.create_combo()


        #self.combo_sizer.Add(control_button_sizer, 0)

        # create form sizer
        form_button_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Add new Website")

        connection_lbl = wx.StaticText(self, -1, "Website")
        connections = ['Local Host', 'Remote Host']

        self.connection_combo_box = wx.ComboBox(self, choices=connections, style=wx.CB_DROPDOWN |wx.CB_READONLY)
        self.connection_combo_box.SetSelection(0)

        sshLbl = wx.StaticText(self, -1, "SSH Host(IP address):")
        self.ssh_value = wx.TextCtrl(self, -1, "")

        cpanel_username_lbl = wx.StaticText(self, -1, "Cpanel Username:")
        self.cpanel_username_value = wx.TextCtrl(self, -1, "")

        ssh_password_lbl = wx.StaticText(self, -1, "SSH Password:")
        self.ssh_password_value = wx.TextCtrl(self, -1, "")

        database_username_lbl = wx.StaticText(self, -1, "Database Username:")
        self.database_username_value = wx.TextCtrl(self, -1, "")

        database_password_lbl = wx.StaticText(self, -1, "Database Password:")
        self.database_password_value = wx.TextCtrl(self, -1, "")

        database_name_lbl = wx.StaticText(self, -1, "Database Name:")
        self.database_name_value = wx.TextCtrl(self, -1, "")

        database_prefix_lbl = wx.StaticText(self, -1, "Database Prefix:")
        self.database_prefix_value = wx.TextCtrl(self, -1, "")

        formSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        formSizer.AddGrowableCol(1)

        formSizer.Add(connection_lbl, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.connection_combo_box, 0, wx.EXPAND)
        formSizer.Add(sshLbl, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.ssh_value, 0, wx.EXPAND)
        formSizer.Add(cpanel_username_lbl, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.cpanel_username_value, 0, wx.EXPAND)
        formSizer.Add(ssh_password_lbl, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.ssh_password_value, 0, wx.EXPAND)
        formSizer.Add(database_username_lbl, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.database_username_value, 0, wx.EXPAND)
        formSizer.Add(database_password_lbl, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.database_password_value, 0, wx.EXPAND)
        formSizer.Add(database_name_lbl, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.database_name_value, 0, wx.EXPAND)
        formSizer.Add(database_prefix_lbl, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.database_prefix_value, 0, wx.EXPAND)

        self.certificate_path_lbl = wx.StaticText(self, -1, "Ceritificate file:[No File Uploaded]")
        formSizer.Add(self.certificate_path_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

        btnData = [
                    ("Add Private Key File", self.savePrivateKey),
                    ("Save Db connection Details",  self.saveWebsiteDetails),
                    ("Clear Form",  self.clearForm)]
        self.create_buttons(formSizer, btnData, flag=wx.ALL)

        form_button_sizer.Add(formSizer)

        launch_button_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Launch Bot sizer")

        main_button_data = [
            ("Launch Bulk Publisher", self.launchBulkPublisher),
            ("Launch Drip Publisher",  self.launchDripPublisher)
        ]

        self.create_buttons(launch_button_sizer, main_button_data, flag = wx.EXPAND, vertical = True)


        #self.logTxtField = wx.TextCtrl(self, -1, "", style=wx.TE_RICH|wx.TE_MULTILINE)

        

        # Add form sizer to main sizer
        self.mainSizer.Add(form_button_sizer, 0 , border = 5)

        self.parentSizer.Add(self.mainSizer,4)
        self.parentSizer.Add(launch_button_sizer,1, wx.EXPAND, border = 15)

        #self.SetAutoLayout(True)
        self.parentSizer.SetSizeHints(self)
        self.SetSizer(self.parentSizer)
        self.Layout()

    def create_combo(self):
        self.website_records_combos = wx.CheckListBox(parent = self, id = -1, choices = list(self.website_records.keys()), style=wx.LB_MULTIPLE)
        self.combo_sizer= wx.StaticBoxSizer(wx.VERTICAL, self, "Websites Stored")
        self.combo_sizer.Add(self.website_records_combos, 1, wx.EXPAND|wx.ALL, 2)
        #self.mainSizer.Add(self.combo_sizer, 0, wx.EXPAND|wx.ALL, 2)
        #self.mainSizer.Add(combo_sizer, 1, wx.EXPAND|wx.ALL, 2)


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
            self.website_records = self.parent.fetch_website_records()
            self.website_records_combos.Destroy()
            self.website_records_combos = wx.CheckListBox(parent = self, id = -1, choices = list(self.website_records.keys()), style=wx.LB_MULTIPLE)

            self.combo_sizer.Add(self.website_records_combos, 1, wx.EXPAND|wx.ALL, 2)

            
            #self.Hide()
            self.Refresh()
            self.Update()
            self.Layout()
            self.Fit()


    def saveWebsiteDetails(self, evt):
        # if all form fields have a value
        website_details = {}
        website_details['website_name'] = self.website_value.GetValue()
        website_details['ssh_host'] = self.ssh_value.GetValue()
        website_details['cpanel_username'] = self.cpanel_username_value.GetValue()
        website_details['ssh_password'] = self.ssh_password_value.GetValue()
        website_details['database_username'] = self.database_username_value.GetValue()
        website_details['database_password'] = self.database_password_value.GetValue()
        website_details['database_name'] = self.database_name_value.GetValue()
        website_details['database_prefix'] = self.database_prefix_value.GetValue()

        form_empty = False

        for item in website_details.keys():
            if website_details[item] == "":
                form_empty = True

        if self.filename == "":
            form_empty = True
        else:
            website_details["security_filepath"] = self.filename

        if form_empty:
            wx.MessageBox("Ensure that you have filled all the fields", "Error", wx.ICON_ERROR)
        else:
            if save_website_records(self.parent.engine, website_details):
                self.website_value.SetValue("")
                self.ssh_value.SetValue("")
                self.cpanel_username_value.SetValue("")
                self.ssh_password_value.SetValue("")
                self.database_username_value.SetValue("")
                self.database_password_value.SetValue("")
                self.database_name_value.SetValue("")
                self.database_prefix_value.SetValue("")
                wx.MessageBox("Record saved successfully", "Success", wx.ICON_INFORMATION)
                self.refresh_display()

    def clearForm(self, evt):
        self.website_value.SetValue("")
        self.ssh_value.SetValue("")
        self.cpanel_username_value.SetValue("")
        self.ssh_password_value.SetValue("")
        self.database_username_value.SetValue("")
        self.database_password_value.SetValue("")
        self.database_name_value.SetValue("")
        self.database_prefix_value.SetValue("")
            
        

    def get_session(self):
        if self.parent.engine is False:
            self.logger.error("Unable to connect to database")
            return False
        else:
            session = create_session(self.parent.engine)
            return session


    def removeString(self, evt):
        selected_strings = self.website_records_combos.GetCheckedStrings()
        if len(selected_strings) > 0:
            # delete string'# get string ids
            #string_ids = [self.stop_words[word] for word in selected_strings]
            #session = self.get_session()
            try:
                remove_website_records(connect_to_db(), selected_strings)
            except Exception as e:
                self.logger.error("Unable to delete string", exc_info=1)
            else:
                self.refresh_display()

                wx.MessageBox("Successfully deleted from database", "Delete Success", wx.OK | wx.ICON_INFORMATION)
            # refresh database
        else:
            wx.MessageBox("You have not selected anything", "Error", wx.OK | wx.ICON_ERROR)


    def log_message_to_txt_field(self, msg):
        self.logTxtField.AppendText(msg)
        self.logTxtField.AppendText("\n")

    def launchDripPublisher(self, evt):
        
        frame = PostaBotFrame(None, logger = self.logger )
        self.locale = wx.GetLocale()
        frame.SetIcon(self.parent.frameIcon)
        frame.Show(True)
        self.parent.Destroy()
        

    def launchBulkPublisher(self, evt):
        
        frame = BulkPostsFrame(None, title = "Publish posts in Bulk", logger = self.logger)
        frame.SetIcon(self.parent.frameIcon)
        frame.SetWindowStyle(style=wx.DEFAULT_FRAME_STYLE)
        frame.Show(True)
        self.parent.Destroy()
        










#----------------------------------------------------------------------

class PostaBotApp(wx.App):

    def OnInit(self, logger = None):
        bmp = wx.Image("gui/posta.png").ConvertToBitmap()
        wx.adv.SplashScreen(bmp, wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT,
                1000, None, -1)
        wx.Yield()

        #----------------------------
        self.installDir = os.path.split(os.path.abspath(sys.argv[0]))[0]


        #-----------------------------

        self.logger = logger or logging.getLogger(__name__)   
        #frame = PostaBotFrame(None, self.logger)
        frame = LaunchBotFrame(None, self.logger)
        self.locale = wx.GetLocale()
        frame.Show(True)
        self.SetTopWindow(frame)
        return True

    def GetInstallDir(self):
        """
        Return the installation directory for my application.
        """
        

        return self.installDir


    def GetIconsDir(self):
        """
        Return the icons directory for my application.
        """

        icons_dir = os.path.join(self.installDir, "gui")
        return icons_dir


def get_logger():
    d = datetime.now()

    log_file = d.strftime("%d %a-%m-%Y-%H-%M-%S")
    log_path = os.getcwd() + "\\logs"

    CHECK_FOLDER = os.path.isdir(log_path)
    if not CHECK_FOLDER:
          os.makedirs(log_path)

    print(log_path)


    logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    datefmt="'%m/%d/%Y %I:%M:%S %p",
    handlers=[
        logging.FileHandler("{0}/{1}.log".format(log_path, log_file)),
        logging.StreamHandler()
    ],
    level = logging.DEBUG)

    logger = logging.getLogger(__name__)

    # get posta object
    logger.info("...Starting Application...")
    return logger




#--------------------------------------------------

if __name__ == '__main__':

    logger = get_logger()
    
    app = PostaBotApp(False, logger)
    #wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()


