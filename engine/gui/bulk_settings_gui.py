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
from engine.local_db import connect_to_db, create_threaded_session, remove_session, save_published_posts, save_short_posts,get_connection, create_session, fetch_published_posts, update_post, get_title_length, set_title_length, count_published_posts, delete_multiple_posts, fetch_short_posts, delete_multiple_short_posts, get_content_length, set_content_length, delete_all_tables, save_references_to_db, get_website_records, remove_website_records
from .drip_posting_gui import PostaBotFrame, PostaAbout
from engine.gui.bulk_publishing import BulkPublishingFrame

class BulkPostsFrame(wx.Frame):
    """Whatsapp GUI Frame"""
    def __init__(self, parent, title = None, logger = None, tables_summary = None):
        self.title = title or "Banned Strings"
        wx.Frame.__init__(self, parent, -1, self.title)
        self.parent  = parent

        self.logger = logger or logging.getLogger(__name__)

        website_records = self.fetch_website_records()

        

        self.createMenuBar()



        

        self.filename = ""

        self.createPanel(website_records)


        #--------------------------------
    def createPanel(self, stop_words):
        self.mainPanel = BulkPostsPanel(self, self.logger, stop_words, parent_frame = self.parent)
        self.box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_sizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.box_sizer.SetSizeHints(self)
        self.SetSizer(self.box_sizer)
        self.Layout()

    def fetch_engine(self):
        return connect_to_db()


    def fetch_website_records(self):
        self.engine = self.fetch_engine()
        
        website_words = []
        if self.engine is False:
            self.logger.error("Unable to connect to database")
            return []
        else:
            website_records = get_website_records(self.engine)
            self.logger.info("Fetched %s stopwords successfully", len(website_records))
            return website_records
        
    def updateDb(self, event):
        from .update_db_gui import UpdateDbFrame
        # launch thread

        frame = UpdateDbFrame(parent=wx.GetTopLevelParent(self), logger = self.logger, title = "Update Database")

        frame.Show(True)

    def menuData(self):
        return [("&File", (

                    ("About...", "Show about window", self.OnAbout),
                    ("Manage Banned Strings", "Create/Delete Banned Strings", self.OnManageBanned),
                    ("Upload References", "Add References", self.UploadReferences),                    
                    ("&Quit", "Quit", self.OnCloseWindow))
                ),
                ("&Bulk Options",(
                    ("Update Word Count", "Update Db", self.updateDb),            
                    ("Export Settings", "Export Database", self.OnExport),
                    ("Import Settings", "Import Database", self.OnImport),
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

    def OnManageBanned(self, event):
        from .banned_strings_gui import BannedStringsFrame
        frame = BannedStringsFrame(parent=wx.GetTopLevelParent(self), title = "Banned Strings")
        frame.SetWindowStyle(style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        frame.Show(True)

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

    def OnAbout(self, event):
        dlg = PostaAbout(self)
        dlg.ShowModal()
        dlg.Destroy()




    def OnCloseWindow(self, event):
        self.Destroy()


    
class BulkPostsPanel(wx.Panel):
    def __init__(self, parent, logger = None, website_records = None, parent_frame = None):
        wx.Panel.__init__(self, parent)
        self.logger = logger or logging.getLogger(__name__)  
        self.parent = parent
        self.parent_frame = parent_frame
        self.website_records = website_records

        self.logger.info(f"Setting up bulk posts Settings and websites")

        

        self.filename = ""

        # get a logger
                     
        self.layout()

    #---------------------------------------------------------
    def layout(self):

        # create main horizontal sizer
        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.parentSizer = wx.BoxSizer(wx.VERTICAL)

        control_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # create main control buttons
        btnData = [
            ("Begin Publishing", self.beginPublishing),
            ("Delete Website Settings",  self.removeString)
            ]
        self.create_buttons(control_button_sizer, btnData, flag=wx.ALL)

        
        # create combo box
        self.create_combo()


        self.combo_sizer.Add(control_button_sizer, 0)

        # create form sizer
        form_button_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, "Add new Website")

        website_lbl = wx.StaticText(self, -1, "Website")
        self.website_value = wx.TextCtrl(self, -1, "https://name.com")

        sshLbl = wx.StaticText(self, -1, "SSH Host(IP address):")
        self.ssh_value = wx.TextCtrl(self, -1, "")

        sshPortLbl = wx.StaticText(self, -1, "Port:")
        self.ssh_port_value = wx.ComboBox(parent = self, id = -1, choices = ['22', '21098', '63162'])
        self.ssh_port_value.SetValue('22')

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

        ssh_port_sizer = wx.BoxSizer(wx.HORIZONTAL)

        formSizer.Add(website_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.website_value, 0, wx.EXPAND)

        #ssh_port_sizer.Add(sshLbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        ssh_port_sizer.Add(self.ssh_value, 0, wx.ALIGN_CENTER_VERTICAL)
        ssh_port_sizer.Add(sshPortLbl, 0, wx.ALIGN_CENTER_VERTICAL)
        ssh_port_sizer.Add(self.ssh_port_value, 0, wx.ALIGN_CENTER_VERTICAL)

        formSizer.Add(sshLbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(ssh_port_sizer, 0, wx.EXPAND, border = 5)
        formSizer.Add(cpanel_username_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.cpanel_username_value, 0, wx.EXPAND)
        formSizer.Add(ssh_password_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.ssh_password_value, 0, wx.EXPAND)
        formSizer.Add(database_username_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.database_username_value, 0, wx.EXPAND)
        formSizer.Add(database_password_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.database_password_value, 0, wx.EXPAND)
        formSizer.Add(database_name_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.database_name_value, 0, wx.EXPAND)
        formSizer.Add(database_prefix_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        formSizer.Add(self.database_prefix_value, 0, wx.EXPAND)

        self.certificate_path_lbl = wx.StaticText(self, -1, "Ceritificate file:[No File Uploaded]")
        formSizer.Add(self.certificate_path_lbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

        btnData = [
                    ("Add Private Key File", self.savePrivateKey),
                    ("Save Website Details",  self.saveWebsiteDetails),
                    ("Clear Form",  self.clearForm)]
        self.create_buttons(formSizer, btnData, flag=wx.ALL)

        form_button_sizer.Add(formSizer)

        self.logTxtField = wx.TextCtrl(self, -1, "", style=wx.TE_RICH|wx.TE_MULTILINE)

        

        # Add form sizer to main sizer
        self.mainSizer.Add(form_button_sizer, 0, border = 5)

        self.parentSizer.Add(self.mainSizer,1)
        self.parentSizer.Add(self.logTxtField,1, wx.EXPAND,)

        #self.SetAutoLayout(True)
        self.parentSizer.SetSizeHints(self)
        self.SetSizer(self.parentSizer)
        self.Layout()

    def create_combo(self):
        self.website_records_combos = wx.CheckListBox(parent = self, id = -1, choices = list(self.website_records.keys()), style=wx.LB_MULTIPLE)
        self.combo_sizer= wx.StaticBoxSizer(wx.VERTICAL, self, "Websites Stored")
        self.combo_sizer.Add(self.website_records_combos, 1, wx.EXPAND|wx.ALL, 2)
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

        

    def beginPublishing(self, evt):
        website_records = self.website_records_combos.GetCheckedStrings()
        if len(website_records) > 0:
            frame = BulkPublishingFrame(parent=wx.GetTopLevelParent(self), panel = self, title = "Bulk Publish Posts", logger = self.logger, website_records = website_records)
            frame.SetWindowStyle(style=wx.DEFAULT_FRAME_STYLE)
            frame.Show(True)
        else:
            wx.MessageBox("Ensure you have choosen a website to populate", "Error!", wx.ICON_ERROR)
        

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
        website_details['ssh_port'] = self.ssh_port_value.GetValue()
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



