import cadnano2.util as util


class XoverItemController(object):
    def __init__(self, xoverItem, modelStrand5p):
        self._xoverItem = xoverItem
        self._modelStrand5p = modelStrand5p
        self._modelOligo = modelStrand5p.oligo()
        self.connectSignals()
    # end def

    def reconnectOligoSignals(self):
        """
        use this for whenever a strands oligo changes
        """
        self.disconnectSignals()
        self.connectSignals()
    # end def

    def reconnectSignals(self, strand):
        self.disconnectSignals()
        self._modelStrand5p = strand
        self.connectSignals()
    # end def

    def connectSignals(self):
        xI = self._xoverItem
        s5p = self._modelStrand5p
        mO = s5p.oligo()
        self._modelOligo = mO

        s5p.strand5pHasSwappedSignal.connect(xI.strandSwapSlot)
        s5p.strandHasNewOligoSignal.connect(xI.strandHasNewOligoSlot)
        mO.oligoAppearanceChangedSignal.connect(xI.oligoAppearanceChangedSlot)
        s5p.strandXover5pRemovedSignal.connect(xI.xover5pRemovedSlot)
    # end def

    def disconnectSignals(self):
        xI = self._xoverItem
        s5p = self._modelStrand5p
        mO = self._modelOligo

        s5p.strand5pHasSwappedSignal.disconnect(xI.strandSwapSlot)
        s5p.strandHasNewOligoSignal.disconnect(xI.strandHasNewOligoSlot)
        mO.oligoAppearanceChangedSignal.disconnect(xI.oligoAppearanceChangedSlot)
        s5p.strandXover5pRemovedSignal.connect(xI.xover5pRemovedSlot)
    # end def
