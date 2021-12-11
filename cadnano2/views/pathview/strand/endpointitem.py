#!/usr/bin/env python
# encoding: utf-8

# from exceptions import NotImplementedError
from math import floor
from cadnano2.views import styles

import cadnano2.views.pathview.pathselection as pathselection

import cadnano2.util as util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject', 'QPointF',
                                        'QRectF', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QBrush', 'QColor', 'QPen',
                                       'QPainterPath', 'QPolygonF'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsPathItem',
                                           'QGraphicsItem',
                                           'QGraphicsRectItem'])

_baseWidth = styles.PATH_BASE_WIDTH

ppL5 = QPainterPath()  # Left 5' PainterPath
ppR5 = QPainterPath()  # Right 5' PainterPath
ppL3 = QPainterPath()  # Left 3' PainterPath
ppR3 = QPainterPath()  # Right 3' PainterPath
pp53 = QPainterPath()  # Left 5', Right 3' PainterPath
pp35 = QPainterPath()  # Left 5', Right 3' PainterPath
# set up ppL5 (left 5' blue square)
ppL5.addRect(0.25 * _baseWidth,
             0.125 * _baseWidth,
             0.75 * _baseWidth,
             0.75 * _baseWidth)
# set up ppR5 (right 5' blue square)
ppR5.addRect(0, 0.125 * _baseWidth, 0.75 * _baseWidth, 0.75 * _baseWidth)
# set up ppL3 (left 3' blue triangle)
l3poly = QPolygonF()
l3poly.append(QPointF(_baseWidth, 0))
l3poly.append(QPointF(0.25 * _baseWidth, 0.5 * _baseWidth))
l3poly.append(QPointF(_baseWidth, _baseWidth))
l3poly.append(QPointF(_baseWidth, 0))
ppL3.addPolygon(l3poly)
# set up ppR3 (right 3' blue triangle)
r3poly = QPolygonF()
r3poly.append(QPointF(0, 0))
r3poly.append(QPointF(0.75 * _baseWidth, 0.5 * _baseWidth))
r3poly.append(QPointF(0, _baseWidth))
r3poly.append(QPointF(0, 0))
ppR3.addPolygon(r3poly)

# single base left 5'->3'
pp53.addRect(0, 0.125 * _baseWidth, 0.5 * _baseWidth, 0.75 * _baseWidth)
poly53 = QPolygonF()
poly53.append(QPointF(0.5 * _baseWidth, 0))
poly53.append(QPointF(_baseWidth, 0.5 * _baseWidth))
poly53.append(QPointF(0.5 * _baseWidth, _baseWidth))
pp53.addPolygon(poly53)
# single base left 3'<-5'
pp35.addRect(0.50 * _baseWidth,
             0.125 * _baseWidth,
             0.5 * _baseWidth,
             0.75 * _baseWidth)
poly35 = QPolygonF()
poly35.append(QPointF(0.5 * _baseWidth, 0))
poly35.append(QPointF(0, 0.5 * _baseWidth))
poly35.append(QPointF(0.5 * _baseWidth, _baseWidth))
pp35.addPolygon(poly35)

_defaultRect = QRectF(0, 0, _baseWidth, _baseWidth)
_noPen = QPen(Qt.PenStyle.NoPen)


