#!/usr/bin/env python
# encoding: utf-8

from collections import defaultdict
from math import ceil
from .activesliceitem import ActiveSliceItem
from cadnano2.controllers.itemcontrollers.partitemcontroller import PartItemController
from .prexoveritem import PreXoverItem
from .strand.xoveritem import XoverNode3
from cadnano2.ui.mainwindow.svgbutton import SVGButton
from cadnano2.views import styles
from .virtualhelixitem import VirtualHelixItem
import cadnano2.util as util
from cadnano2.cadnano import app

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QDir', 'QPointF', 'QRectF', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QBrush',
                                       'QPen'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsPathItem',
                                           'QGraphicsItem',
                                           'QGraphicsRectItem',
                                           'QInputDialog'])


_baseWidth = _bw = styles.PATH_BASE_WIDTH
_defaultRect = QRectF(0, 0, _baseWidth, _baseWidth)
_modPen = QPen(styles.bluestroke)


class ProxyParentItem(QGraphicsRectItem):
    """an invisible container that allows one to play with Z-ordering"""
    findChild = util.findChild  # for debug


class PartItem(QGraphicsRectItem):
    findChild = util.findChild  # for debug

    def __init__(self, modelPart, viewroot, activeTool, parent):
        """parent should always be pathrootitem"""
        super(PartItem, self).__init__(parent)
        self._modelPart = mP = modelPart
        self._viewroot = viewroot
        self._activeTool = activeTool
        self._activeSliceItem = ActiveSliceItem(self, mP.activeBaseIndex())
        self._activeVirtualHelixItem = None
        self._controller = PartItemController(self, mP)
        self._preXoverItems = []  # crossover-related
        self._virtualHelixHash = {}
        self._virtualHelixItemList = []
        self._vHRect = QRectF()
        self.setAcceptHoverEvents(True)
        self._initModifierRect()
        self._initResizeButtons()
        self._proxyParent = ProxyParentItem(self)
        self._proxyParent.setFlag(QGraphicsItem.GraphicsItemFlag.ItemHasNoContents)
    # end def

    def proxy(self):
        return self._proxyParent
    # end def

    def _initModifierRect(self):
        """docstring for _initModifierRect"""
        self._canShowModRect = False
        self._modRect = mR = QGraphicsRectItem(_defaultRect, self)
        mR.setPen(_modPen)
        mR.hide()
    # end def

    def _initResizeButtons(self):
        """Instantiate the buttons used to change the canvas size."""
        self._addBasesButton = SVGButton("icons:add-bases.svg", self)
        self._addBasesButton.clicked.connect(self._addBasesClicked)
        self._addBasesButton.hide()
        self._removeBasesButton = SVGButton("icons:remove-bases.svg", self)
        self._removeBasesButton.clicked.connect(self._removeBasesClicked)
        self._removeBasesButton.hide()
    # end def

    def vhItemForVH(self, vhref):
        """Returns the pathview VirtualHelixItem corresponding to vhref"""
        vh = self._modelPart.virtualHelix(vhref)
        return self._virtualHelixHash.get(vh.coord())

    ### SIGNALS ###

    ### SLOTS ###
    def partParentChangedSlot(self, sender):
        """docstring for partParentChangedSlot"""
        # print "PartItem.partParentChangedSlot"
        pass
    # end def

    def partHideSlot(self, sender):
        self.hide()
    # end def

    def partActiveVirtualHelixChangedSlot(self, part, virtualHelix):
        self.updatePreXoverItems()
    #end def

    def partDimensionsChangedSlot(self, part):
        if len(self._virtualHelixItemList) > 0:
            vhi = self._virtualHelixItemList[0]
            vhiRect = vhi.boundingRect()
            vhiHRect = vhi.handle().boundingRect()
            self._vHRect.setLeft(vhiHRect.left())
            self._vHRect.setRight(vhiRect.right())
        self.scene().views()[0].zoomToFit()
        self._activeSliceItem.resetBounds()
        self._updateBoundingRect()
    # end def

    def partRemovedSlot(self, sender):
        """docstring for partRemovedSlot"""
        self._activeSliceItem.removed()
        self.parentItem().removePartItem(self)
        scene = self.scene()
        scene.removeItem(self)
        self._modelPart = None
        self._virtualHelixHash = None
        self._virtualHelixItemList = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partPreDecoratorSelectedSlot(self, sender, row, col, baseIdx):
        """docstring for partPreDecoratorSelectedSlot"""
        part = self._modelPart
        vh = part.virtualHelixAtCoord((row,col))
        vhi = self.itemForVirtualHelix(vh)
        yOffset = _bw if vh.isEvenParity() else 0
        p = QPointF(baseIdx*_bw, vhi.y() + yOffset)
        view = self.window().pathGraphicsView
        view.sceneRootItem.resetTransform()
        view.centerOn(p)
        view.zoomIn()
        self._modRect.setPos(p)
        if self._canShowModRect:
            self._modRect.show()
    # end def

    def partVirtualHelixAddedSlot(self, sender, modelVirtualHelix):
        """
        When a virtual helix is added to the model, this slot handles
        the instantiation of a virtualhelix item.
        """
        # print "PartItem.partVirtualHelixAddedSlot"
        vh = modelVirtualHelix
        vhi = VirtualHelixItem(self, modelVirtualHelix, self._viewroot, self._activeTool)
        self._virtualHelixHash[vh.coord()] = vhi
        self._virtualHelixItemList.append(vhi)
        self._setVirtualHelixItemList(self._virtualHelixItemList)
        self._updateBoundingRect()
    # end def

    def partVirtualHelixRenumberedSlot(self, sender, coord):
        """Notifies the virtualhelix at coord to change its number"""
        vh = self._virtualHelixHash[coord]
        # check for new number
        # notify VirtualHelixHandleItem to update its label
        # notify VirtualHelix to update its xovers
        # if the VirtualHelix is active, refresh prexovers
        pass
    # end def

    def partVirtualHelixResizedSlot(self, sender, coord):
        """Notifies the virtualhelix at coord to resize."""
        vh = self._virtualHelixHash[coord]
        vh.resize()
    # end def

    def partVirtualHelicesReorderedSlot(self, sender, orderedCoordList):
        """docstring for partVirtualHelicesReorderedSlot"""
        newList = self._virtualHelixItemList
        decorated = [(orderedCoordList.index(vhi.coord()), vhi)\
                        for vhi in self._virtualHelixItemList]
        decorated.sort()
        newList = [vhi for idx, vhi in decorated]
        self._setVirtualHelixItemList(newList)
    # end def

    def updatePreXoverItemsSlot(self, sender, virtualHelix):
        part = self.part()
        if virtualHelix == None:
            self.setPreXoverItemsVisible(None)
        elif part.areSameOrNeighbors(part.activeVirtualHelix(), virtualHelix):
            vhi = self.itemForVirtualHelix(virtualHelix)
            self.setActiveVirtualHelixItem(vhi)
            self.setPreXoverItemsVisible(self.activeVirtualHelixItem())
    # end def

    ### ACCESSORS ###
    def activeTool(self):
        return self._activeTool
    # end def

    def activeVirtualHelixItem(self):
        return self._activeVirtualHelixItem
    # end def

    def part(self):
        """Return a reference to the model's part object"""
        return self._modelPart
    # end def

    def document(self):
        """Return a reference to the model's document object"""
        return self._modelPart.document()
    # end def

    def removeVirtualHelixItem(self, virtualHelixItem):
        vh = virtualHelixItem.virtualHelix()
        self._virtualHelixItemList.remove(virtualHelixItem)
        del self._virtualHelixHash[vh.coord()]
        self._setVirtualHelixItemList(self._virtualHelixItemList)
        self._updateBoundingRect()

    # end def

    def itemForVirtualHelix(self, virtualHelix):
        return self._virtualHelixHash[virtualHelix.coord()]
    # end def

    def virtualHelixBoundingRect(self):
        return self._vHRect
    # end def

    def window(self):
        return self.parentItem().window()
    # end def

    ### PRIVATE METHODS ###
    def _addBasesClicked(self):
        part = self._modelPart
        step = part.stepSize()
        self._addBasesDialog = dlg = QInputDialog(self.window())
        dlg.setInputMode(QInputDialog.InputMode.IntInput)
        dlg.setIntMinimum(0)
        dlg.setIntValue(step)
        dlg.setIntMaximum(100000)
        dlg.setIntStep(step)
        dlg.setLabelText(( "Number of bases to add to the existing"\
                         + " %i bases\n(must be a multiple of %i)")\
                         % (part.maxBaseIdx(), step))
        dlg.intValueSelected.connect(self._addBasesCallback)
        dlg.open()
    # end def

    def _addBasesCallback(self, n):
        """
        Given a user-chosen number of bases to add, snap it to an index
        where index modulo stepsize is 0 and calls resizeVirtualHelices to
        adjust to that size.
        """
        part = self._modelPart
        self._addBasesDialog.intValueSelected.disconnect(self._addBasesCallback)
        del self._addBasesDialog
        maxDelta = int(n/part.stepSize()) * part.stepSize()
        part.resizeVirtualHelices(0, maxDelta)
        if app().isInMaya():
            import maya.cmds as cmds
            cmds.select(clear=True)
    # end def

    def _removeBasesClicked(self):
        """
        Determines the minimum maxBase index where index modulo stepsize == 0
        and is to the right of the rightmost nonempty base, and then resize
        each calls the resizeVirtualHelices to adjust to that size.
        """
        part = self._modelPart
        stepSize = part.stepSize()
        # first find out the right edge of the part
        idx = part.indexOfRightmostNonemptyBase()
        # next snap to a multiple of stepsize
        idx = int(ceil(float(idx+1)/stepSize))*stepSize
        # finally, make sure we're a minimum of stepSize bases
        idx = util.clamp(idx, part.stepSize(), 10000)
        delta = idx - (part.maxBaseIdx() + 1)
        if delta < 0:
            part.resizeVirtualHelices(0, delta)
            if app().isInMaya():
                import maya.cmds as cmds
                cmds.select(clear=True)
    # end def

    def _setVirtualHelixItemList(self, newList, zoomToFit=True):
        """
        Give me a list of VirtualHelixItems and I'll parent them to myself if
        necessary, position them in a column, adopt their handles, and
        position them as well.
        """
        y = 0  # How far down from the top the next PH should be
        leftmostExtent = 0
        rightmostExtent = 0

        scene = self.scene()
        vhiRect = None
        vhiHRect = None

        for vhi in newList:
            vhi.setPos(0, y)
            if not vhiRect:
                vhiRect = vhi.boundingRect()
                step = vhiRect.height() + styles.PATH_HELIX_PADDING
            # end if

            # get the VirtualHelixHandleItem
            vhiH = vhi.handle()
            if vhiH.parentItem() != self._viewroot._vhiHSelectionGroup:
                vhiH.setParentItem(self)

            if not vhiHRect:
                vhiHRect = vhiH.boundingRect()

            vhiH.setPos(-2 * vhiHRect.width(), y + (vhiRect.height() - vhiHRect.height()) / 2)

            leftmostExtent = min(leftmostExtent, -2 * vhiHRect.width())
            rightmostExtent = max(rightmostExtent, vhiRect.width())
            y += step
            self.updateXoverItems(vhi)
        # end for
        self._vHRect = QRectF(leftmostExtent, -40, -leftmostExtent + rightmostExtent, y + 40)
        self._virtualHelixItemList = newList
        if zoomToFit:
            self.scene().views()[0].zoomToFit()
    # end def

    def _updateBoundingRect(self):
        """
        Updates the bounding rect to the size of the childrenBoundingRect,
        and refreshes the addBases and removeBases buttons accordingly.

        Called by partVirtualHelixAddedSlot, partDimensionsChangedSlot, or
        removeVirtualHelixItem.
        """
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setRect(self.childrenBoundingRect())
        # move and show or hide the buttons if necessary
        addButton = self._addBasesButton
        rmButton = self._removeBasesButton
        if len(self._virtualHelixItemList) > 0:
            addRect = addButton.boundingRect()
            rmRect = rmButton.boundingRect()
            x = self._vHRect.right()
            y = -styles.PATH_HELIX_PADDING
            addButton.setPos(x, y)
            rmButton.setPos(x-rmRect.width(), y)
            addButton.show()
            rmButton.show()
        else:
            addButton.hide()
            rmButton.hide()
    # end def

    ### PUBLIC METHODS ###
    def setModifyState(self, bool):
        """Hides the modRect when modify state disabled."""
        self._canShowModRect = bool
        if bool == False:
            self._modRect.hide()

    def getOrderedVirtualHelixList(self):
        """Used for encoding."""
        ret = []
        for vhi in self._virtualHelixItemList:
            ret.append(vhi.coord())
        return ret
    # end def

    def numberOfVirtualHelices(self):
        return len(self._virtualHelixItemList)
    # end def

    def reorderHelices(self, first, last, indexDelta):
        """
        Reorder helices by moving helices _pathHelixList[first:last]
        by a distance delta in the list. Notify each PathHelix and
        PathHelixHandle of its new location.
        """
        vhiList = self._virtualHelixItemList
        helixNumbers = [vhi.number() for vhi in vhiList]
        firstIndex = helixNumbers.index(first)
        lastIndex = helixNumbers.index(last) + 1

        if indexDelta < 0:  # move group earlier in the list
            newIndex = max(0, indexDelta + firstIndex)
            newList = vhiList[0:newIndex] +\
                                vhiList[firstIndex:lastIndex] +\
                                vhiList[newIndex:firstIndex] +\
                                vhiList[lastIndex:]
        # end if
        else:  # move group later in list
            newIndex = min(len(vhiList), indexDelta + lastIndex)
            newList = vhiList[:firstIndex] +\
                                 vhiList[lastIndex:newIndex] +\
                                 vhiList[firstIndex:lastIndex] +\
                                 vhiList[newIndex:]
        # end else

        # call the method to move the items and store the list
        self._setVirtualHelixItemList(newList, zoomToFit=False)
    # end def

    def setActiveVirtualHelixItem(self, newActiveVHI):
        if newActiveVHI != self._activeVirtualHelixItem:
            self._activeVirtualHelixItem = newActiveVHI
            # self._modelPart.setActiveVirtualHelix(newActiveVHI.virtualHelix())
    # end def

    def setPreXoverItemsVisible(self, virtualHelixItem):
        """
        self._preXoverItems list references prexovers parented to other
        PathHelices such that only the activeHelix maintains the list of
        visible prexovers
        """
        vhi = virtualHelixItem

        if vhi == None:
            if self._preXoverItems:
                # clear all PreXoverItems
                list(map(PreXoverItem.remove, self._preXoverItems))
                self._preXoverItems = []
            return

        vh = vhi.virtualHelix()
        partItem = self
        part = self.part()
        idx = part.activeVirtualHelixIdx()

        # clear all PreXoverItems
        list(map(PreXoverItem.remove, self._preXoverItems))
        self._preXoverItems = []

        potentialXovers = part.potentialCrossoverList(vh, idx)
        for neighbor, index, strandType, isLowIdx in potentialXovers:
            # create one half
            neighborVHI = self.itemForVirtualHelix(neighbor)
            pxi = PreXoverItem(vhi, neighborVHI, index, strandType, isLowIdx)
            # add to list
            self._preXoverItems.append(pxi)
            # create the complement
            pxi = PreXoverItem(neighborVHI, vhi, index, strandType, isLowIdx)
            # add to list
            self._preXoverItems.append(pxi)
        # end for
    # end def

    def updatePreXoverItems(self):
        self.setPreXoverItemsVisible(self.activeVirtualHelixItem())
    # end def

    def updateXoverItems(self, virtualHelixItem):
        for item in virtualHelixItem.childItems():
            if isinstance(item, XoverNode3):
                item.refreshXover()
     # end def

    def updateStatusBar(self, statusString):
        """Shows statusString in the MainWindow's status bar."""
        self.window().statusBar().showMessage(statusString)

    ### COORDINATE METHODS ###
    def keyPanDeltaX(self):
        """How far a single press of the left or right arrow key should move
        the scene (in scene space)"""
        vhs = self._virtualHelixItemList
        return vhs[0].keyPanDeltaX() if vhs else 5
    # end def

    def keyPanDeltaY(self):
        """How far an an arrow key should move the scene (in scene space)
        for a single press"""
        vhs = self._virtualHelixItemList
        if not len(vhs) > 1:
            return 5
        dy = vhs[0].pos().y() - vhs[1].pos().y()
        dummyRect = QRectF(0, 0, 1, dy)
        return self.mapToScene(dummyRect).boundingRect().height()
    # end def

    ### TOOL METHODS ###
    def hoverMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        activeTool = self._activeTool()
        toolMethodName = str(activeTool) + "HoverMove"
        if hasattr(self, toolMethodName):
            getattr(self, toolMethodName)(event.pos())
    # end def

    def pencilToolHoverMove(self, pt):
        """Pencil the strand is possible."""
        partItem = self
        activeTool = self._activeTool()
        if not activeTool.isFloatingXoverBegin():
            tempXover = activeTool.floatingXover()
            tempXover.updateFloatingFromPartItem(self, pt)
    # end def
