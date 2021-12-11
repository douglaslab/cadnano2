class ActiveSliceItemController(object):
    def __init__(self, activeSliceItem, modelPart):
        self._activeSliceItem = activeSliceItem
        self._modelPart = modelPart
        self.connectSignals()

    def connectSignals(self):
        aSI = self._activeSliceItem
        mP = self._modelPart

        mP.partActiveSliceResizeSignal.connect(aSI.updateRectSlot)
        mP.partActiveSliceIndexSignal.connect(aSI.updateIndexSlot)
        mP.partStrandChangedSignal.connect(aSI.strandChangedSlot)
    # end def

    def disconnectSignals(self):
        aSI = self._activeSliceItem
        mP = self._modelPart

        mP.partActiveSliceResizeSignal.disconnect(aSI.updateRectSlot)
        mP.partActiveSliceIndexSignal.disconnect(aSI.updateIndexSlot)
        mP.partStrandChangedSignal.disconnect(aSI.strandChangedSlot)
    # end def
# end class
