# sample_two.py

import os
import sys
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2Wx
import wx

import seaborn


# class MyCanvasPanel
# class MyFrame
# class MyApp

#---------------------------------------------------------------------------

# Some data
# Pie chart, where the slices will be ordered and plotted counter-clockwise :
labels = 'Hogs', 'Frogs', 'Logs', 'Dogs'
sizes = [15, 30, 45, 10]
explode = (0, 0.1, 0, 0)  # Only "explode" the 2nd slice (i.e. 'Hogs').

#---------------------------------------------------------------------------

class MyCanvasPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        #------------
        
        # Simplified init method.
        self.CreateCtrls()
        self.DoLayout()
        
    #-----------------------------------------------------------------------

    def CreateCtrls(self):
        """
        ...
        """

        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)

        #------------
        
        self.canvas = FigureCanvas(self, -1, self.figure)

        #------------
        
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()


    def DoLayout(self):
        """
        ...
        """

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        
        
    def Draw(self):
        """
        ...
        """
        
        # Make figure and axes.
        self.axes.plot(1, 0)
        
        # To draw the pies.
        self.axes.pie(sizes,
                      labels=labels,
                      autopct='%1.1f%%',
                      textprops={'size': 'smaller'},
                      shadow=True,
                      radius=0.5, 
                      startangle=90,
                      explode=explode)

        # Equal aspect ratio ensures that pie is drawn as a circle.           
        self.axes.axis('equal')  

        self.axes.legend(title="Hogs and dogs",
                         loc="center right",
                         bbox_to_anchor=(1, 0, 0, 1))
        self.axes.set_title("Raining hogs and dogs", bbox={'facecolor':'0.9', 'pad':8})

#---------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, -1,
                          title,
                          size=(640, 500))

        #------------

        # Return icons folder.
        self.icons_dir = wx.GetApp().GetIconsDir()

        #------------
        
        # Simplified init method.
        self.SetProperties()
        self.CreateCtrls()
        
    #-----------------------------------------------------------------------

    def SetProperties(self):
        """
        ...
        """

        self.SetMinSize((640, 500))

        #------------

        frameIcon = wx.Icon(os.path.join(self.icons_dir,
                                         "wxwin.ico"),
                            type=wx.BITMAP_TYPE_ICO)
        self.SetIcon(frameIcon)


    def CreateCtrls(self):
        """
        ...
        """

        self.panel = MyCanvasPanel(self)
        self.panel.Draw()
    
#---------------------------------------------------------------------------

class MyApp(wx.App):    
    def OnInit(self):

        #------------

        self.installDir = os.path.split(os.path.abspath(sys.argv[0]))[0]
        
        #------------
        
        frame = MyFrame("Sample two")
        self.SetTopWindow(frame)
        frame.Show(True)

        return True
    
    #-----------------------------------------------------------------------
    
    def GetInstallDir(self):
        """
        Return the installation directory for my application.
        """

        return self.installDir


    def GetIconsDir(self):
        """
        Return the icons directory for my application.
        """

        icons_dir = os.path.join(self.installDir, "icons")
        return icons_dir
    
#---------------------------------------------------------------------------

def main():
    app = MyApp(False)
    app.MainLoop()

#---------------------------------------------------------------------------

if __name__ == "__main__" :
    main()
    