class EndpointItem(QGraphicsPathItem):

    _filterName = "endpoint"

    def __init__(self, strandItem, captype, isDrawn5to3):
        """The parent should be a StrandItem."""
        super(EndpointItem, self).__init__(strandItem.virtualHelixItem())

        self._strandItem = strandItem
        self._activeTool = strandItem.activeTool()
        self._capType = captype
        self._lowDragBound = None
        self._highDragBound = None
        self._initCapSpecificState(isDrawn5to3)
        self.setPen(QPen())
        # for easier mouseclick
        self._clickArea = cA = QGraphicsRectItem(_defaultRect, self)
        self._clickArea.setAcceptHoverEvents(True)
        cA.hoverMoveEvent = self.hoverMoveEvent
        cA.mousePressEvent = self.mousePressEvent
        cA.mouseMoveEvent = self.mouseMoveEvent
        cA.setPen(_noPen)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
    # end def

    # def __repr__(self):
    #     return "%s" % self.__class__.__name__

    ### SIGNALS ###

    ### SLOTS ###

    ### ACCESSORS ###
    def idx(self):
        """Look up baseIdx, as determined by strandItem idxs and cap type."""
        if self._capType == 'low':
            return self._strandItem.idxs()[0]
        else:  # high or dual, doesn't matter
            return self._strandItem.idxs()[1]
    # end def

    def partItem(self):
        return self._strandItem.partItem()
    # end def

    def disableEvents(self):
        self._clickArea.setAcceptHoverEvents(False)
        self.mouseMoveEvent = QGraphicsPathItem.mouseMoveEvent
        self.mousePressEvent = QGraphicsPathItem.mousePressEvent
    # end def

    def window(self):
        return self._strandItem.window()

    ### PUBLIC METHODS FOR DRAWING / LAYOUT ###
    def updatePosIfNecessary(self, idx):
        """Update position if necessary and return True if updated."""
        group = self.group()
        self.tempReparent()
        x = int(idx * _baseWidth)
        if x != self.x():
            self.setPos(x, self.y())
            if group:
                group.addToGroup(self)
            return True
        else:
            if group:
                group.addToGroup(self)
            return False

    def safeSetPos(self, x, y):
        """
        Required to ensure proper reparenting if selected
        """
        group = self.group()
        self.tempReparent()
        self.setPos(x,y)
        if group:
            group.addToGroup(self)
    # end def

    def resetEndPoint(self, isDrawn5to3):
        self.setParentItem(self._strandItem.virtualHelixItem())
        self._initCapSpecificState(isDrawn5to3)
        upperLeftY = 0 if isDrawn5to3 else _baseWidth
        self.setY(upperLeftY)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _initCapSpecificState(self, isDrawn5to3):
        cT = self._capType
        if cT == 'low':
            path = ppL5 if isDrawn5to3 else ppL3
        elif cT == 'high':
            path = ppR3 if isDrawn5to3 else ppR5
        elif cT == 'dual':
            path = pp53 if isDrawn5to3 else pp35
        self.setPath(path)
    # end def

    def _getNewIdxsForResize(self, baseIdx):
        """Returns a tuple containing idxs to be passed to the """
        cT = self._capType
        if cT == 'low':
            return (baseIdx, self._strandItem.idxs()[1])
        elif cT == 'high':
            return (self._strandItem.idxs()[0], baseIdx)
        elif cT == 'dual':
            raise NotImplementedError

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent, calling the approproate tool method as
        necessary. Stores _moveIdx for future comparison.
        """
        self.scene().views()[0].addToPressList(self)
        self._strandItem.virtualHelixItem().setActive(self.idx())
        self._moveIdx = self.idx()
        activeToolStr = str(self._activeTool())
        toolMethodName = activeToolStr + "MousePress"
        if hasattr(self, toolMethodName):  # if the tool method exists
            modifiers = event.modifiers()
            getattr(self, toolMethodName)(modifiers, event, self.idx())

    def hoverLeaveEvent(self, event):
        self.partItem().updateStatusBar("")
    # end def

    def hoverMoveEvent(self, event):
        """
        Parses a mousePressEvent, calling the approproate tool method as
        necessary. Stores _moveIdx for future comparison.
        """
        vhiNum = self._strandItem._virtualHelixItem.number()
        oligoLength = self._strandItem._modelStrand.oligo().length()
        msg = "%d[%d]\tlength: %d" % (vhiNum, self.idx(), oligoLength)
        self.partItem().updateStatusBar(msg)

        activeToolStr = str(self._activeTool())
        if activeToolStr == 'pencilTool':
            return self._strandItem.pencilToolHoverMove(self.idx())

    def mouseMoveEvent(self, event):
        """
        Parses a mouseMoveEvent, calling the approproate tool method as
        necessary. Updates _moveIdx if it changed.
        """
        toolMethodName = str(self._activeTool()) + "MouseMove"
        if hasattr(self, toolMethodName):  # if the tool method exists
            idx = int(floor((self.x() + event.pos().x()) / _baseWidth))
            if idx != self._moveIdx:  # did we actually move?
                modifiers = event.modifiers()
                self._moveIdx = idx
                getattr(self, toolMethodName)(modifiers, idx)

    def customMouseRelease(self, event):
        """
        Parses a mouseReleaseEvent, calling the approproate tool method as
        necessary. Deletes _moveIdx if necessary.
        """
        toolMethodName = str(self._activeTool()) + "MouseRelease"
        if hasattr(self, toolMethodName):  # if the tool method exists
            modifiers = event.modifiers()
            x = event.position().x()
            getattr(self, toolMethodName)(modifiers, x)  # call tool method
        if self._moveIdx is not None:
            self._moveIdx = None

    ### TOOL METHODS ###
    def addSeqToolMousePress(self, modifiers, event, idx):
        """
        Checks that a scaffold was clicked, and then calls apply sequence
        to the clicked strand via its oligo.
        """
        mStrand = self._strandItem._modelStrand
        if mStrand.isScaffold():
            olgLen, seqLen = self._activeTool().applySequence(mStrand.oligo())
            if olgLen:
                msg = "Populated %d of %d scaffold bases." % (min(seqLen, olgLen), olgLen)
                if olgLen > seqLen:
                    d = olgLen - seqLen
                    msg = msg + " Warning: %d bases have no sequence." % d
                elif olgLen < seqLen:
                    d = seqLen - olgLen
                    msg = msg + " Warning: %d sequence bases unused." % d
                self.partItem().updateStatusBar(msg)


    def breakToolMouseRelease(self, modifiers, x):
        """Shift-click to merge without switching back to select tool."""
        mStrand = self._strandItem._modelStrand
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            mStrand.merge(self.idx())
    # end def

    def eraseToolMousePress(self, modifiers, event, idx):
        """Erase the strand."""
        mStrand = self._strandItem._modelStrand
        mStrand.strandSet().removeStrand(mStrand)
    # end def

    def insertionToolMousePress(self, modifiers, event, idx):
        """Add an insert to the strand if possible."""
        mStrand = self._strandItem._modelStrand
        mStrand.addInsertion(idx, 1)
    # end def

    def paintToolMousePress(self, modifiers, event, idx):
        """Add an insert to the strand if possible."""
        mStrand = self._strandItem._modelStrand
        if mStrand.isStaple():
            color = self.window().pathColorPanel.stapColorName()
        else:
            color = self.window().pathColorPanel.scafColorName()
        mStrand.oligo().applyColor(color)
    # end def

    def pencilToolHoverMove(self, idx):
        """Pencil the strand is possible."""
        mStrand = self._strandItem._modelStrand
        vhi = self._strandItem._virtualHelixItem
        activeTool = self._activeTool()

        if not activeTool.isFloatingXoverBegin():
            tempXover = activeTool.floatingXover()
            tempXover.updateFloatingFromStrandItem(vhi, mStrand, idx)
            # if mStrand.idx5Prime() == idx:
            #     tempXover.hide3prime()
    # end def

    def pencilToolMousePress(self, modifiers, event, idx):
        """Break the strand is possible."""
        mStrand = self._strandItem._modelStrand
        vhi = self._strandItem._virtualHelixItem
        partItem = vhi.partItem()
        activeTool = self._activeTool()

        if activeTool.isFloatingXoverBegin():
            if mStrand.idx5Prime() == idx:
                return
            tempXover = activeTool.floatingXover()
            tempXover.updateBase(vhi, mStrand, idx)
            activeTool.setFloatingXoverBegin(False)
            # tempXover.hide5prime()
        else:
            activeTool.setFloatingXoverBegin(True)
            # install Xover
            activeTool.attemptToCreateXover(vhi, mStrand, idx)
    # end def

    # def selectToolMousePress(self, modifiers, event):
    #     """
    #     Set the allowed drag bounds for use by selectToolMouseMove.
    #     """
    #     print "mouse press ep", self.parentItem()
    #     # print "%s.%s [%d]" % (self, util.methodName(), self.idx())
    #     self._lowDragBound, self._highDragBound = \
    #                 self._strandItem._modelStrand.getResizeBounds(self.idx())
    #     sI = self._strandItem
    #     viewroot = sI.viewroot()
    #     selectionGroup = viewroot.strandItemSelectionGroup()
    #     selectionGroup.setInstantAdd(True)
    #     self.setSelected(True)
    # # end def

    def selectToolMousePress(self, modifiers, event, idx):
        """
        Set the allowed drag bounds for use by selectToolMouseMove.
        """
        # print "%s.%s [%d]" % (self, util.methodName(), self.idx())
        self._lowDragBound, self._highDragBound = \
                    self._strandItem._modelStrand.getResizeBounds(self.idx())
        sI = self._strandItem
        viewroot = sI.viewroot()
        currentFilterDict = viewroot.selectionFilterDict()
        if sI.strandFilter() in currentFilterDict \
                                    and self._filterName in currentFilterDict:
            selectionGroup = viewroot.strandItemSelectionGroup()
            mod = Qt.KeyboardModifier.MetaModifier
            if not (modifiers & mod):
                selectionGroup.clearSelection(False)
            selectionGroup.setSelectionLock(selectionGroup)
            selectionGroup.pendToAdd(self)
            selectionGroup.processPendingToAddList()
            return selectionGroup.mousePressEvent(event)
    # end def

    def selectToolMouseMove(self, modifiers, idx):
        """
        Given a new index (pre-validated as different from the prev index),
        calculate the new x coordinate for self, move there, and notify the
        parent strandItem to redraw its horizontal line.
        """
        idx = util.clamp(idx, self._lowDragBound, self._highDragBound)
        # x = int(idx * _baseWidth)
        # self.setPos(x, self.y())
        # self._strandItem.updateLine(self)
    # end def

    def selectToolMouseRelease(self, modifiers, x):
        """
        If the positional-calculated idx differs from the model idx, it means
        we have moved and should notify the model to resize.

        If the mouse event had a key modifier, perform special actions:
            shift = attempt to merge with a neighbor
            alt = extend to max drag bound
        """
        mStrand = self._strandItem._modelStrand
        baseIdx = int(floor(self.x() / _baseWidth))
        # if baseIdx != self.idx():
        #     newIdxs = self._getNewIdxsForResize(baseIdx)
        #     mStrand.resize(newIdxs)

        if modifiers & Qt.KeyboardModifier.AltModifier:
            if self._capType == 'low':
                newIdxs = self._getNewIdxsForResize(self._lowDragBound)
            else:
                newIdxs = self._getNewIdxsForResize(self._highDragBound)
            mStrand.resize(newIdxs)
        elif modifiers & Qt.KeyboardModifier.ShiftModifier:
            self.setSelected(False)
            self.restoreParent()
            mStrand.merge(self.idx())
    # end def

    def skipToolMousePress(self, modifiers, event, idx):
        """Add an insert to the strand if possible."""
        mStrand = self._strandItem._modelStrand
        mStrand.addInsertion(idx, -1)
    # end def

    def restoreParent(self, pos=None):
        """
        Required to restore parenting and positioning in the partItem
        """
        # map the position
        # print "restoring parent ep"
        self.tempReparent(pos)
        self.setSelectedColor(False)
        self.setSelected(False)
    # end def

    def tempReparent(self, pos=None):
        vhItem = self._strandItem.virtualHelixItem()
        if pos == None:
            pos = self.scenePos()
        self.setParentItem(vhItem)
        tempP = vhItem.mapFromScene(pos)
        self.setPos(tempP)
    # end def

    def setSelectedColor(self, value):
        if value == True:
            color = styles.selected_color
        else:
            oligo = self._strandItem.strand().oligo()
            color = QColor(oligo.color())
            if oligo.shouldHighlight():
                color.setAlpha(128)
        brush = self.brush()
        brush.setColor(color)
        self.setBrush(brush)
    # end def

    def updateHighlight(self, brush):
        if not self.isSelected():
            self.setBrush(brush)
    # end def

    def itemChange(self, change, value):
        # for selection changes test against QGraphicsItem.GraphicsItemChange.ItemSelectedChange
        # intercept the change instead of the has changed to enable features.
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange and self.scene():
            activeTool = self._activeTool()
            if str(activeTool) == "selectTool":
                sI = self._strandItem
                viewroot = sI.viewroot()
                currentFilterDict = viewroot.selectionFilterDict()
                selectionGroup = viewroot.strandItemSelectionGroup()

                # only add if the selectionGroup is not locked out
                if value == True and self._filterName in currentFilterDict:
                    # if self.group() != selectionGroup \
                    #                   and sI.strandFilter() in currentFilterDict:
                    if sI.strandFilter() in currentFilterDict:
                        if self.group() != selectionGroup or not self.isSelected():
                            selectionGroup.pendToAdd(self)
                            selectionGroup.setSelectionLock(selectionGroup)
                            self.setSelectedColor(True)
                        return True
                    else:
                        return False
                # end if
                elif value == True:
                    # don't select
                    return False
                else:
                    # Deselect
                    # Check if strand is being added to the selection group still
                    if not selectionGroup.isPending(self._strandItem):
                        selectionGroup.pendToRemove(self)
                        self.tempReparent()
                        self.setSelectedColor(False)
                        return False
                    else:   # don't deselect, because the strand is still selected
                        return True
                # end else
            # end if
            elif str(activeTool) == "paintTool":
                sI = self._strandItem
                viewroot = sI.viewroot()
                currentFilterDict = viewroot.selectionFilterDict()
                if sI.strandFilter() in currentFilterDict:
                    if not activeTool.isMacrod():
                        activeTool.setMacrod()
                    self.paintToolMousePress(None, None, None)
            # end elif
            return False
        # end if
        return QGraphicsPathItem.itemChange(self, change, value)
    # end def

    def modelDeselect(self, document):
        strand = self._strandItem.strand()
        test = document.isModelStrandSelected(strand)
        lowVal, highVal = document.getSelectedStrandValue(strand) if test \
                                                            else (False, False)
        if self._capType == 'low':
            outValue = (False, highVal)
        else:
            outValue = (lowVal, False)
        if not outValue[0] and not outValue[1] and test:
            document.removeStrandFromSelection(strand)
        elif outValue[0] or outValue[1]:
            document.addStrandToSelection(strand, outValue)
        self.restoreParent()
    # end def

    def modelSelect(self, document):
        strand = self._strandItem.strand()
        test = document.isModelStrandSelected(strand)
        lowVal, highVal = document.getSelectedStrandValue(strand) if test \
                                                            else (False, False)
        if self._capType == 'low':
            outValue = (True, highVal)
        else:
            outValue = (lowVal, True)
        self.setSelected(True)
        self.setSelectedColor(True)
        document.addStrandToSelection(strand, outValue)
    # end def

    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawPath(self.path())
    # end def
