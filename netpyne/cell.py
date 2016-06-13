"""
cell.py 

Contains Cell related classes 

Contributors: salvadordura@gmail.com
"""

from neuron import h # Import NEURON
import framework as f
from copy import deepcopy as dcp


###############################################################################
#
# GENERIC CELL CLASS
#
###############################################################################

class Cell(object):
    ''' Generic 'Cell' class used to instantiate individual neurons based on (Harrison & Sheperd, 2105) '''
    
    def __init__(self, gid, tags):
        self.gid = gid  # global cell id 
        self.tags = tags  # dictionary of cell tags/attributes 
        self.secs = {}  # dict of sections
        self.conns = []  # list of connections
        self.stims = []  # list of stimuli
        
        self.stimtimevecs = None # Create array for storing time vectors
        self.stimweightvecs = None # Create array for holding weight vectors

        self.create()  # create cell 
        self.associateGid() # register cell for this node

    def create(self):
        for prop in f.net.params['cellParams']:  # for each set of cell properties
            conditionsMet = 1
            for (condKey,condVal) in prop['conditions'].iteritems():  # check if all conditions are met
                if self.tags[condKey] != condVal: 
                    conditionsMet = 0
                    break
            if conditionsMet:  # if all conditions are met, set values for this cell
                if 'propList' not in self.tags:
                    self.tags['propList'] = [prop['label']] # create list of property sets
                else:
                    self.tags['propList'].append(prop['label'])  # add label of cell property set to list of property sets for this cell
                if f.cfg['createPyStruct']:
                    self.createPyStruct(prop)
                if f.cfg['createNEURONObj']:
                    self.createNEURONObj(prop)  # add sections, mechanisms, synaptic mechanisms, geometry and topolgy specified by this property set


    def createPyStruct(self, prop):
        # set params for all sections
        for sectName,sectParams in prop['sections'].iteritems(): 
            # create section
            if sectName not in self.secs:
                self.secs[sectName] = {}  # create section dict
            sec = self.secs[sectName]  # pointer to section
            
            # add distributed mechanisms 
            if 'mechs' in sectParams:
                for mechName,mechParams in sectParams['mechs'].iteritems(): 
                    if 'mechs' not in sec:
                        sec['mechs'] = {}
                    if mechName not in sec['mechs']: 
                        sec['mechs'][mechName] = {}  
                    for mechParamName,mechParamValue in mechParams.iteritems():  # add params of the mechanism
                        sec['mechs'][mechName][mechParamName] = mechParamValue

            # add point processes
            if 'pointps' in sectParams:
                for pointpName,pointpParams in sectParams['pointps'].iteritems(): 
                    #if self.tags['cellModel'] == pointpName: # only required if want to allow setting various cell models in same rule
                    if 'pointps' not in sec:
                        sec['pointps'] = {}
                    if pointpName not in sec['pointps']: 
                        sec['pointps'][pointpName] = {}  
                    for pointpParamName,pointpParamValue in pointpParams.iteritems():  # add params of the mechanism
                        sec['pointps'][pointpName][pointpParamName] = pointpParamValue


            # add geometry params 
            if 'geom' in sectParams:
                for geomParamName,geomParamValue in sectParams['geom'].iteritems():  
                    if 'geom' not in sec:
                        sec['geom'] = {}
                    if not type(geomParamValue) in [list, dict]:  # skip any list or dic params
                        sec['geom'][geomParamName] = geomParamValue

            # add 3d geometry
            if 'pt3d' in sectParams['geom']:
                if 'pt3d' not in sec['geom']:  
                    sec['geom']['pt3d'] = []
                for pt3d in sectParams['geom']['pt3d']:
                    sec['geom']['pt3d'].append(pt3d)

            # add topolopgy params
            if 'topol' in sectParams:
                if 'topol' not in sec:
                    sec['topol'] = {}
                for topolParamName,topolParamValue in sectParams['topol'].iteritems(): 
                    sec['topol'][topolParamName] = topolParamValue

            # add other params
            if 'spikeGenLoc' in sectParams:
                sec['spikeGenLoc'] = sectParams['spikeGenLoc']

            if 'vinit' in sectParams:
                sec['vinit'] = sectParams['vinit']

        # add sectionLists
        if prop.get('secLists'):
            self.secLists.update(prop['secLists'])  # diction of section lists



    def initV(self): 
        for sec in self.secs.values():
            if 'vinit' in sec:
                sec['hSection'](0.5).v = sec['vinit']

    def createNEURONObj(self, prop):
        # set params for all sections
        for sectName,sectParams in prop['sections'].iteritems(): 
            # create section
            if sectName not in self.secs:
                self.secs[sectName] = {}  # create sect dict if doesn't exist
            self.secs[sectName]['hSection'] = h.Section(name=sectName)  # create h Section object
            sec = self.secs[sectName]  # pointer to section
            
            # add distributed mechanisms 
            if 'mechs' in sectParams:
                for mechName,mechParams in sectParams['mechs'].iteritems():  
                    if mechName not in sec['mechs']: 
                        sec['mechs'][mechName] = {}
                    sec['hSection'].insert(mechName)
                    for mechParamName,mechParamValue in mechParams.iteritems():  # add params of the mechanism
                        mechParamValueFinal = mechParamValue
                        for iseg,seg in enumerate(sec['hSection']):  # set mech params for each segment
                            if type(mechParamValue) in [list]: 
                                mechParamValueFinal = mechParamValue[iseg]
                            seg.__getattribute__(mechName).__setattr__(mechParamName,mechParamValueFinal)

            # add point processes
            if 'pointps' in sectParams:
                for pointpName,pointpParams in sectParams['pointps'].iteritems(): 
                    #if self.tags['cellModel'] == pointpParams:  # only required if want to allow setting various cell models in same rule
                    if pointpName not in sec['pointps']:
                        sec['pointps'][pointpName] = {} 
                    pointpObj = getattr(h, pointpParams['mod'])
                    loc = pointpParams['loc'] if 'loc' in pointpParams else 0.5  # set location
                    sec['pointps'][pointpName]['hPointp'] = pointpObj(loc, sec = sec['hSection'])  # create h Pointp object (eg. h.Izhi2007b)
                    for pointpParamName,pointpParamValue in pointpParams.iteritems():  # add params of the point process
                        if pointpParamName not in ['mod', 'loc'] and not pointpParamName.startswith('_'):
                            setattr(sec['pointps'][pointpName]['hPointp'], pointpParamName, pointpParamValue)

            # set geometry params 
            if 'geom' in sectParams:
                for geomParamName,geomParamValue in sectParams['geom'].iteritems():  
                    if not type(geomParamValue) in [list, dict]:  # skip any list or dic params
                        setattr(sec['hSection'], geomParamName, geomParamValue)

            # set 3d geometry
            if 'pt3d' in sectParams['geom']:  
                h.pt3dclear(sec=sec['hSection'])
                x = self.tags['x']
                if 'ynorm' in self.tags and 'sizeY' in f.net.params:
                    y = self.tags['ynorm'] * f.net.params['sizeY']/1e3  # y as a func of ynorm and cortical thickness
                else:
                    y = self.tags['y']
                z = self.tags['z']
                for pt3d in sectParams['geom']['pt3d']:
                    h.pt3dadd(x+pt3d[0], y+pt3d[1], z+pt3d[2], pt3d[3], sec=sec['hSection'])

        # set topology 
        for sectName,sectParams in prop['sections'].iteritems():  # iterate sects again for topology (ensures all exist)
            sec = self.secs[sectName]  # pointer to section # pointer to child sec
            if 'topol' in sectParams:
                if sectParams['topol']:
                    sec['hSection'].connect(self.secs[sectParams['topol']['parentSec']]['hSection'], sectParams['topol']['parentX'], sectParams['topol']['childX'])  # make topol connection



    def associateGid (self, threshold = 10.0):
        if self.secs:
            f.pc.set_gid2node(self.gid, f.rank) # this is the key call that assigns cell gid to a particular node
            sec = next((secParams for secName,secParams in self.secs.iteritems() if 'spikeGenLoc' in secParams), None) # check if any section has been specified as spike generator
            if sec:
                loc = sec['spikeGenLoc']  # get location of spike generator within section
            else:
                sec = self.secs['soma'] if 'soma' in self.secs else self.secs[self.secs.keys()[0]]  # use soma if exists, otherwise 1st section
                loc = 0.5
            nc = None
            if 'pointps' in sec:  # if no syns, check if point processes with '_vref' (artificial cell)
                for pointpName, pointpParams in sec['pointps'].iteritems():
                    if '_vref' in pointpParams:
                        nc = h.NetCon(sec['pointps'][pointpName]['hPointp'].__getattribute__('_ref_'+pointpParams['_vref']), None, sec=sec['hSection'])
                        break
            if not nc:  # if still haven't created netcon  
                nc = h.NetCon(sec['hSection'](loc)._ref_v, None, sec=sec['hSection'])
            nc.threshold = threshold
            f.pc.cell(self.gid, nc, 1)  # associate a particular output stream of events
            f.net.gid2lid[self.gid] = len(f.net.lid2gid)
            f.net.lid2gid.append(self.gid) # index = local id; value = global id
            del nc # discard netcon

    def addSynMech (self, label, secName, loc):
        synMechParams = next((params for params in f.net.params['synMechParams'] if params['label'] == label), None)  # get params for this synMech
        sec = self.secs.get(secName, None)
        if synMechParams and sec:  # if both the synMech and the section exist
            if f.cfg['createPyStruct']:
                # add synaptic mechanism to python struct
                if 'synMechs' not in sec:
                    sec['synMechs'] = []
                synMech = next((synMech for synMech in sec['synMechs'] if synMech['label']==label and synMech['loc']==loc), None)
                if not synMech:  # if synMech not in section, then create
                    synMech = {'label': label, 'loc': loc}
                    sec['synMechs'].append(synMech)

            if f.cfg['createNEURONObj']:
                # add synaptic mechanism NEURON objectes 
                if 'synMechs' not in sec:
                    sec['synMechs'] = []
                if not synMech:  # if pointer not created in createPyStruct, then check 
                    synMech = next((synMech for synMech in sec['synMechs'] if synMech['label']==label and synMech['loc']==loc), None)
                if not synMech:  # if still doesnt exist, then create
                    synMech = {}
                    sec['synMechs'].append(synMech)
                if not 'hSyn' in synMech:  # if synMech doesn't have NEURON obj, then create
                    synObj = getattr(h, synMechParams['mod'])
                    synMech['hSyn'] = synObj(loc, sec = sec['hSection'])  # create h Syn object (eg. h.Exp2Syn)
                    for synParamName,synParamValue in synMechParams.iteritems():  # add params of the synaptic mechanism
                        if synParamName not in ['label', 'mod']:
                            setattr(synMech['hSyn'], synParamName, synParamValue)
            return synMech

    def addConn(self, params):
        if params['preGid'] == self.gid:
            print 'Error: attempted to create self-connection on cell gid=%d, section=%s '%(self.gid, params['sec'])
            return  # if self-connection return

        if not params['sec'] or not params['sec'] in self.secs:  # if no section specified or section specified doesnt exist
            if 'soma' in self.secs:  
                params['sec'] = 'soma'  # use 'soma' if exists
            elif self.secs:  
                params['sec'] = self.secs.keys()[0]  # if no 'soma', use first sectiona available
                for secName, secParams in self.secs.iteritems():   # replace with first section that includes synaptic mechanism
                    if 'synMechs' in secParams:
                        if secParams['synMechs']:
                            params['sec'] = secName
                            break
            else:  
                print 'Error: no Section available on cell gid=%d to add connection'%(self.gid)
                return  # if no Sections available print error and exit
        sec = self.secs[params['sec']]

        weightIndex = 0  # set default weight matrix index
        if not 'loc' in params: params['loc'] = 0.5  # default synMech location    

        pointp = None
        if 'pointps' in self.secs[params['sec']]:  #  check if point processes with '_vref' (artificial cell)
            for pointpName, pointpParams in self.secs[params['sec']]['pointps'].iteritems():
                if '_vref' in pointpParams:  # if includes vref param means doesn't use Section v or synaptic mechanisms
                    pointp = pointpName
                    if '_synList' in pointpParams:
                        if params['synMech'] in pointpParams['_synList']: 
                            weightIndex = pointpParams['_synList'].index(params['synMech'])  # udpate weight index based pointp synList

        if not pointp: # not a point process
            if params['synMech']: # if desired synaptic mechanism specified in conn params
                synMech = self.addSynMech (params['synMech'], params['sec'], params['loc'])  # add synaptic mechanism to section (if already exists won't be added)
            elif f.net.params['synMechParams']:  # if no synMech specified, but some synMech params defined
                synLabel = f.net.params['synMechParams'][0]['label']  # select first synMech from net params and add syn
                params['synMech'] = synLabel
                synMech = self.addSynMech(params['synMech'], params['sec'], params['loc'])  # add synapse
            else: # if no synaptic mechanism specified and no synMech params available 
                print 'Error: no synaptic mechanisms available to add stim on cell gid=%d, section=%s '%(self.gid, params['sec'])
                return  # if no Synapse available print error and exit

        self.conns.append(params)
        if pointp:
            postTarget = sec['pointps'][pointp]['hPointp'] #  local point neuron
        else:
            postTarget = synMech['hSyn'] # local synaptic mechanism
        netcon = f.pc.gid_connect(params['preGid'], postTarget) # create Netcon between global gid and target
        netcon.weight[weightIndex] = f.net.params['scaleConnWeight']*params['weight']  # set Netcon weight
        netcon.delay = params['delay']  # set Netcon delay
        netcon.threshold = params['threshold']  # set Netcon delay
        self.conns[-1]['hNetcon'] = netcon  # add netcon object to dict in conns list
        if f.cfg['verbose']: print('Created connection preGid=%d, postGid=%d, sec=%s, syn=%s, weight=%.4g, delay=%.1f'%
            (params['preGid'], self.gid, params['sec'], params['synMech'], f.net.params['scaleConnWeight']*params['weight'], params['delay']))

        plasticity = params.get('plasticity')
        if plasticity:  # add plasticity
            try:
                plastSection = h.Section()
                plastMech = getattr(h, plasticity['mech'], None)(0, sec=plastSection)  # create plasticity mechanism (eg. h.STDP)
                for plastParamName,plastParamValue in plasticity['params'].iteritems():  # add params of the plasticity mechanism
                    setattr(plastMech, plastParamName, plastParamValue)
                if plasticity['mech'] == 'STDP':  # specific implementation steps required for the STDP mech
                    precon = f.pc.gid_connect(params['preGid'], plastMech); precon.weight[0] = 1 # Send presynaptic spikes to the STDP adjuster
                    pstcon = f.pc.gid_connect(self.gid, plastMech); pstcon.weight[0] = -1 # Send postsynaptic spikes to the STDP adjuster
                    h.setpointer(netcon._ref_weight[weightIndex], 'synweight', plastMech) # Associate the STDP adjuster with this weight
                    self.conns[-1]['hPlastSection'] = plastSection
                    self.conns[-1]['hSTDP']         = plastMech
                    self.conns[-1]['hSTDPprecon']   = precon
                    self.conns[-1]['hSTDPpstcon']   = pstcon
                    self.conns[-1]['STDPdata']      = {'preGid':params['preGid'], 'postGid': self.gid, 'receptor': weightIndex} # Not used; FYI only; store here just so it's all in one place
                    if f.cfg['verbose']: print('  Added STDP plasticity to synaptic mechanism')
            except:
                print 'Error: exception when adding plasticity using %s mechanism' % (plasticity['mech'])



    def addNetStim (self, params):
        if not params['sec'] or not params['sec'] in self.secs:  # if no section specified or section specified doesnt exist
            if 'soma' in self.secs:  
                params['sec'] = 'soma'  # use 'soma' if exists
            elif self.secs:  
                params['sec'] = self.secs.keys()[0]  # if no 'soma', use first sectiona available
                for secName, secParams in self.secs.iteritems():              # replace with first section that includes synaptic mechanism
                    if 'synMechs' in secParams:
                        if secParams['synMechs']:
                            params['sec'] = secName
                            break
            else:  
                print 'Error: no Section available on cell gid=%d to add connection'%(self.gid)
                return  # if no Sections available print error and exit
        sec = self.secs[params['sec']]

        weightIndex = 0  # set default weight matrix index
        if not 'loc' in params: params['loc'] = 0.5  # default synMech location 
 
        pointp = None
        if 'pointps' in sec:  # check if point processes (artificial cell)
            for pointpName, pointpParams in sec['pointps'].iteritems():
                  if '_vref' in pointpParams:  # if includes vref param means doesn't use Section v or synaptic mechanisms
                    pointp = pointpName
                    if '_synList' in pointpParams:
                        if params['synMech'] in pointpParams['_synList']: 
                            weightIndex = pointpParams['_synList'].index(params['synMech'])  # udpate weight index based pointp synList

        if not pointp: # not a point process
            if params['synMech']: # if desired synaptic mechanism specified in conn params
                synMech = self.addSynMech (params['synMech'], params['sec'], params['loc'])  # add synaptic mechanism to section (won't be added if exists)
            elif f.net.params['synMechParams']:  # if some synMech params defined
                synLabel = f.net.params['synMechParams'][0]['label']  # select first synMech from net params and add syn
                params['synMech'] = synLabel
                synMech = self.addSynMech (params['synMech'], params['sec'], params['loc'])  # add synapse
            else: # if no synaptic mechanism specified and no synMech params available 
                print 'Error: no synaptic mechanisms available to add stim on cell gid=%d, section=%s '%(self.gid, params['sec'])
                return  # if no Synapse available print error and exit

        self.stims.append(params)  # add new stim to Cell object

        if params['source'] == 'random':
            rand = h.Random()
            #rand.Random123(self.gid,self.gid*2)
            #rand.negexp(1)
            self.stims[-1]['hRandom'] = rand  # add netcon object to dict in conns list

            if isinstance(params['rate'], str):
                if params['rate'] == 'variable':
                    try:
                        netstim = h.NSLOC()
                        netstim.interval = 0.1**-1*1e3 # inverse of the frequency and then convert from Hz^-1 to ms (set very low)
                        netstim.noise = params['noise']
                    except:
                        print 'Error: tried to create variable rate NetStim but NSLOC mechanism not available'
                else:
                    print 'Error: Unknown stimulation rate type: %s'%(h.params['rate'])
            else:
                netstim = h.NetStim()
                netstim.interval = params['rate']**-1*1e3 # inverse of the frequency and then convert from Hz^-1 to ms
                netstim.noise = params['noise']
                netstim.start = params['start']
            netstim.noiseFromRandom(rand)  # use random number generator
            netstim.number = params['number']
            self.stims[-1]['hNetStim'] = netstim  # add netstim object to dict in stim list

        if pointp:
            netcon = h.NetCon(netstim, sec['pointps'][pointp]['hPointp'])  # create Netcon between global gid and local point neuron
        else:
            netcon = h.NetCon(netstim, synMech['hSyn']) # create Netcon between global gid and local synaptic mechanism
        netcon.weight[weightIndex] = params['weight']  # set Netcon weight
        
        
        
        # Custom code for time-dependently shaping the weight of a NetCon corresponding to a NetStim.
        # Default arguments used in practice are actually specified later.
        def shapeStim(isi=1, variation=0, width=0.05, weight=10, start=0, finish=1, stimshape='gaussian'):
            from pylab import r_, convolve, shape, exp, zeros, hstack, array, rand
            
            # Create event times
            timeres = 0.001 # Time resolution = 1 ms = 500 Hz (DJK to CK: 500...?)
            pulselength = 10 # Length of pulse in units of width
