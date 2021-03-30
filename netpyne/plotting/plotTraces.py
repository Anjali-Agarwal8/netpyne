# Generate a plot of traces

def plotTrace(
    traceData=None,
    axis=None, 
    legend=True, 
    color=None, 
    returnPlotter=False, 
    **kwargs):
    """Function to plot a recorded trace

    """

    pass



def plotTraces(
    tracesData=None, 
    axis=None, 
    legend=True,
    colorList=None,
    returnPlotter=False, 
    **kwargs):
    """Function to plot recorded traces

    """

    from .. import sim

    if tracesData is None:
        tracesData = sim.analysis.prepareTraces(**kwargs)

    print('Plotting recorded cell traces ...')

    dataKeys = ['spkTimes', 'spkInds', 'spkColors', 'cellGids', 'sortedGids', 'numNetStims', 'include', 'timeRange', 'maxSpikes', 'orderBy', 'orderInverse', 'spikeHist', 'syncLines', 'popLabels', 'popLabelRates', 'popColors']

    scatterData = {}
    scatterData['x'] = rasterData['spkTimes']
    scatterData['y'] = rasterData['spkInds']
    scatterData['c'] = rasterData['spkColors']
    scatterData['s'] = 5
    scatterData['marker'] = '|'
    scatterData['linewidth'] = 2
    scatterData['cmap'] = None
    scatterData['norm'] = None
    scatterData['alpha'] = None
    scatterData['linewidths'] = None

    for kwarg in kwargs:
        if kwarg in scatterData:
            scatterData[kwarg] = kwargs[kwarg]

    axisArgs = {}
    axisArgs['title'] = 'Raster Plot of Spiking'
    axisArgs['xlabel'] = 'Time (ms)'
    axisArgs['ylabel'] = 'Cells'


    rasterPlotter = sim.plotting.ScatterPlotter(data=scatterData, axis=axis, **axisArgs, **kwargs)

    rasterPlotter.type = 'raster'

    rasterPlot = rasterPlotter.plot(**axisArgs)

    if legend:
        #rasterPlotter.options['addLegend'] = True
        labels = []
        handles = []
        for ipop, popLabel in enumerate(rasterData['popLabels']):
            labels.append(rasterData['popLabelRates'][ipop] if popRates else popLabel)
            handles.append(mpatches.Rectangle((0,0),1,1,fc=rasterData['popColors'][popLabel]))

        legendKwargs = {}
        legendKwargs['bbox_to_anchor'] = (1.025, 1)
        legendKwargs['loc'] = 2
        legendKwargs['borderaxespad'] = 0.0
        legendKwargs['handlelength'] = 1.0
        legendKwargs['fontsize'] = 'medium'

        rasterPlotter.addLegend(handles, labels, **legendKwargs)

        rightOffset = 0.8 if popRates else 0.9
        maxLabelLen = max([len(label) for label in rasterData['popLabels']])
        rasterPlotter.fig.subplots_adjust(right=(rightOffset-0.012*maxLabelLen))


    return rasterPlotter
