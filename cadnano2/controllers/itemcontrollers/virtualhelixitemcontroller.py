class VirtualHelixItemController():
    def __init__(self, virtualHelixItem, modelVirtualHelix):
        self._virtualHelixItem = virtualHelixItem
        self._modelVirtualHelix = modelVirtualHelix
        self.connectSignals()
    # end def

    def connectSignals(self):
        vhItem = self._virtualHelixItem
        mvh = self._modelVirtualHelix

        mvh.virtualHelixNumberChangedSignal.connect(vhItem.virtualHelixNumberChangedSlot)
        mvh.virtualHelixRemovedSignal.connect(vhItem.virtualHelixRemovedSlot)

        for strandSet in mvh.getStrandSets():
            strandSet.strandsetStrandAddedSignal.connect(vhItem.strandAddedSlot)
            # strandSet.decoratorAddedSignal.connect(vhItem.decoratorAddedSlot)
    # end def

    def disconnectSignals(self):
        vhItem = self._virtualHelixItem
        mvh = self._modelVirtualHelix

        mvh.virtualHelixNumberChangedSignal.disconnect(vhItem.virtualHelixNumberChangedSlot)
        mvh.virtualHelixRemovedSignal.disconnect(vhItem.virtualHelixRemovedSlot)

        for strandSet in mvh.getStrandSets():
            strandSet.strandsetStrandAddedSignal.disconnect(vhItem.strandAddedSlot)
            # strandSet.decoratorAddedSignal.disconnect(vhItem.decoratorAddedSlot)