#            lowthreshold = 1e-6 # Below this level, weights may as well be zero
            currenttime = 0
            timewindow = finish-start
            allpts = int(timewindow/timeres)
            output = []
            while currenttime<timewindow:
                # Note: The timeres/2 subtraction acts as an eps to avoid later int rounding errors.
                if currenttime>=0 and currenttime<timewindow-timeres/2: output.append(currenttime)
                currenttime = currenttime+isi+variation*(rand()-0.5)
            
            # Create single pulse
            npts = pulselength*width/timeres
            x = (r_[0:npts]-npts/2+1)*timeres
            if stimshape=='gaussian': 
                pulse = exp(-2*(2*x/width-1)**2) # Offset by 2 standard deviations from start
                pulse = pulse/max(pulse)
            elif stimshape=='square': 
                pulse = zeros(shape(x))
                pulse[int(npts/2):int(npts/2)+int(width/timeres)] = 1 # Start exactly on time
            else:
                raise Exception('Stimulus shape "%s" not recognized' % stimshape)
            
            # Create full stimulus
            events = zeros((allpts))
            events[array(array(output)/timeres,dtype=int)] = 1
            fulloutput = convolve(events,pulse,mode='full')*weight # Calculate the convolved input signal, scaled by rate
            fulloutput = fulloutput[npts/2-1:-npts/2]   # Slices out where the convolved pulse train extends before and after sequence of allpts.
            fulltime = (r_[0:allpts]*timeres+start)*1e3 # Create time vector and convert to ms
            
