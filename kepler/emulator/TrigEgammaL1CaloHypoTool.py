
__all__ = ['TrigEgammaL1CaloHypoTool']

from Gaugi import Algorithm
from Gaugi import StatusCode
from Gaugi import ToolSvc
from Gaugi import declareProperty
from Gaugi.macros import *

from kepler.menu import treat_trigger_dict_type
from kepler.emulator import Accept

import math
import re

#
# Hypo tool
#
class TrigEgammaL1CaloHypoTool( Algorithm ):

  #
  # Constructor
  #
  def __init__(self, name, **kw):
    
    Algorithm.__init__(self, name)
    
    #
    # L1 configuration default parameters
    #

    declareProperty( self, kw, "WPNames"        , ['Tight','Medium','Loose']        )
    declareProperty( self, kw, "HadCoreCutMin"  , [ 1.0   ,  1.0  ,  1.0  ,  1.0  ] )
    declareProperty( self, kw, "HadCoreCutOff"  , [-0.2   , -0,2  , -0.2  , -0.2  ] )
    declareProperty( self, kw, "HadCoreSlope"   , [ 1/23. ,  1/23.,  1/23.,  1/23.] )
    declareProperty( self, kw, "EmIsolCutMin"   , [ 2.0   ,  1.0  ,  1.0  ,  1.5  ] )
    declareProperty( self, kw, "EmIsolCutOff"   , [-1.8   , -2.6  , -2.0  , -1.8  ] )
    declareProperty( self, kw, "EmIsolSlope"    , [ 1/8.  ,  1/8. ,  1/8. ,  1/8. ] )
    declareProperty( self, kw, "IsolCutMax"     , 50                                )
    declareProperty( self, kw, "L1Item"         , 'L1_EM3'                          )

 

  #
  # Initialize method
  #
  def initialize(self):
 
    self.init_lock()
    return StatusCode.SUCCESS


  #
  # Finalize method
  #
  def finalize(self):
    self.fina_lock()
    return StatusCode.SUCCESS


  #
  # Accept method
  #
  def accept( self, context ):

    l1 = context.getHandler( "HLT__EmTauRoIContainer" )
    passed = self.emulate( l1, self.L1Item )
    return Accept( self.name(), [ ("Pass", passed ) ] )


  #
  # L1 emulation
  #
  def emulate(self, l1, L1Item):
  
   
    l1type      = self.L1Item.replace('L1_EM','') # L1_EM3 to EM3
    l1threshold = float(re.findall('\d+', l1type)[0])


    c=0
    if(self.WPNames[0] in l1type):  c=1 # Tightl
    if(self.WPNames[1] in l1type):  c=2 # Medium
    if(self.WPNames[2] in l1type):  c=3 # Loose

    hadCoreCutMin  = self.HadCoreCutMin[c]
    hadCoreCutOff  = self.HadCoreCutOff[c]
    hadCoreSlope   = self.HadCoreSlope[c]
    emIsolCutMin   = self.EmIsolCutMin[c]
    emIsolCutOff   = self.EmIsolCutOff[c]
    emIsolCutSlope = self.EmIsolSlope[c]
   

    emE = 0.0
    emIsol = 0.0
    hadCore = 0.0
    eta = 0.0
    
    emE     = l1.emClus()/1.e3   # Cluster energy
    eta     = l1.eta()           # eta
    hadCore = l1.hadCore()/1.e3  # Hadronic core energy
    emIsol  = l1.emIsol()/1.e3   # EM Isolation energy
    
    if ('H' in l1type):
      MSG_DEBUG(self, "L1 (H) CUT")
      if not self.isolationL1(hadCoreCutMin,hadCoreCutOff,hadCoreSlope,hadCore,emE):
        MSG_DEBUG(self, "rejected")
        return False
      MSG_DEBUG(self, "accepted")
    
    if ('I' in l1type):
      MSG_DEBUG(self, "L1 (I) CUT")
      if not self.isolationL1(emIsolCutMin,emIsolCutOff,emIsolCutSlope,emIsol,emE):
        MSG_DEBUG(self, "rejected")
        return False
      MSG_DEBUG(self, "accepted")
    
    
    if ('V' in l1type):
      MSG_DEBUG(self, "L1 (V) CUT")
      if not self.variableEtL1(l1type,emE,eta):
        MSG_DEBUG(self, "rejected")
        return False
      MSG_DEBUG(self, "accepted")
    
    # add new method for this also
    if  (emE <= l1threshold): # // this cut is confirmed to be <=
      return False

    return True

     

  #//!==========================================================================
  #// (H) and (I) Hadronic core and electromagnetic isolation
  def isolationL1(self, min_, offset, slope, energy, emE):
  	
    if (emE > self.IsolCutMax):
      MSG_DEBUG(self, "L1 Isolation skipped, ET > Maximum isolation")
      return True
        
    isolation = offset + emE*slope
    if (isolation < min_): isolation = min_
    
    value = False if (energy > isolation) else True
    #MSG_DEBUG(self,  ("L1 Isolation ET = %1.3f ISOLATION CUT %1.3f")%(energy,isolation) )
    return value
  
  #//!==========================================================================
  #// (V) Variable Et cut
  def variableEtL1(self, L1item, l1energy, l1eta):
    cut = self.emulationL1V(L1item,l1eta)
    energy = l1energy
    # if (energy <= cut) return false;
    value = False if (energy <= cut) else True
    return value
  
  
  #//!==========================================================================
  #// Eta dependant cuts for (V)
  def emulationL1V(self, L1item, l1eta):
    # Values updated from TriggerMenu-00-13-26
    # Now they all look symmetric in negative and positive eta
    # look that in general que can remove the first region since it is the defaul value
    cut=0.0
    # float eta = fabs((int)l1eta*10);
    eta = math.fabs(l1eta)

    if (L1item == "50V"):
      if (eta >= 0.8 and eta < 1.2): cut = 51.0
      elif (eta >= 1.2 and eta < 1.6): cut = 50.0
      elif (eta >= 1.6 and eta < 2.0): cut = 51.0
      else: cut = 52
    
    elif (L1item=="8VH"):
      if   (eta > 0.8 and eta <= 1.1): cut = 7.0
      elif (eta > 1.1 and eta <= 1.4): cut = 6.0
      elif (eta > 1.4 and eta <= 1.5): cut = 5.0
      elif (eta > 1.5 and eta <= 1.8): cut = 7.0
      elif (eta > 1.8 and eta <= 2.5): cut = 8.0
      else: cut = 9.0
    
    elif (L1item=="10VH"):
      if   (eta > 0.8 and eta <= 1.1): cut = 9.0
      elif (eta > 1.1 and eta <= 1.4): cut = 8.0
      elif (eta > 1.4 and eta <= 1.5): cut = 7.0
      elif (eta > 1.5 and eta <= 1.8): cut = 9.0
      elif (eta > 1.8 and eta <= 2.5): cut = 10.0
      else: cut = 11.0
    
    elif (L1item=="13VH"):
      if   (eta > 0.7 and eta <= 0.9): cut = 14.0
      elif (eta > 0.9 and eta <= 1.2): cut = 13.0
      elif (eta > 1.2 and eta <= 1.4): cut = 12.0
      elif (eta > 1.4 and eta <= 1.5): cut = 11.0
      elif (eta > 1.5 and eta <= 1.7): cut = 13.0
      elif (eta > 1.7 and eta <= 2.5): cut = 14.0
      else: cut = 15.0
    
    elif (L1item=="15VH"):
      if   (eta > 0.7 and eta <= 0.9): cut = 16.0
      elif (eta > 0.9 and eta <= 1.2): cut = 15.0
      elif (eta > 1.2 and eta <= 1.4): cut = 14.0
      elif (eta > 1.4 and eta <= 1.5): cut = 13.0
      elif (eta > 1.5 and eta <= 1.7): cut = 15.0
      elif (eta > 1.7 and eta <= 2.5): cut = 16.0
      else: cut = 17.0
    
    elif (L1item == "18VH"):
      if   (eta > 0.7 and eta <= 0.8): cut = 19.0
      elif (eta > 0.8 and eta <= 1.1): cut = 18.0
      elif (eta > 1.1 and eta <= 1.3): cut = 17.0
      elif (eta > 1.3 and eta <= 1.4): cut = 16.0
      elif (eta > 1.4 and eta <= 1.5): cut = 15.0
      elif (eta > 1.5 and eta <= 1.7): cut = 17.0
      elif (eta > 1.7 and eta <= 2.5): cut = 19.0
      else: cut = 20.0
    
    elif (L1item == "20VH"):
      if   (eta > 0.7 and eta <= 0.8): cut = 21.0
      elif (eta > 0.8 and eta <= 1.1): cut = 20.0
      elif (eta > 1.1 and eta <= 1.3): cut = 19.0
      elif (eta > 1.3 and eta <= 1.4): cut = 18.0
      elif (eta > 1.4 and eta <= 1.5): cut = 17.0
      elif (eta > 1.5 and eta <= 1.7): cut = 19.0
      elif (eta > 1.7 and eta <= 2.5): cut = 21.0
      else: cut = 22.0
    
    elif (L1item == "20VHI"): # Same as 20VH
      if   (eta > 0.7 and eta <= 0.8): cut = 21.0
      elif (eta > 0.8 and eta <= 1.1): cut = 20.0
      elif (eta > 1.1 and eta <= 1.3): cut = 19.0
      elif (eta > 1.3 and eta <= 1.4): cut = 18.0
      elif (eta > 1.4 and eta <= 1.5): cut = 17.0
      elif (eta > 1.5 and eta <= 1.7): cut = 19.0
      elif (eta > 1.7 and eta <= 2.5): cut = 21.0
      else: cut = 22.0
    
    elif (L1item == "22VHI"):
      if   (eta > 0.7 and eta <= 0.8): cut = 23.0
      elif (eta > 0.8 and eta <= 1.1): cut = 22.0
      elif (eta > 1.1 and eta <= 1.3): cut = 21.0
      elif (eta > 1.3 and eta <= 1.4): cut = 20.0
      elif (eta > 1.4 and eta <= 1.5): cut = 19.0
      elif (eta > 1.5 and eta <= 1.7): cut = 21.0
      elif (eta > 1.7 and eta <= 2.5): cut = 23.0
      else: cut = 24.0


    return cut





