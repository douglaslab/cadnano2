import cadnano2.util as util
from cadnano2.controllers.itemcontrollers.strand.abstractstranditemcontroller \
     import AbstractStrandItemController


class StrandItemController(AbstractStrandItemController):
    def __init__(self, strandItem, modelStrand):
        super(StrandItemController, self).__init__(strandItem, modelStrand)
        self.connectSignals()
    # end def

    def reconnectOligoSignals(self):
        """
        use this for whenever a strands oligo changes
        """
        AbstractStrandItemController.disconnectOligoSignals(self)
        self.disconnectOligoSignals()
        AbstractStrandItemController.connectOligoSignals(self)
        self.connectOligoSignals()
    # end def

    def connectSignals(self):
        AbstractStrandItemController.connectSignals(self)
        mS = self._modelStrand
        sI = self._strandItem
        mS.strandResizedSignal.connect(sI.strandResizedSlot)
        # mS.strandXover5pChangedSignal.connect(sI.strandXover5pChangedSlot)
        mS.strandUpdateSignal.connect(sI.strandUpdateSlot)
        self.connectOligoSignals()
    # end def

    def connectOligoSignals(self):
        mO = self._modelStrand.oligo()
        self._modelOligo = mO
        sI = self._strandItem
        mO.oligoSequenceAddedSignal.connect(sI.oligoSequenceAddedSlot)
        mO.oligoSequenceClearedSignal.connect(sI.oligoSequenceClearedSlot)
    # end def

    def disconnectSignals(self):
        AbstractStrandItemController.disconnectSignals(self)
        mS = self._modelStrand
        sI = self._strandItem
        mS.strandResizedSignal.disconnect(sI.strandResizedSlot)
        # mS.strandXover5pChangedSignal.disconnect(sI.strandXover5pChangedSlot)
        mS.strandUpdateSignal.disconnect(sI.strandUpdateSlot)
        self.disconnectOligoSignals()
    # end def

    def disconnectOligoSignals(self):
        mO = self._modelOligo
        sI = self._strandItem
        mO.oligoSequenceAddedSignal.disconnect(sI.oligoSequenceAddedSlot)
        mO.oligoSequenceClearedSignal.disconnect(sI.oligoSequenceClearedSlot)
    # end def
