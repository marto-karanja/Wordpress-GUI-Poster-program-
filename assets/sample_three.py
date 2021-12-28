# sample_three.py

"""

Link : https://white-wheels.hatenadiary.org/entry/20100327/p5

"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.interactive(True)
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2Wx
from mpl_toolkits.mplot3d import Axes3D
import wx

# class MyCanvasPanel
# class MyFrame
# class MyApp

#---------------------------------------------------------------------------

class MyCanvasPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        #------------

        self.parent = parent

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
        self.figure.set_facecolor((1.,1.,1.))
        self.axes = self.figure.add_subplot(111)

        #------------
        
        self.canvas = FigureCanvas(self, -1, self.figure)
        # self.canvas.SetBackgroundColour(wx.Colour(100, 100, 100))
        
        #------------
        
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()

        #------------
        
        self.SetSize()


    def SetSize(self):
        """
        ...
        """
        
        size = tuple(self.parent.GetClientSize())
        self.canvas.SetSize(740, 740)
        self.figure.set_size_inches(float(size[0])/self.figure.get_dpi(),
                                    float(size[1])/self.figure.get_dpi())

    def DoLayout(self):
        """
        ...
        """

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.RIGHT| wx.TOP | wx.GROW)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        
        
    def Draw(self):
        """
        ...
        """
        
        x = np.arange(-3, 3, 0.25)
        y = np.arange(-3, 3, 0.25)
        X, Y = np.meshgrid(x, y)
        Z = np.sin(X)+ np.cos(Y)
        
        ax = Axes3D(self.figure)
        ax.plot_wireframe(X, Y, Z)

#---------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, -1,
                          title,
                          size=(740, 740))

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

        self.SetMinSize((740, 740))
        
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
        
        frame = MyFrame("Sample three")
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
    