def configure_from_trigger( trigger ):

  d = treat_trigger_dict_type( trigger )
  l1item = d['L1Seed']
  name = 'Hypo__L1Calo__' + trigger

  emulator = ToolSvc.retrieve("Emulator")
  if not emulator.isValid(name):
    configure( name, l1item )
    emulator+=hypo

  return name




#
# Configure the hypo tool using the trigger chain name
#
def configure( name, l1item ):


  # L1 configuration parameters
  hypo = TrigEgammaL1CaloHypoTool( name,
                                   WPNames        =  ['Tight','Medium','Loose'], # must be: ["T","M","L"] (Tight,Medium and Loose)
                                   HadCoreCutMin  =  [ 1.0   ,  1.0  ,  1.0  ,  1.0  ], # must be a list with for values: (default,tight,medium and loose)
                                   HadCoreCutOff  =  [-0.2   , -0,2  , -0.2  , -0.2  ],
                                   HadCoreSlope 	 = [ 1/23. ,  1/23.,  1/23.,  1/23.],
                                   EmIsolCutMin   = [ 2.0   ,  1.0  ,  1.0  ,  1.5  ],
                                   EmIsolCutOff   = [-1.8   , -2.6  , -2.0  , -1.8  ],
                                   EmIsolSlope    = [ 1/8.  ,  1/8. ,  1/8. ,  1/8. ],
                                   IsolCutMax     = 50,
                                   L1Item         = l1item )

  return hypo

