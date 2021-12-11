from cadnano2.views import styles
from cadnano2.model.enum import StrandType

import cadnano2.util as util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QPointF', 'QRectF', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QBrush', 'QFont', 'QPen'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsItem',
                                           'QGraphicsItemGroup',
                                           'QGraphicsObject'])


_bw = styles.PATH_BASE_WIDTH
_toolRect = QRectF(0, 0, _bw, _bw)  # protected not private
_rect = QRectF(-styles.PATH_BASE_HL_STROKE_WIDTH,
               -styles.PATH_BASE_HL_STROKE_WIDTH,
               _bw + 2*styles.PATH_BASE_HL_STROKE_WIDTH,
               _bw + 2*styles.PATH_BASE_HL_STROKE_WIDTH)
_pen = QPen(styles.redstroke, styles.PATH_BASE_HL_STROKE_WIDTH)
_brush = QBrush(Qt.BrushStyle.NoBrush)

# There's a bug where C++ will free orphaned graphics items out from
# under pyqt. To avoid this, "_mother" adopts orphaned graphics items.
_mother = QGraphicsItemGroup()


class AbstractPathTool(QGraphicsObject):
    """Abstract base class to be subclassed by all other pathview tools."""
    def __init__(self, controller, parent=None):
        super(AbstractPathTool, self).__init__(parent)
        self._controller = controller
        self._window = controller.window
        self._active = False
        self._lastLocation = None

    ######################## Drawing #######################################
    def paint(self, painter, option, widget=None):
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawRect(self._toolRect)

    def boundingRect(self):
        return self._rect

    ######################### Positioning and Parenting ####################
    def hoverEnterVirtualHelixItem(self, virtualHelixItem, event):
        self.updateLocation(virtualHelixItem, virtualHelixItem.mapToScene(QPointF(event.position())))

    def hoverLeaveVirtualHelixItem(self, virtualHelixItem, event):
        self.updateLocation(None, virtualHelixItem.mapToScene(QPointF(event.position())))

    def hoverMoveVirtualHelixItem(self, virtualHelixItem, event, flag=None):
        self.updateLocation(virtualHelixItem, virtualHelixItem.mapToScene(QPointF(event.position())))

    def updateLocation(self, virtualHelixItem, scenePos, *varargs):
        """Takes care of caching the location so that a tool switch
        outside the context of an event will know where to
        position the new tool and snaps self's pos to the upper
        left hand corner of the base the user is mousing over"""
        if virtualHelixItem:
            if self.parentObject() != virtualHelixItem:
                self.setParentItem(virtualHelixItem)
            self._lastLocation = (virtualHelixItem, scenePos)
            posItem = virtualHelixItem.mapFromScene(scenePos)
            pos = self.helixPos(posItem)
            if pos != None:
                if pos != self.pos():
                    self.setPos(pos)
                self.update(self.boundingRect())
                if not self.isVisible():
                    self.show()
                    pass
        else:
            self._lastLocation = None
            if self.isVisible():
                self.hide()
            if self.parentItem() != _mother:
                self.setParentItem(_mother)

    def lastLocation(self):
        """A tuple (virtualHelixItem, QPoint) representing the last
        known location of the mouse for purposes of positioning
        the graphic of a new tool on switching tools (the tool
        will have updateLocation(*oldTool.lastLocation()) called
        on it)"""
        return self._lastLocation

    def setActive(self, willBeActive, oldTool=None):
        """
        Called by PathToolManager.setActiveTool when the tool becomes
        active. Used, for example, to show/hide tool-specific ui elements.
        """
        if self.isActive() and not willBeActive:
            self.setParentItem(_mother)
            self.hide()

    def isActive(self):
        """Returns isActive"""
        return self._active != _mother

    def widgetClicked(self):
        """Called every time a widget representing self gets clicked,
        not just when changing tools."""
        pass

    ####################### Coordinate Utilities ###########################
    def baseAtPoint(self, virtualHelixItem, pt):
        """Returns the (strandType, baseIdx) corresponding
        to pt in virtualHelixItem."""
        x, strandIdx = self.helixIndex(pt)
        vh = virtualHelixItem.virtualHelix()
        if vh.isEvenParity():
            strandType = (StrandType.Scaffold, StrandType.Staple)[util.clamp(strandIdx, 0, 1)]
        else:
            strandType = (StrandType.Staple, StrandType.Scaffold)[util.clamp(strandIdx, 0, 1)]
        return (strandType, x, strandIdx)

    def helixIndex(self, point):
        """
        Returns the (row, col) of the base which point
        lies within.
        point is in virtualHelixItem coordinates.
        """
        x = int(int(point.x()) / _bw)
        y = int(int(point.y()) / _bw)
        return (x, y)
    # end def

    def helixPos(self, point):
        """
        Snaps a point to the upper left corner of the base
        it is within.
        point is in virtualHelixItem coordinates
        """
        col = int(int(point.x()) / _bw)
        row = int(int(point.y()) / _bw)
        # Doesn't know numBases, can't check if point is too far right
        if col < 0 or row < 0 or row > 1:
            return None
        return QPointF(col*_bw, row*_bw)
    # end def
# end class