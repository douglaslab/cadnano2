"""
pathselection.py

Created by Nick on 2011-06-27.
"""

from cadnano2.views import styles
from math import floor
import cadnano2.util as util

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['Qt', 'QPointF', 'QEvent', 'QRectF'])
util.qtWrapImport('QtGui', globals(), ['QPen', 'QBrush', 'QColor',
                                       'QPainterPath'])
util.qtWrapImport('QtWidgets', globals(), [  # 'qApp',
                                           'QGraphicsItem',
                                           'QGraphicsItemGroup',
                                           'QGraphicsPathItem'])


class SelectionItemGroup(QGraphicsItemGroup):
    """
    SelectionItemGroup
    """
    def __init__(self, boxtype, constraint='y', parent=None):
        super(SelectionItemGroup, self).__init__(parent)
        self._viewroot = parent
        self.setFiltersChildEvents(True)

        # LOOK at Qt Source for deprecated code to replace this behavior
        # self.setHandlesChildEvents(True) # commented out NC

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)  # for keyPressEvents
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemHasNoContents)

        self._rect = QRectF()
        self._pen = QPen(styles.bluestroke, styles.PATH_SELECTBOX_STROKE_WIDTH)

        self.selectionbox = boxtype(self)

        self._dragEnable = False
        self._dragged = False
        self._baseClick = 0  # tri-state counter to enable deselection on click away

        self._r0 = 0  # save original mousedown
        self._r = 0  # latest position for moving

        # self._lastKid = 0

        # this keeps track of mousePressEvents within the class
        # to aid in intellignetly removing items from the group
        self._addedToPressList = False

        self._pendingToAddDict = {}

        if constraint == 'y':
            self.getR = self.selectionbox.getY
            self.translateR = self.selectionbox.translateY
        else:
            self.getR = self.selectionbox.getX
            self.translateR = self.selectionbox.translateX

        self._normalSelect = True
        self._instantAdd = 0

        self.setZValue(styles.ZPATHSELECTION)
    # end def

    # def paint(self, painter, option, widget):
    #     painter.drawRect(self.boundingRect())
    # # end def

    def pendToAdd(self, item):
        self._pendingToAddDict[item] = True
    # end def

    def isPending(self, item):
        return item in self._pendingToAddDict
    # end def
    
    def document(self):
        return self._viewroot.document()
    # end def
    
    def pendToRemove(self, item):
        if item in self._pendingToAddDict:
            del self._pendingToAddDict[item]
    # end def

    def setNormalSelect(self, boolVal):
        self._normalSelect = boolVal
    # end def

    def isNormalSelect(self):
        return self._normalSelect
    # end def

    def processPendingToAddList(self):
        """
        Adds to the local selection and the document if required
        """
        doc = self.document()

        # print "instant add is 1 from process pending"
        if len(self._pendingToAddDict) > 0:
            for item in self._pendingToAddDict:
                # print "just checking1", item, item.group(), item.parentItem()
                self.addToGroup(item)
                item.modelSelect(doc)
            # end for
            self._pendingToAddDict = {}
            doc.updateSelection()
    # end def

    def resetSelection(self):
        self._pendingToAddDict = {}
        self._addedToPressList = False
        self.clearSelection(False)
        self.setSelectionLock(None)
        self.selectionbox.setParentItem(self._viewroot)
        self.setParentItem(self._viewroot)
    # end def

    def selectionLock(self):
        return self._viewroot.selectionLock()
    # end def

    def setSelectionLock(self, selectionGroup):
        self._viewroot.setSelectionLock(selectionGroup)
    # end def

    # def paint(self, painter, option, widget=None):
    #     # painter.setBrush(QBrush(QColor(255,128,255,128)))
    #     painter.setPen(QPen(styles.redstroke))
    #     painter.drawRect(self.boundingRect())
    #     pass
    # # end def

    def keyPressEvent(self, event):
        """
        Must intercept invalid input events.  Make changes here
        """
        key = event.key()
        if key in [Qt.Key.Key_Backspace, Qt.Key.Key_Delete]:
            self.selectionbox.deleteSelection()
            # self.document().deleteSelection()
            self.clearSelection(False)
            return QGraphicsItemGroup.keyPressEvent(self, event)
        else:
            return QGraphicsItemGroup.keyPressEvent(self, event)
    # end def

    def mousePressEvent(self, event):
        # self.show()
        # print "instant add is 1 from MousePress"
        if event.button() != Qt.MouseButton.LeftButton:
            return QGraphicsItemGroup.mousePressEvent(self, event)
        else:
            self._dragEnable = True

            # required to get the itemChanged event to work
            # correctly for this
            self.setSelected(True)

            # self.selectionbox.resetTransform()
            self.selectionbox.resetPosition()
            self.selectionbox.refreshPath()

            # self.selectionbox.resetTransform()
            self.selectionbox.resetPosition()
            self.selectionbox.show()

            # for some reason we need to skip the first mouseMoveEvent
            self._dragged = False

            if self._addedToPressList == False:
                self._addedToPressList = True
                self.scene().views()[0].addToPressList(self)
            return QGraphicsItemGroup.mousePressEvent(self, event)
    # end def

    def mouseMoveEvent(self, event):
        if self._dragEnable == True:
            # map the item to the scene coordinates
            # to help keep coordinates uniform
            rf = self.getR(self.mapFromScene(QPointF(event.scenePos())))
            # for some reason we need to skip the first mouseMoveEvent
            if self._dragged == False:
                self._dragged = True
                self._r0 = rf
            # end if
            else:
                delta = self.selectionbox.delta(rf, self._r0)
                self.translateR(delta)
            # end else
            self._r = rf
        # end if
        else:
            QGraphicsItemGroup.mouseMoveEvent(self, event)
        # end else
    # end def

    def customMouseRelease(self, event):
        """docstring for customMouseRelease"""
        self.selectionbox.hide()
        self.selectionbox.resetTransform()
        self._dragEnable = False
        # now do stuff
        if not (self._r0 == 0 and self._r == 0):
            self.selectionbox.processSelectedItems(self._r0, self._r)
        # end if
        self._r0 = 0  # reset
        self._r = 0  # reset
        self.setFocus() # needed to get keyPresses post a move
        self._addedToPressList = False
    # end def

    def clearSelection(self, value):
        if value == False:
            self.selectionbox.hide()
            self.selectionbox.resetPosition()
            self.removeSelectedItems()
            self._viewroot.setSelectionLock(None)
            self.clearFocus()  # this is to disable delete keyPressEvents
            self.prepareGeometryChange()
            self._rect.setWidth(0)
            # self._rect = QRectF()
        # end if
        else:
            self.setFocus()  # this is to get delete keyPressEvents
        self.update(self.boundingRect())
    # end def

    def itemChange(self, change, value):
        """docstring for itemChange"""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value == False:
                self.clearSelection(False)
                return False
            else:
                return True
        elif change == QGraphicsItem.GraphicsItemChange.ItemChildAddedChange:
            if self._addedToPressList == False:
                # print "kid added"
                self.setFocus()  # this is to get delete keyPressEvents
                self.setParentItem(self.selectionbox.boxParent())
                self._addedToPressList = True
                self.scene().views()[0].addToPressList(self)
            return
        return QGraphicsItemGroup.itemChange(self, change, value)
    # end def

    def removeChild(self, child):
        """
        remove only the child and ask it to
        restore it's original parent
        """
        doc = self.document()
        tPos = child.scenePos()
        self.removeFromGroup(child)
        child.modelDeselect(doc)
    # end def

    def removeSelectedItems(self):
        """docstring for removeSelectedItems"""
        doc = self.document()
        for item in self.childItems():
            self.removeFromGroup(item)
            item.modelDeselect(doc)
        # end for
        doc.updateSelection()
    # end def

    def setBoundingRect(self, rect):
        self.prepareGeometryChange()
        self._rect = rect
    # end def

    def boundingRect(self):
        return self._rect

