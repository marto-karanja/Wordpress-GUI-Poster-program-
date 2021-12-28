import os
import sys
import wx
import wx.adv
import wx.html
import threading
import time
from queue import Queue
from sys import maxsize



from charts.CrawlingReportsFrame import CrawlingReportsFrame

class PostaPanel(wx.Panel):
    #----------------------------------------------------------------------
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
               
        self.layout()

    def layout(self):
        # create main horizontal sizer
        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttonSizer = wx.BoxSizer(wx.VERTICAL)
        self.reportsSizer = wx.BoxSizer(wx.VERTICAL)
        
        #--------------------------

        self.SetSizer(self.mainSizer)
        self.Fit()



#-------------------------------------------------------------------



class PostaBotFrame(wx.Frame):
    """Whatsapp GUI Frame"""
    def __init__(self, parent):
        self.title = "Posta posting Bot"
        wx.Frame.__init__(self, parent, -1, self.title, size=(900,700))
        self.createMenuBar()

        self.createPanel()


        #--------------------------------
        self.icons_dir = wx.GetApp().GetIconsDir()

        
        frameIcon = wx.Icon(os.path.join(self.icons_dir, "posta.ico"),   type=wx.BITMAP_TYPE_ICO)
        self.SetIcon(frameIcon)
        self.Center(wx.BOTH)

    def createPanel(self):
        self.mainPanel = PostaPanel(self)
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
    app.MainLoop()

