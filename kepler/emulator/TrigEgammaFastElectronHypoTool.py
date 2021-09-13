
__all__ = ['TrigEgammaFastElectronHypoTool']


from Gaugi.messenger.macros import *
from Gaugi import Algorithm
from Gaugi import StatusCode
from Gaugi import ToolSvc
from Gaugi import GeV
from Gaugi import declareProperty

from kepler.menu import treat_trigger_dict_type
from kepler.emulator import Accept


#
# Hypo tool
#
class TrigEgammaFastElectronHypoTool( Algorithm ):


  #
  # Constructor
  #
  def __init__(self, name, **kw):

    Algorithm.__init__(self, name)

    declareProperty( self, kw, "EtCut"               ,   0      )
    declareProperty( self, kw, "TrackPt"             ,   0      )
    declareProperty( self, kw, "CaloTrackdETA"       ,   0.2    )
    declareProperty( self, kw, "CaloTrackdPHI"       ,   0.3    )
    declareProperty( self, kw, "CaloTrackdEoverPLow" ,   0      )
    declareProperty( self, kw, "CaloTrackdEoverPHigh",   999    )
    declareProperty( self, kw, "TRTRatio"            ,   -999   )


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

    elCont = context.getHandler( "HLT__TrigElectronContainer" )
    current = elCont.getPos()

    bitAccept = [False for _ in range(elCont.size())]

    for el in elCont:
      # Retrieve all quantities
      dPhiCalo    = el.trkClusDphi()
      dEtaCalo    = el.trkClusDeta()
      pTcalo      = el.pt()
      eTOverPt    = el.etOverPt()
      NTRHits     = el.numberOfTRTHits()
      NStrawHits  = el.numberOfTRTHiThresholdHits()
      TRTHitRatio = 1e10 if NStrawHits==0 else NTRHits/float(NStrawHits)
      # apply cuts

      passed = False

      if (pTcalo > self.TrackPt):
        if (dEtaCalo < self.CaloTrackdETA):
          if (dPhiCalo < self.CaloTrackdPHI):
            if(eTOverPt >  self.CaloTrackdEoverPLow ):
              if ( eTOverPt < self.CaloTrackdEoverPHigh ):
                if (TRTHitRatio > self.TRTRatio):
                  # TrigElectron passed all cuts: set flags
                  passed = True
                  MSG_DEBUG( self,  "Event accepted !" )
                #TRTHitRatio
              #etOverPt
            #dphi
          #deta
        #pt
      #apply cuts

      bitAccept[el.getPos()] = passed

    # Loop over electrons

    elCont.setPos( current )
    # got this far => passed!
    passed = any( bitAccept )
    return Accept( self.name(), [("Pass", passed)] )







def configure_from_trigger( trigger ):

  d = treat_trigger_dict_type( trigger )
  etthr = d['etthr']
  name = 'Hypo__FastElectron__' + trigger

  emulator = ToolSvc.retrieve("Emulator")
  if not emulator.isValid(name):
    hypo = configure( name, etthr )
    emulator+=hypo
  return name


#
# Configure hypo tool from trigger name
#
def configure( name, etthr ):

  from kepler.emulator import TrigEgammaFastElectronHypoTool
  hypo = TrigEgammaFastElectronHypoTool(name,
                                      EtCut                =   (etthr - 3)*GeV,
                                      TrackPt              =   1*GeV,
                                      CaloTrackdETA        =   0.2  ,
                                      CaloTrackdPHI        =   0.3  ,
                                      CaloTrackdEoverPLow  =   0    ,
                                      CaloTrackdEoverPHigh =   999  ,
                                      TRTRatio             =   -999 )
  if etthr < 15:
    hypo.TrackPt = 1*GeV
  elif etthr >= 15 and etthr < 20:
    hypo.TrackPt = 2*GeV
  elif etthr >=20 and etthr < 50:
    hypo.TrackPt = 3*GeV
  else:
    hypo.TrackPt = 5*GeV
    hypo.CaloTrackdETA = 999
    hypo.CaloTrackdPHI = 999


  return hypo