# end class


class VirtualHelixHandleSelectionBox(QGraphicsPathItem):
    """
    docstring for VirtualHelixHandleSelectionBox
    """
    _helixHeight = styles.PATH_HELIX_HEIGHT + styles.PATH_HELIX_PADDING
    _radius = styles.VIRTUALHELIXHANDLEITEM_RADIUS
    _penWidth = styles.SLICE_HELIX_HILIGHT_WIDTH
    _boxPen = QPen(styles.bluestroke, _penWidth)

    def __init__(self, itemGroup):
        """
        The itemGroup.parentItem() is expected to be a partItem
        """
        super(VirtualHelixHandleSelectionBox, self).__init__(
                                                        itemGroup.parentItem())
        self._itemGroup = itemGroup
        self._rect = itemGroup.boundingRect()
        self.hide()
        self.setPen(self._boxPen)
        self.setZValue(styles.ZPATHSELECTION)
        self._bounds = None
        self._pos0 = QPointF()
    # end def

    def getY(self, pos):
        pos = self._itemGroup.mapToScene(QPointF(pos))
        return pos.y()
    # end def

    def translateY(self, delta):
        self.setY(delta)
     # end def

    def refreshPath(self):
        self.prepareGeometryChange()
        self.setPath(self.painterPath())
        self._pos0 = self.pos()
    # end def

    def painterPath(self):
        iG = self._itemGroup
        # the childrenBoundingRect is necessary to get this to work
        rect = self.mapRectFromItem(iG, iG.childrenBoundingRect())
        radius = self._radius

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        path.moveTo(rect.right(),\
                         rect.center().y())
        path.lineTo(rect.right() + radius / 2,\
                         rect.center().y())
        return path
    # end def

    def processSelectedItems(self, rStart, rEnd):
        """docstring for processSelectedItems"""
        margin = styles.VIRTUALHELIXHANDLEITEM_RADIUS
        delta = (rEnd - rStart)  # r delta
        midHeight = (self.boundingRect().height()) / 2 - margin
        helixHeight = self._helixHeight

        if abs(delta) < midHeight:  # move is too short for reordering
            return
        if delta > 0:  # moved down, delta is positive
            indexDelta = int((delta - midHeight) / helixHeight)
        else:  # moved up, delta is negative
            indexDelta = int((delta + midHeight) / helixHeight)
        # sort on y to determine the extremes of the selection group
        items = sorted(self._itemGroup.childItems(), key=lambda vhhi: vhhi.y())
        partItem = items[0].partItem()
        partItem.reorderHelices(items[0].number(),\
                                items[-1].number(),\
                                indexDelta)
        partItem.updateStatusBar("")
    # end def

    def boxParent(self):
        temp = self._itemGroup.childItems()[0].partItem()
        self.setParentItem(temp)
        return temp
    # end def
    
    def deleteSelection(self):
        """
        Delete selection operates outside of the documents a virtual helices
        are not actually selected in the model
        """
        vHelices = [vhh.virtualHelix() for vhh in self._itemGroup.childItems()]
        uS = self._itemGroup.document().undoStack()
        uS.beginMacro("delete Virtual Helices")
        for vh in vHelices:
            vh.remove()
        uS.endMacro()
    # end def

    def bounds(self):
        return self._bounds
    # end def

    def delta(self, yf, y0):
        return yf - y0
    # end def

    def resetPosition(self):
        self.setPos(self._pos0)
    # end def
