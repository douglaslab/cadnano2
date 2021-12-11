from cadnano2.controllers.viewrootcontroller import ViewRootController
from .partitem import PartItem
import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsRectItem'])


class SliceRootItem(QGraphicsRectItem):
    """
    PathRootItem is the root item in the PathView. It gets added directly
    to the pathscene by DocumentWindow. It receives two signals
    (partAddedSignal and selectedPartChangedSignal) via its ViewRootController.

    PathRootItem must instantiate its own controller to receive signals
    from the model.
    """
    def __init__(self, rect, parent, window, document):
        super(SliceRootItem, self).__init__(rect, parent)
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._instanceItems = {}

    ### SIGNALS ###

    ### SLOTS ###
    def partAddedSlot(self, sender, modelPart):
        """
        Receives notification from the model that a part has been added.
        Views that subclass AbstractView should override this method.
        """
        self._modelPart = modelPart
        partItem = PartItem(modelPart, parent=self)
        self._instanceItems[partItem] = partItem
        self.setModifyState(self._window.actionModify.isChecked())
    # end def

    def selectedChangedSlot(self, itemDict):
        """docstring for selectedChangedSlot"""
        pass
    # end def
    
    def selectionFilterChangedSlot(self, filterNameList):
        pass
    # end def
    
    def clearSelectionsSlot(self, doc):
        self.scene().views()[0].clearSelectionLockAndCallbacks()
    # end def
    
    def resetRootItemSlot(self, doc):
        pass
    # end def

    ### ACCESSORS ###
    def sliceToolManager(self):
        """docstring for sliceToolManager"""
        return self._window.sliceToolManager
    # end def

    def window(self):
        return self._window
    # end def

    ### METHODS ###
    def removePartItem(self, partItem):
        del self._instanceItems[partItem]
    # end def

    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController"""
        self._document = document
        self._controller = ViewRootController(self, document)
        if len(self._instanceItems) > 0:
            raise ImportError
    # end def

    def setModifyState(self, bool):
        """docstring for setModifyState"""
        for partItem in self._instanceItems:
            partItem.setModifyState(bool)
    # end def
