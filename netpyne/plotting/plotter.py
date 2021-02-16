"""
Module for plotting analyses

"""

import matplotlib.pyplot as plt

try:
    basestring
except NameError:
    basestring = str

legendParams = ['loc', 'bbox_to_anchor', 'fontsize', 'numpoints', 'scatterpoints', 'scatteryoffsets', 'markerscale', 'markerfirst', 'frameon', 'fancybox', 'shadow', 'framealpha', 'facecolor', 'edgecolor', 'mode', 'bbox_transform', 'title', 'title_fontsize', 'borderpad', 'labelspacing', 'handlelength', 'handletextpad', 'borderaxespad', 'columnspacing', 'handler_map']


class GeneralPlotter:
    """A class used for plotting"""

    def __init__(self, data, axis=None, sim=None, options={}, **kwargs):
        """
        Parameters
        ----------
        data : dict?

        axis : matplotlib axis
            The axis to plot into.  If axis is set to None, a new figure and axis are created and plotted into.  If plotting into an existing axis, more options are available: xtwin, ytwin,
        
        """

        if not sim:
            from .. import sim

        self.data = data
        self.axis = axis
        self.options = sim.cfg.plotting
        #self.options['addLegend'] = False

        for option in options:
            if option in self.options:
                self.options[option] = options[option]

        if self.axis is None:
            self.fig, self.axis = plt.subplots(figsize=self.options['figSize'])
        else:
            self.fig = plt.gcf()


    def saveData(self, fileName=None, fileDesc=None, fileType='pkl', sim=None, **kwargs):

        from ..analysis import saveData as saveFigData

        saveFigData(self.data, fileName=fileName, fileDesc=fileDesc, fileType=fileType, sim=sim, **kwargs)
    

    def formatAxis(self, **kwargs):
        
        if 'title' in kwargs:
            self.axis.set_title(kwargs['title'], fontdict=None, loc=None, pad=None, y=None)

        if 'xlabel' in kwargs:
            self.axis.set_xlabel(kwargs['xlabel'], fontdict=None, loc=None, labelpad=None)

        if 'ylabel' in kwargs:
            self.axis.set_ylabel(kwargs['ylabel'], fontdict=None, loc=None, labelpad=None)

        # Set fontSize



    def saveFig(self, fileName=None, fileSpec=None, **kwargs):
        
        filespec = ''
        if fileSpec is not None:
            filespec = '_' + str(fileSpec)

        if isinstance(fileName, basestring):
            fileName = fileName + filespec
        else:
            fileName = sim.cfg.filename + '_' + self.type + filespec + '.png'
        
        self.fig.savefig(fileName)



    def showFig(self, **kwargs):

        dummy = plt.figure()
        new_manager = dummy.canvas.manager
        new_manager.canvas.figure = self.fig
        self.fig.set_canvas(new_manager.canvas)
        self.fig.show()


    def addLegend(self, handles=None, labels=None, **kwargs):

        legendKwargs = {}
        for kwarg in kwargs:
            if kwarg in legendParams:
                legendKwargs[kwarg] = kwargs[kwarg]

        cur_handles, cur_labels = self.axis.get_legend_handles_labels()

        if not handles:
            handles = cur_handles
        if not labels:
            labels = cur_labels

        self.axis.legend(handles, labels, **legendKwargs)
        


    def finishFig(self, **kwargs):

        if self.options['saveData']:
            self.saveData(**kwargs)
        if self.options['saveFig']:
            self.saveFig(**kwargs)
        if self.options['showFig']:
            self.showFig(**kwargs)
        else:
            plt.close(self.fig)
        
                

    


class ScatterPlotter(GeneralPlotter):
    """A class used for scatter plotting"""

    def __init__(self, data, axis=None, options={}, **kwargs):
        
        super().__init__(data=data, axis=axis, **kwargs)

        self.type       = 'scatter'
        self.x          = data.get('x')
        self.y          = data.get('y')
        self.s          = data.get('s')
        self.c          = data.get('c')
        self.marker     = data.get('marker')
        self.linewidth  = data.get('linewidth')
        self.cmap       = data.get('cmap')
        self.norm       = data.get('norm')
        self.alpha      = data.get('alpha')
        self.linewidths = data.get('linewidths')


    def plot(self, **kwargs):

        self.formatAxis(**kwargs)

        scatterPlot = self.axis.scatter(x=self.x, y=self.y, s=self.s, c=self.c, marker=self.marker, linewidth=self.linewidth, cmap=self.cmap, norm=self.norm, alpha=self.alpha, linewidths=self.linewidths)

        self.finishFig(**kwargs)

        return self.fig


class LinePlotter(GeneralPlotter):
    """A class used for line plotting"""

    def __init__(self, data, axis=None, options={}, **kwargs):
        
        super().__init__(data=data, axis=axis, **kwargs)

        self.type       = 'scatter'
        self.x          = data.get('x')
        self.y          = data.get('y')
        self.s          = data.get('s')
        self.c          = data.get('c')
        self.marker     = data.get('marker')
        self.linewidth  = data.get('linewidth')
        self.cmap       = data.get('cmap')
        self.norm       = data.get('norm')
        self.alpha      = data.get('alpha')
        self.linewidths = data.get('linewidths')


    def plot(self, **kwargs):

        self.formatAxis(**kwargs)

        scatterPlot = self.axis.scatter(x=self.x, y=self.y, s=self.s, c=self.c, marker=self.marker, linewidth=self.linewidth, cmap=self.cmap, norm=self.norm, alpha=self.alpha, linewidths=self.linewidths)

        self.finishFig(**kwargs)

        return self.fig

    """

    Types of plot:
        line
        scatter
        matrix
        bar
        pie
        

    Plots:
        plot2Dnet                   scatter
        plotConn                    matrix, bar, pie
        plotCSD                         
        plotEPSPAmp                 
        plotfI
        plotLFP
        plotRaster                  scatter
        plotRatePSD                 
        plotRates                   
        plotRateSpectrogram         
        plotRxDConcentration        
        plotShape                   
        plotSpikeHist               
        plotSpikeStats              
        plotSyncs                   
        plotTraces                  line

    """