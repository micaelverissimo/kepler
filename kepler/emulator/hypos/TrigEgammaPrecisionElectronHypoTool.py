
__all__ = ['TrigEgammaPrecisionElectronHypoTool']

from Gaugi.macros import *
from Gaugi import StatusCode
from Gaugi import Algorithm
from Gaugi import ToolSvc
from Gaugi import declareProperty

from kepler.emulator import Accept
from kepler.menu import treat_trigger_dict_type

from kepler.events import IsolationType

#
# Hypo tool
#
class TrigEgammaPrecisionElectronHypoTool( Algorithm ):


  #
  # Constructor
  #
  def __init__(self, name, **kw):

    Algorithm.__init__(self, name)

    declareProperty( self, kw, "Branch"              , 'trig_EF_el_lhtight'     )
    declareProperty( self, kw, "EtConeCut"           , [-1, -1, -1, -1, -1, -1] )
    declareProperty( self, kw, "PtConeCut"           , [-1, -1, -1, -1, -1, -1] )
    declareProperty( self, kw, "RelEtConeCut"        , [-1, -1, -1, -1, -1, -1] )
    declareProperty( self, kw, "RelPtConeCut"        , [-1, -1, -1, -1, -1, -1] )
    declareProperty( self, kw, "DoIsolation"         , False                    )
    declareProperty( self, kw, "UseClusETforCaloIso" , True                     )
    declareProperty( self, kw, "UseClusETforTrackIso", True                     )


  #
  # Initialize method
  #
  def initialize(self):
    self.init_lock()
    return StatusCode.SUCCESS


  #
  # Accept method
  # 
  def accept(self, context):

    elCont = context.getHandler("HLT__ElectronContainer")
    current = elCont.getPos()
    bitAccept = [False for _ in range(elCont.size())]


    if not elCont.checkBody( self.Branch ):
      MSG_FATAL( self, "The branch %s is not found into the HLT electron body.", self.branch )

    for el in elCont:
      passed = True if el.accept(self.Branch) else False
      if passed and self.DoIsolation:
        passed = self.isolation(el) # overwrite decision
      bitAccept[el.getPos()] = passed

   
    elCont.setPos( current )
    # got this far => passed!
    passed = any( bitAccept )

    return Accept( self.name(), [ ("Pass", passed) ] )


  #
  # Finalize method
  #
  def finalize(self):
    self.fina_lock()
    return StatusCode.SUCCESS


  #
  # Apply isolation cuts
  #
  def isolation(self, el):

    etcone20 = el.isolationValue( IsolationType.etcone20 )
    etcone30 = el.isolationValue( IsolationType.etcone30 )
    etcone40 = el.isolationValue( IsolationType.etcone40 )
    ptcone20 = el.isolationValue( IsolationType.ptcone20 )
    ptcone30 = el.isolationValue( IsolationType.ptcone30 )
    ptcone40 = el.isolationValue( IsolationType.ptcone40 )
    ptvarcone20 = el.isolationValue( IsolationType.ptvarcone20 )
    ptvarcone30 = el.isolationValue( IsolationType.ptvarcone30 )
    ptvarcone40 = el.isolationValue( IsolationType.ptvarcone40 )

    etcone = [
              etcone20,
              etcone30,
              etcone40,
             ]
    
    ptcone = [
              ptcone20,
              ptcone30,
              ptcone40,
              ptvarcone20,
              ptvarcone30,
              ptvarcone40
              ]

    el_clus_pt     = el.caloCluster().et()
    el_trk_pt      = el.trackParticle().pt() if el.trackParticle() else -999
    caloIso_ele_pt = el_clus_pt if self.UseClusETforCaloIso else el_trk_pt
    trkIso_ele_pt  = el_clus_pt if self.UseClusETforTrackIso else el_trk_pt

    absEtConeCut_ispassed = True
    # Cut on Absolute Calo Isolation
    for idx, value in enumerate( etcone ):
      if self.EtConeCut[idx] > 0 and value > self.EtConeCut[idx]:
        absEtConeCut_ispassed = False
        break
    if not absEtConeCut_ispassed:
      return False
    
    absPtConeCut_ispassed = True
    # Cut on Absolute Track Isolation
    for idx, value in enumerate( ptcone ):
      if self.PtConeCut[idx] > 0 and value > self.PtConeCut[idx]:
        absPtConeCut_ispassed = False
        break
    if not absPtConeCut_ispassed:
      return False

    relEtcone = []
    # Fill rel et cone
    for idx, value in enumerate( etcone ):
      if caloIso_ele_pt > 0.:
        relEtcone.append( value/caloIso_ele_pt )
      else:
        relEtcone.append( 99990. )
    
    relPtcone = []
    # Fill rel pt cone
    for idx, value in enumerate( ptcone ):
      if caloIso_ele_pt > 0.:
        relPtcone.append( value/trkIso_ele_pt )
      else:
        relPtcone.append( 99990. )
    

    relEtConeCut_ispassed = True
    # Cut on Absolute Calo Isolation
    for idx, value in enumerate( relEtcone ):
      if self.RelEtConeCut[idx] > 0 and value > self.RelEtConeCut[idx]:
        relEtConeCut_ispassed = False
        break
    if not relEtConeCut_ispassed:
      return False
    
    relPtConeCut_ispassed = True
    # Cut on Absolute Track Isolation
    for idx, value in enumerate( relPtcone ):
      if self.PtConeCut[idx] > 0 and value > self.PtConeCut[idx]:
        relPtConeCut_ispassed = False
        break
    if not relPtConeCut_ispassed:
      return False

    return True









