import os
import sys
import wx
import csv
import wx.adv
import wx.html
import wx.lib.inspection
import threading
import time
from queue import Queue
from sys import maxsize
from engine.db import Db



from charts.CrawlingReportsFrame import CrawlingReportsFrame
from engine.gui_grids import GenericTable

class PostaPanel(wx.Panel):
    #----------------------------------------------------------------------
    def __init__(self, parent, tables):
        wx.Panel.__init__(self, parent)
        self.table_names = [x[0] for x in tables ]
        self.wildcard = "Setting files (*.csv)|*.csv|All files (*.*)|*.*"


               
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
        self.logTxtField = wx.TextCtrl(self, -1, "", style=wx.TE_RICH|wx.TE_MULTILINE)
        self.reportTxtField = wx.TextCtrl(self, -1, "", style=wx.TE_RICH|wx.TE_MULTILINE)

        
        
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
        self.bottom_left_vertical_sizer.Add(self.logTxtField, 1, wx.EXPAND | wx.ALL, 5)
        self.bottom_right_vertical_sizer.Add(self.reportTxtField, 1, wx.EXPAND | wx.ALL, 5)
        
        self.bottom_horizontal_sizer.Add(self.bottom_left_vertical_sizer,1,flag = wx.EXPAND | wx.ALL)
        self.bottom_horizontal_sizer.Add(self.bottom_right_vertical_sizer ,2,flag = wx.EXPAND | wx.ALL)




        self.mainSizer.Add(self.top_horizontal_sizer, 1, flag = wx.EXPAND | wx.ALL)
        self.mainSizer.Add(self.bottom_horizontal_sizer, 2, flag = wx.EXPAND | wx.ALL)
        

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
        
        #self.grid.SetMinSize((-1, 250))
        #self.grid.SetVirtualSize((-1, 250))
        self.grid.ShowScrollbars(wx.SHOW_SB_NEVER,wx.SHOW_SB_DEFAULT)
        #
        #self.grid.SetVirtualSize(600, 400)
        
        if data is None:
            data = [["https://onlinetutorglobal.com/", "***********", "***********", "**********", "1", "********" ],["********", "***********", "***********", "***********", "", "***********" ], ["********", "***********", "***********", "***********", "", "***********" ], ["********", "***********", "***********", "***********", "", "***********" ], ["********", "***********", "***********", "***********", "", "***********" ], ["********", "***********", "***********", "***********", "", "***********" ],["********", "***********", "***********", "***********", "", "***********" ],["********", "***********", "***********", "***********", "", "***********" ],["********", "***********", "***********", "***********", "", "***********" ]]
        colLabels = ("site", "posts", "username", "password", "Crawl (Yes/No)", "Status") 
        self.data_table = GenericTable(data, colLabels = colLabels) 
        self.grid.SetTable(self.data_table, True)
        self.grid.SetColFormatBool(4)
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
        print(self.data_table.data)


    #-------------------------------------------------------------------
    def stopPosting(self, evt):
        pass

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
            #print(self.data_table.data)
            self.data_table.data = None
            #print(self.data_table.data)
            self.data_table.data = csv_data
            rows_affected = len(csv_data)

            msg = wx.grid.GridTableMessage(self.data_table,wx.grid.GRIDTABLE_NOTIFY_ROWS_INSERTED,1,  rows_affected)

            #self.scroll_grid.Hide()
            #self.reportSizer.Detach(self.scroll_grid)
            #self.scroll_grid.Destroy()
            #self.grid = None
            
            #self.scroll_grid = None
            # create a new scrolled window
            #self.scroll_grid = wx.ScrolledWindow(self, -1)
            #self.scroll_grid.SetScrollbars(1, 1, 600, 400)



            #self.createGrid(self.scroll_grid, csv_data)
            #self.grid.SetMaxSize((-1, 400))
            #self.grid.AutoSize()
            self.grid.GetTable().GetView().ProcessTableMessage(msg)

            self.grid.ForceRefresh()
            

            self.Layout()

            """self.reportSizer.Layout()
            self.grid_button_sizer.Layout()
            self.top_left_vertical_sizer.Layout()
            self.top_horizontal_sizer.Layout()
            self.mainSizer.Layout()"""
            """


        

            self.reportSizer.Add(self.scroll_grid, 0, wx.EXPAND | wx.ALL)
            self.scroll_grid.Fit()
            self.reportSizer.Fit(self.scroll_grid)


            widget = self.grid
            while widget.GetParent():
                widget = widget.GetParent()
                widget.Layout()
                print("layout")
                if widget.IsTopLevel():
                    break
       

            
            #self.top_left_vertical_sizer.Add(self.grid_button_sizer)
            self.Refresh()
            self.Layout()"""



    #-------------------------------------------------------------------
    def saveSettings(self, evt):
        pass



#-------------------------------------------------------------------
#-------------------------------------------------------------------



class PostaBotFrame(wx.Frame):
    """Whatsapp GUI Frame"""
    def __init__(self, parent):
        self.title = "Posta posting Bot"
        wx.Frame.__init__(self, parent, -1, self.title, size=(900,700))
        self.createMenuBar()

        self.db = Db()
        tables = self.db.fetch_tables()

        self.createPanel(tables)


        #--------------------------------
        self.icons_dir = wx.GetApp().GetIconsDir()

        
        frameIcon = wx.Icon(os.path.join(self.icons_dir, "posta.ico"),   type=wx.BITMAP_TYPE_ICO)
        self.SetIcon(frameIcon)
        self.Center(wx.BOTH)

    def createPanel(self, table):
        self.mainPanel = PostaPanel(self, table)
        self.box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_sizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.SetSizer(self.box_sizer)


    def menuData(self):
        return [("&File", (

                    ("About...", "Show about window", self.OnAbout),
                    ("Export Settings", "Export Database", self.OnExport),
                    ("Import Settings", "Import Database", self.OnImport),
                    ("&Quit", "Quit", self.OnCloseWindow))
                ),
                ("&Reports",(
                    ("View Posting Reports", "Show posts reports", self.OnPostReports),
                    ("View Crawling Reports", "Show crawling reports", self.OnCrawlReports)
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
        self.db.close_conn()
        self.Destroy()

    def OnAbout(self, event):
        dlg = PostaAbout(self)
        dlg.ShowModal()
        dlg.Destroy()

    
    #-----------------------------------------------------------------------

    def OnCrawlReports(self, event):
        frame = CrawlingReportsFrame("Crawling reports", parent=wx.GetTopLevelParent(self))
        frame.SetWindowStyle(style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        frame.Show(True)




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
        con = sqlite3.connect('bot.db')
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
        wx.Dialog.__init__(self, parent, -1, 'About Sketch',
                          size=(440, 400) )

        html = wx.html.HtmlWindow(self)
        html.SetPage(self.text)
        button = wx.Button(self, wx.ID_OK, "Okay")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(button, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()






#----------------------------------------------------------------------

class PostaBotApp(wx.App):

    def OnInit(self):
        bmp = wx.Image("gui/posta.png").ConvertToBitmap()
        wx.adv.SplashScreen(bmp, wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT,
                1000, None, -1)
        wx.Yield()

        #----------------------------
        self.installDir = os.path.split(os.path.abspath(sys.argv[0]))[0]


        #-----------------------------


        frame = PostaBotFrame(None)
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




#--------------------------------------------------

if __name__ == '__main__':
    
    app = PostaBotApp(False)
    #wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()

