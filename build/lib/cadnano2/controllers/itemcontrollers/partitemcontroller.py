class PartItemController(object):
    def __init__(self, partItem, modelPart):
        self._partItem = partItem
        self._modelPart = modelPart
        self.connectSignals()

    def connectSignals(self):
        mP = self._modelPart
        pI = self._partItem

        if hasattr(pI, "partHideSlot"):
            mP.partHideSignal.connect(pI.partHideSlot)
        if hasattr(pI, "partActiveVirtualHelixChangedSlot"):
            mP.partActiveVirtualHelixChangedSignal.connect(pI.partActiveVirtualHelixChangedSlot)

        mP.partDimensionsChangedSignal.connect(pI.partDimensionsChangedSlot)
        mP.partParentChangedSignal.connect(pI.partParentChangedSlot)
        mP.partPreDecoratorSelectedSignal.connect(pI.partPreDecoratorSelectedSlot)
        mP.partRemovedSignal.connect(pI.partRemovedSlot)
        mP.partStrandChangedSignal.connect(pI.updatePreXoverItemsSlot)
        mP.partVirtualHelixAddedSignal.connect(pI.partVirtualHelixAddedSlot)
        mP.partVirtualHelixRenumberedSignal.connect(pI.partVirtualHelixRenumberedSlot)
        mP.partVirtualHelixResizedSignal.connect(pI.partVirtualHelixResizedSlot)
        mP.partVirtualHelicesReorderedSignal.connect(pI.partVirtualHelicesReorderedSlot)
    # end def

    def disconnectSignals(self):
        mP = self._modelPart
        pI = self._partItem

        if hasattr(pI, "partHideSlot"):
            mP.partHideSignal.disconnect(pI.partHideSlot)
        if hasattr(pI, "partActiveVirtualHelixChangedSlot"):
            mP.partActiveVirtualHelixChangedSignal.disconnect(pI.partActiveVirtualHelixChangedSlot)

        mP.partDimensionsChangedSignal.disconnect(pI.partDimensionsChangedSlot)
        mP.partParentChangedSignal.disconnect(pI.partParentChangedSlot)
        mP.partPreDecoratorSelectedSignal.disconnect(pI.partPreDecoratorSelectedSlot)
        mP.partRemovedSignal.disconnect(pI.partRemovedSlot)
        mP.partStrandChangedSignal.disconnect(pI.updatePreXoverItemsSlot)
        mP.partVirtualHelixAddedSignal.disconnect(pI.partVirtualHelixAddedSlot)
        mP.partVirtualHelixRenumberedSignal.disconnect(pI.partVirtualHelixRenumberedSlot)
        mP.partVirtualHelixResizedSignal.disconnect(pI.partVirtualHelixResizedSlot)
        mP.partVirtualHelicesReorderedSignal.disconnect(pI.partVirtualHelicesReorderedSlot)
    # end def
# end class
