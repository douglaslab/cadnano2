import cadnano2.util as util
# from cadnano2.controllers.itemcontrollers.abstractitemcontroller import AbstractItemController


class AbstractStrandItemController(object):
    def __init__(self, strandItem, modelStrand):
        """
        Do not call connectSignals here.  subclasses
        will install two sets of signals.
        """
        if self.__class__ == AbstractStrandItemController:
            e = "AbstractStrandItemController should be subclassed."
            raise NotImplementedError(e)
        self._strandItem = strandItem
        self._modelStrand = modelStrand
        self._modelOligo = modelStrand.oligo()
    # end def

    def reconnectOligoSignals(self):
        self.disconnectOligoSignals()
        self.connectOligoSignals()
    # end def

    def connectSignals(self):
        """Connects modelStrant signals to strandItem slots."""
        mS = self._modelStrand
        sI = self._strandItem

        AbstractStrandItemController.connectOligoSignals(self)
        mS.strandHasNewOligoSignal.connect(sI.strandHasNewOligoSlot)
        mS.strandRemovedSignal.connect(sI.strandRemovedSlot)

        mS.strandInsertionAddedSignal.connect(sI.strandInsertionAddedSlot)
        mS.strandInsertionChangedSignal.connect(sI.strandInsertionChangedSlot)
        mS.strandInsertionRemovedSignal.connect(sI.strandInsertionRemovedSlot)
        mS.strandDecoratorAddedSignal.connect(sI.strandDecoratorAddedSlot)
        mS.strandDecoratorChangedSignal.connect(sI.strandDecoratorChangedSlot)
        mS.strandDecoratorRemovedSignal.connect(sI.strandDecoratorRemovedSlot)
        mS.strandModifierAddedSignal.connect(sI.strandModifierAddedSlot)
        mS.strandModifierChangedSignal.connect(sI.strandModifierChangedSlot)
        mS.strandModifierRemovedSignal.connect(sI.strandModifierRemovedSlot)

        mS.selectedChangedSignal.connect(sI.selectedChangedSlot)
    # end def

    def connectOligoSignals(self):
        sI = self._strandItem
        mO = self._modelStrand.oligo()
        self._modelOligo = mO
        mO.oligoAppearanceChangedSignal.connect(sI.oligoAppearanceChangedSlot)
    # end def

    def disconnectSignals(self):
        mS = self._modelStrand
        sI = self._strandItem

        AbstractStrandItemController.disconnectOligoSignals(self)
        mS.strandHasNewOligoSignal.disconnect(sI.strandHasNewOligoSlot)
        mS.strandRemovedSignal.disconnect(sI.strandRemovedSlot)

        mS.strandInsertionAddedSignal.disconnect(sI.strandInsertionAddedSlot)
        mS.strandInsertionChangedSignal.disconnect(sI.strandInsertionChangedSlot)
        mS.strandInsertionRemovedSignal.disconnect(sI.strandInsertionRemovedSlot)
        mS.strandDecoratorAddedSignal.disconnect(sI.strandDecoratorAddedSlot)
        mS.strandDecoratorChangedSignal.disconnect(sI.strandDecoratorChangedSlot)
        mS.strandDecoratorRemovedSignal.disconnect(sI.strandDecoratorRemovedSlot)
        mS.strandModifierAddedSignal.disconnect(sI.strandModifierAddedSlot)
        mS.strandModifierChangedSignal.disconnect(sI.strandModifierChangedSlot)
        mS.strandModifierRemovedSignal.disconnect(sI.strandModifierRemovedSlot)

        mS.selectedChangedSignal.disconnect(sI.selectedChangedSlot)
    # end def

    def disconnectOligoSignals(self):
        sI = self._strandItem
        mO = self._modelOligo
        mO.oligoAppearanceChangedSignal.disconnect(sI.oligoAppearanceChangedSlot)
    # end def