#            # Slim down weight/time/event vectors by cutting repeated weights
#            fulloutput = [j if j > lowthreshold else 0.0 for j in fulloutput]
#            fo = dcp(fulloutput)
#            events = [events[k[0]] for k in zip(xrange(len(fo)),fo,[None]+fo) if k[1] != k[2]]
#            fulltime = [fulltime[k[0]] for k in zip(xrange(len(fo)),fo,[None]+fo) if k[1] != k[2]]
#            fulloutput = [fulloutput[k[0]] for k in zip(xrange(len(fo)),fo,[None]+fo) if k[1] != k[2]]
#            print fulloutput
#            print fulltime
#            print events
            
            fulltime = hstack((0,fulltime,fulltime[-1]+timeres*1e3)) # Create "bookends" so always starts and finishes at zero
            fulloutput = hstack((0,fulloutput,0)) # Set weight to zero at either end of the stimulus period
            events = hstack((0,events,0)) # Ditto
            stimvecs = dcp([fulltime, fulloutput, events]) # Combine vectors into a matrix           
            
            return stimvecs        

        # Time-dependently shaping connection weights of NetStim...
        if 'shape' in params and params['shape']:
            
            temptimevecs = []
            tempweightvecs = []
            
            # Default shape
            pulsetype = params['shape']['pulseType'] if 'pulseType' in params['shape'] else 'square'
            pulsewidth = params['shape']['pulseWidth'] if 'pulseWidth' in params['shape'] else 100.0
            pulseperiod = params['shape']['pulsePeriod'] if 'pulsePeriod' in params['shape'] else 100.0
            
            # Determine on-off switching time pairs for stimulus, where default is always on
            if 'switchOnOff' not in params['shape']:
                switchtimes = [0, f.cfg['duration']]
            else:
                if not params['shape']['switchOnOff'] == sorted(params['shape']['switchOnOff']):
                    raise Exception('On-off switching times for a particular stimulus are not monotonic')   
                switchtimes = dcp(params['shape']['switchOnOff'])
                switchtimes.append(f.cfg['duration'])
            
            switchiter = iter(switchtimes)
            switchpairs = zip(switchiter,switchiter)
            for pair in switchpairs:
                # Note: Cliff's makestim code is in seconds, so conversions from ms to s occurs in the args.
                stimvecs = shapeStim(width=float(pulsewidth)/1000.0, isi=float(pulseperiod)/1000.0, weight=params['weight'], start=float(pair[0])/1000.0, finish=float(pair[1])/1000.0, stimshape=pulsetype)
                temptimevecs.extend(stimvecs[0])
                tempweightvecs.extend(stimvecs[1])
            
            self.stimtimevecs = h.Vector().from_python(temptimevecs)
            self.stimweightvecs = h.Vector().from_python(tempweightvecs)    
            self.stimweightvecs.play(netcon._ref_weight[weightIndex], self.stimtimevecs) # Play shaped weights into stimulus connection's weighting   


        
        netcon.delay = params['delay']  # set Netcon delay
        netcon.threshold = params['threshold']  # set Netcon delay
        self.stims[-1]['hNetcon'] = netcon  # add netcon object to dict in conns list
        self.stims[-1]['weightIndex'] = weightIndex
        if f.cfg['verbose']: print('Created NetStim prePop=%s, postGid=%d, sec=%s, syn=%s, weight=%.4g, delay=%.4g'%
            (params['popLabel'], self.gid, params['sec'], params['synMech'], params['weight'], params['delay']))


    def addIClamp (self, params):
        if not params['sec'] or not params['sec'] in self.secs:  # if no section specified or section specified doesnt exist
            if 'soma' in self.secs:  
                params['sec'] = 'soma'  # use 'soma' if exists
            elif self.secs:  
                params['sec'] = self.secs.keys()[0]  # if no 'soma', use first sectiona available
                for secName, secParams in self.secs.iteritems():              # replace with first section that includes synaptic mechanism
                    if 'synMechs' in secParams:
                        if secParams['synMechs']:
                            params['sec'] = secName
                            break
            else:  
                print 'Error: no Section available on cell gid=%d to add connection'%(self.gid)
                return  # if no Sections available print error and exit
        sec = self.secs[params['sec']]
        
        if not 'loc' in params: params['loc'] = 0.5  # default synMech location 

        iclamp = h.IClamp(sec['hSection'](params['loc']))  # create Netcon between global gid and local point neuron
        iclamp.amp = params['amp']
        iclamp.delay = params['delay']
        iclamp.dur = params['dur']

        self.stims.append(params)
        self.stims[-1]['hIClamp'] = iclamp  # add netcon object to dict in conns list
        if f.cfg['verbose']: print('Created IClamp postGid=%d, sec=%s, loc=%.4g, amp=%.4g, delay=%.4g, dur=%.4g'%
            (self.gid, params['sec'], params['loc'], params['amp'], params['delay'], params['dur']))


    def recordTraces (self):
        # set up voltagse recording; recdict will be taken from global context
        for key, params in f.cfg['recordTraces'].iteritems():
            ptr = None
            try: 
                if 'loc' in params:
                    if 'mech' in params:  # eg. soma(0.5).hh._ref_gna
                        ptr = self.secs[params['sec']]['hSection'](params['loc']).__getattribute__(params['mech']).__getattribute__('_ref_'+params['var'])
                    elif 'synMech' in params:  # eg. soma(0.5).AMPA._ref_g
                        sec = self.secs[params['sec']]
                        synMech = next((synMech for synMech in sec['synMechs'] if synMech['label']==params['synMech'] and synMech['loc']==params['loc']), None)
                        ptr = synMech['hSyn'].__getattribute__('_ref_'+params['var'])
                    else:  # eg. soma(0.5)._ref_v
                        ptr = self.secs[params['sec']]['hSection'](params['loc']).__getattribute__('_ref_'+params['var'])
                else:
                    if 'pointp' in params: # eg. soma.izh._ref_u
                        #print self.secs[params['sec']]
                        if params['pointp'] in self.secs[params['sec']]['pointps']:
                            ptr = self.secs[params['sec']]['pointps'][params['pointp']]['hPointp'].__getattribute__('_ref_'+params['var'])

                if ptr:  # if pointer has been created, then setup recording
                    f.simData[key]['cell_'+str(self.gid)] = h.Vector(f.cfg['duration']/f.cfg['recordStep']+1).resize(0)
                    f.simData[key]['cell_'+str(self.gid)].record(ptr, f.cfg['recordStep'])
                    if f.cfg['verbose']: print 'Recording ', key, 'from cell ', self.gid
            except:
                if f.cfg['verbose']: print 'Cannot record ', key, 'from cell ', self.gid


    def recordStimSpikes (self):
        f.simData['stims'].update({'cell_'+str(self.gid): {}})
        for stim in self.stims:
            if 'hNetcon' in stim:
                stimSpikeVecs = h.Vector() # initialize vector to store 
                stim['hNetcon'].record(stimSpikeVecs)
                f.simData['stims']['cell_'+str(self.gid)].update({stim['popLabel']: stimSpikeVecs})


    def __getstate__(self): 
        ''' Removes non-picklable h objects so can be pickled and sent via py_alltoall'''
        odict = self.__dict__.copy() # copy the dict since we change it
        odict = f.sim.copyReplaceItemObj(odict, keystart='h', newval=None)  # replace h objects with None so can be pickled
        return odict



###############################################################################
#
# POINT NEURON CLASS (v not from Section)
#
###############################################################################

class PointNeuron(Cell):
    '''
    Point Neuron that doesn't use v from Section - TO DO
    '''
    pass

