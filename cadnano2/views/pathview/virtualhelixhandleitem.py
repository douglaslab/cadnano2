"""
pathhelixhandle.py
Created by Shawn on 2011-02-05.
"""
from cadnano2.views import styles

import cadnano2.util as util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QPointF', 'QRectF', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QBrush',
                                       'QFont',
                                       'QPen',
                                       'QDrag',
                                       'QTransform',
                                       'QUndoCommand'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsEllipseItem',
                                           'QGraphicsItem',
                                           'QGraphicsSimpleTextItem',
                                           'QGraphicsTextItem',
                                           'QStyle'])


_radius = styles.VIRTUALHELIXHANDLEITEM_RADIUS
_rect = QRectF(0, 0, 2*_radius + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH,\
        2*_radius + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_defBrush = QBrush(styles.grayfill)
_defPen = QPen(styles.graystroke, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_hovBrush = QBrush(styles.bluefill)
_hovPen = QPen(styles.bluestroke, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_useBrush = QBrush(styles.orangefill)
_usePen = QPen(styles.orangestroke, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_font = styles.VIRTUALHELIXHANDLEITEM_FONT


class VirtualHelixHandleItem(QGraphicsEllipseItem):
    """docstring for VirtualHelixHandleItem"""
    _filterName = "virtualHelix"
    
    def __init__(self, virtualHelix, partItem, viewroot):
        super(VirtualHelixHandleItem, self).__init__(partItem)
        self._virtualHelix = virtualHelix
        self._partItem = partItem
        self._viewroot = viewroot
        self._beingHoveredOver = False
        self.setAcceptHoverEvents(True)
        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setSelectedColor(False)
        self.setZValue(styles.ZPATHHELIX)
        self.setRect(_rect)
    # end def

    def setSelectedColor(self, value):
        if self.number() >= 0:
            if value == True:
                self.setBrush(_hovBrush)
                self.setPen(_hovPen)
            else:
                self.setBrush(_useBrush)
                self.setPen(_usePen)
        else:
            self.setBrush(_defBrush)
            self.setPen(_defPen)
        self.update(self.boundingRect())
    # end def
    
    def virtualHelix(self):
        return self._virtualHelix

    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawEllipse(self.rect())
    # end def

    def remove(self):
        scene = self.scene()
        scene.removeItem(self._label)
        scene.removeItem(self)
        self._label = None
    # end def

    def someVHChangedItsNumber(self, r, c):
        # If it was our VH, we need to update the number we
        # are displaying!
        if (r,c) == self.vhelix.coord():
            self.setNumber()
    # end def

    def createLabel(self):
        label = QGraphicsSimpleTextItem("%d" % self._virtualHelix.number())
        label.setFont(_font)
        label.setZValue(styles.ZPATHHELIX)
        label.setParentItem(self)
        return label
    # end def

    def setNumber(self):
        """docstring for setNumber"""
        vh = self._virtualHelix
        num = vh.number()
        label = self._label
        radius = _radius

        if num != None:
            label.setText("%d" % num)
        else:
            return
        y_val = radius / 3
        if num < 10:
            label.setPos(radius / 1.5, y_val)
        elif num < 100:
            label.setPos(radius / 3, y_val)
        else: # _number >= 100
            label.setPos(0, y_val)
        bRect = label.boundingRect()
        posx = bRect.width()/2
        posy = bRect.height()/2
        label.setPos(radius-posx, radius-posy)
    # end def

    def number(self):
        """docstring for number"""
        return self._virtualHelix.number()
        
    def partItem(self):
        return self._partItem
    # end def

    def hoverEnterEvent(self, event):
        """
        hoverEnterEvent changes the PathHelixHandle brush and pen from default
        to the hover colors if necessary.
        """
        if not self.isSelected():
            if self.number() >= 0:
                if self.isSelected():
                    self.setBrush(_hovBrush)
                else:
                    self.setBrush(_useBrush)
            else:
                self.setBrush(_defBrush)
            self.setPen(_hovPen)
            self.update(self.boundingRect())
    # end def

    def hoverLeaveEvent(self, event):
        """
        hoverEnterEvent changes the PathHelixHanle brush and pen from hover
        to the default colors if necessary.
        """
        if not self.isSelected():
            self.setSelectedColor(False)
            self.update(self.boundingRect())
    # end def

    def mousePressEvent(self, event):
        """
        All mousePressEvents are passed to the group if it's in a group
        """
        selectionGroup = self.group()
        if selectionGroup != None:
            selectionGroup.mousePressEvent(event)
        else:
            QGraphicsItem.mousePressEvent(self, event)
    # end def

    def mouseMoveEvent(self, event):
        """
        All mouseMoveEvents are passed to the group if it's in a group
        """
        selectionGroup = self.group()
        if selectionGroup != None:
            selectionGroup.mousePressEvent(event)
        else:
            QGraphicsItem.mouseMoveEvent(self, event)
    # end def

    def restoreParent(self, pos=None):
        """
        Required to restore parenting and positioning in the partItem
        """

        # map the position
        partItem = self._partItem
        if pos == None:
            pos = self.scenePos()
        self.setParentItem(partItem)
        self.setSelectedColor(False)

        assert(self.parentItem() == partItem)
        # print "restore", self.number(), self.parentItem(), self.group()
        assert(self.group() == None)
        tempP = partItem.mapFromScene(pos)
        self.setPos(tempP)
        self.setSelected(False)
    # end def

    def itemChange(self, change, value):
        # for selection changes test against QGraphicsItem.GraphicsItemChange.ItemSelectedChange
        # intercept the change instead of the has changed to enable features.

        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange and self.scene():
            viewroot = self._viewroot
            currentFilterDict = viewroot.selectionFilterDict()
            selectionGroup = viewroot.vhiHandleSelectionGroup()

            # only add if the selectionGroup is not locked out
            if value == True and self._filterName in currentFilterDict:
                if self.group() != selectionGroup:
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
                selectionGroup.pendToRemove(self)
                self.setSelectedColor(False)
                return False
            # end else
        # end if
        return QGraphicsEllipseItem.itemChange(self, change, value)
    # end def
    
    def modelDeselect(self, document):
        pass
        self.restoreParent()
    # end def
    
    def modelSelect(self, document):
        pass
        self.setSelected(True)
    # end def
# end class
