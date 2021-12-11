from cadnano2.controllers.viewrootcontroller import ViewRootController
from .partitem import PartItem
from .pathselection import SelectionItemGroup
from .pathselection import VirtualHelixHandleSelectionBox
from .pathselection import EndpointHandleSelectionBox
import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsRectItem'])


class PathRootItem(QGraphicsRectItem):
    """
    PathRootItem is the root item in the PathView. It gets added directly
    to the pathscene by DocumentWindow. It receives two signals
    (partAddedSignal and documentSelectedPartChangedSignal)
    via its ViewRootController.

    PathRootItem must instantiate its own controller to receive signals
    from the model.
    """
    findChild = util.findChild  # for debug

    def __init__(self, rect, parent, window, document):
        super(PathRootItem, self).__init__(rect, parent)
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._modelPart = None
        self._partItemForPart = {}  # Maps Part -> PartItem
        self._selectionFilterDict = {}
        self._initSelections()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def partItems(self):
        return list(self._partItemForPart.values())

    def partItemForPart(self, part):
        return self._partItemForPart[part]

    def partAddedSlot(self, sender, modelPart):
        """
        Receives notification from the model that a part has been added.
        The Pathview doesn't need to do anything on part addition, since
        the Sliceview handles setting up the appropriate lattice.
        """
        # print "PathRootItem partAddedSlot", modelPart
        self._modelPart = modelPart
        win = self._window
        partItem = PartItem(modelPart,\
                            viewroot=self, \
                            activeTool=win.pathToolManager.activeTool,\
                            parent=self)
        self._partItemForPart[modelPart] = partItem
        win.pathToolManager.setActivePart(partItem)
        self.setModifyState(win.actionModify.isChecked())
    # end def

    def selectedChangedSlot(self, itemDict):
        """Given a newly selected modelPart, update the scene to indicate
        that modelPart is selected and the previously selected part is
        deselected."""
        for item, value in itemDict:
            item.selectionProcess(value)
    # end def

    def clearSelectionsSlot(self, doc):
        self._vhiHSelectionGroup.resetSelection()
        self._strandItemSelectionGroup.resetSelection()
        self.scene().views()[0].clearSelectionLockAndCallbacks()
    # end def

    def selectionFilterChangedSlot(self, filterNameList):
        self._vhiHSelectionGroup.clearSelection(False)
        self._strandItemSelectionGroup.clearSelection(False)
        self.clearSelectionFilterDict()
        for filterName in filterNameList:
            self.addToSelectionFilterDict(filterName)
    # end def

    def resetRootItemSlot(self, doc):
        self._vhiHSelectionGroup.resetSelection()
        self._strandItemSelectionGroup.resetSelection()
        self.scene().views()[0].clearGraphicsView()
    # end def

    ### ACCESSORS ###
    def sliceToolManager(self):
        """
        Used for getting access to button signals that need to be connected
        to item slots.
        """
        return self._window.sliceToolManager
    # end def

    def window(self):
        return self._window
    # end def

    def document(self):
        return self._document
    # end def

    def _initSelections(self):
        """Initialize anything related to multiple selection."""
        bType = VirtualHelixHandleSelectionBox
        self._vhiHSelectionGroup = SelectionItemGroup(boxtype=bType,\
                                                      constraint='y',\
                                                      parent=self)
        bType = EndpointHandleSelectionBox
        self._strandItemSelectionGroup = SelectionItemGroup(boxtype=bType,\
                                                      constraint='x',\
                                                      parent=self)
    # end def

    ### PUBLIC METHODS ###
    def getSelectedPartOrderedVHList(self):
        """Used for encoding."""
        selectedPart = self._document.selectedPart()
        return self._partItemForPart[selectedPart].getOrderedVirtualHelixList()
    # end def

    def removePartItem(self, partItem):
        for k in self._partItemForPart.keys():
            if k==partItem:
                del self._partItemForPart[k]
                return
    # end def

    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController"""
        self._document = document
        self._controller = ViewRootController(self, document)
    # end def

    def setModifyState(self, bool):
        """docstring for setModifyState"""
        for partItem in self._partItemForPart.values():
            partItem.setModifyState(bool)
    # end def

    def selectionFilterDict(self):
        return self._selectionFilterDict
    # end def

    def addToSelectionFilterDict(self, filterName):
        self._selectionFilterDict[filterName] = True
    # end def

    def removeFromSelectionFilterDict(self, filterName):
        del self._selectionFilterDict[filterName]
    # end def

    def clearSelectionFilterDict(self):
        self._selectionFilterDict = {}
    # end def

    def vhiHandleSelectionGroup(self):
        return self._vhiHSelectionGroup
    # end def

    def strandItemSelectionGroup(self):
        return self._strandItemSelectionGroup
    # end def

    def selectionLock(self):
        return self.scene().views()[0].selectionLock()
    # end def

    def setSelectionLock(self, locker):
        self.scene().views()[0].setSelectionLock(locker)
    # end def

    def clearStrandSelections(self):
        self._strandItemSelectionGroup.clearSelection(False)
    # end def
# end class
