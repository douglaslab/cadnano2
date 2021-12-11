class ViewRootController():
    def __init__(self, viewRoot, modelDocument):
        self._viewRoot = viewRoot
        self._modelDocument = modelDocument
        self.connectSignals()

    def connectSignals(self):
        mD = self._modelDocument
        vR = self._viewRoot
        mD.documentPartAddedSignal.connect(vR.partAddedSlot)
        mD.documentClearSelectionsSignal.connect(vR.clearSelectionsSlot)
        mD.documentSelectionFilterChangedSignal.connect(vR.selectionFilterChangedSlot)
        mD.documentViewResetSignal.connect(vR.resetRootItemSlot)

    def disconnectSignals(self):
        mD = self._modelDocument
        vR = self._viewRoot
        mD.documentPartAddedSignal.disconnect(vR.partAddedSlot)
        mD.documentClearSelectionsSignal.disconnect(vR.clearSelectionsSlot)
        mD.documentSelectionFilterChangedSignal.disconnect(vR.selectionFilterChangedSlot)
        mD.documentViewResetSignal.disconnect(vR.resetRootItemSlot)