def configure_from_trigger( trigger ):

  d = treat_trigger_dict_type(trigger)
  etthr = d['etthr']
  pidname = d['pidname']
  iso = d['iso']

  name = 'Hypo__HLT__' + trigger
  emulator = ToolSvc.retrieve("Emulator")
  if not emulator.isValid(name):
    hypo = configure(name, pidname, iso)
    emulator+=hypo

  return name




#
# Configure the hypo tool from trigger name
#
def configure( name, pidname, iso ):

  isolation_dict = {
                    'ivarloose'   : [-1, -1, -1,0.100,-1,-1],
                    'ivarmedium'  : [-1, -1, -1,0.065,-1,-1],
                    'ivartight'   : [-1, -1, -1,0.05,-1,-1],
                    'iloose'      : [0.100, -1, -1,-1,-1,-1],
                   }
  
  caloisolation_dict = {
                        'icaloloose'  : [-1, -1, -1,0.2,-1,-1],
                        'icalomedium' : [-1, -1, -1,0.15,-1,-1],
                        'icalotight'  : [-1, -1, -1,0.1,-1,-1],
                       }
  relPtConeCuts = [-1, -1, -1,-1, -1, -1]
  relEtConeCuts = [-1, -1, -1,-1, -1, -1]

  if iso and 'icalo' in iso:
    relEtConeCuts = caloisolation_dict[iso] 
  if iso and not 'icalo' in iso:
    relPtConeCuts = isolation_dict[iso] 

  from kepler.emulator import TrigEgammaPrecisionElectronHypoTool
  hypo  = TrigEgammaPrecisionElectronHypoTool(name,
                                                Branch = 'trig_EF_el_'+pidname,
                                                UseClusETforCaloIso   = True,
                                                UseClusETforTrackIso  = True,
                                                PtConeCut             = [-1, -1, -1, -1, -1, -1],
                                                EtConeCut             = [-1, -1, -1, -1, -1, -1],
                                                RelPtConeCut          = relPtConeCuts,
                                                RelEtConeCut          = relEtConeCuts,
                                                DoIsolation           = True if iso else False,
                                                )

  return hypo