# end class


class EndpointHandleSelectionBox(QGraphicsPathItem):
    _penWidth = styles.SLICE_HELIX_HILIGHT_WIDTH
    _boxPen = QPen(styles.selected_color, _penWidth)
    _baseWidth = styles.PATH_BASE_WIDTH

    def __init__(self, itemGroup):
        """
        The itemGroup.parentItem() is expected to be a partItem
        """
        super(EndpointHandleSelectionBox, self).__init__(
                                                    itemGroup.parentItem())
        self._itemGroup = itemGroup
        self._rect = itemGroup.boundingRect()
        self.hide()
        self.setPen(self._boxPen)
        self.setZValue(styles.ZPATHSELECTION)
        self._bounds = (0, 0)
        self._pos0 = QPointF()
    # end def

    def getX(self, pos):
        return pos.x()
    # end def

    def translateX(self, delta):
        children = self._itemGroup.childItems()
        if children:
            pI = children[0].partItem()
            str = "+%d" % delta if delta >= 0 else "%d" % delta
            pI.updateStatusBar(str)
        self.setX(self._baseWidth * delta)
    # end def

    def resetPosition(self):
        self.setPos(self._pos0)

    def delta(self, xf, x0):
        boundL, boundH = self._bounds
        delta = int(floor((xf - x0) / self._baseWidth))
        if delta > 0 and delta > boundH:
            delta = boundH
        elif delta < 0 and abs(delta) > boundL:
            delta = -boundL
        return delta

    def refreshPath(self):
        tempLow, tempHigh = \
                    self._itemGroup._viewroot.document().getSelectionBounds()
        self._bounds = (tempLow, tempHigh)
        self.prepareGeometryChange()
        self.setPath(self.painterPath())
        self._pos0 = self.pos()
    # end def

    def painterPath(self):
        bw = self._baseWidth
        iG = self._itemGroup
        # the childrenBoundingRect is necessary to get this to work
        rectIG = iG.childrenBoundingRect()
        rect = self.mapRectFromItem(iG, rectIG)
        if rect.width() < bw:
            rect.adjust(-bw / 4, 0, bw / 2, 0)
        path = QPainterPath()
        path.addRect(rect)
        self._itemGroup.setBoundingRect(rectIG)

        # path.addRoundedRect(rect, radius, radius)
        # path.moveTo(rect.right(),\
        #                  rect.center().y())
        # path.lineTo(rect.right() + radius / 2,\
        #                  rect.center().y())
        return path
    # end def

    def processSelectedItems(self, rStart, rEnd):
        """docstring for processSelectedItems"""
        delta = self.delta(rEnd, rStart)
        self._itemGroup._viewroot.document().resizeSelection(delta)
    # end def
    
    def deleteSelection(self):
        self._itemGroup.document().deleteSelection()

    def boxParent(self):
        temp = self._itemGroup.childItems()[0].partItem()
        self.setParentItem(temp)
        return temp
    # end def

    def bounds(self):
        return self._bounds
    # end def
# end class
