#!/usr/bin/env python
# encoding: utf-8

import cadnano2.util as util
from .abstractdecoratoritem import AbstractDecoratorItem
from cadnano2.views import styles

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QPointF', 'QRectF', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QBrush',
                                       'QColor',
                                       'QFont',
                                       'QFontMetricsF',
                                       'QPainterPath',
                                       'QPen',
                                       'QTextCursor',
                                       'QTransform'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsItem',
                                           'QGraphicsPathItem',
                                           'QGraphicsRectItem',
                                           'QGraphicsTextItem',
                                           'QLabel',
                                           ])

_baseWidth = _bw = styles.PATH_BASE_WIDTH
_halfbaseWidth = _hbw = _baseWidth / 2
_offset1 = _baseWidth / 4
_offset2 = _bw * 0.75
_font = QFont(styles.thefont, 10, QFont.Weight.Bold)
_noPen = QPen(Qt.PenStyle.NoPen)
_defaultRect = QRectF(0, 0, _baseWidth, _baseWidth)
_bpen = QPen(styles.bluestroke, styles.INSERTWIDTH)

def _insertGen(path, start, c1, p1, c2):
    path.moveTo(start)
    path.quadTo(c1, p1)
    path.quadTo(c2, start)
# end def

def _xGen(path, p1, p2, p3, p4):
    path.moveTo(p1)
    path.lineTo(p2)
    path.moveTo(p3)
    path.lineTo(p4)
# end def

def _tGen(path, p1, p2, p3, p4):
    path.moveTo(p1)
    path.lineTo(p2)
    path.lineTo(p3)
    path.lineTo(p4)
# end def

# _skipPath = QPainterPath()
# _xGen(_skipPath,
#         _defaultRect.bottomLeft(),
#         _defaultRect.topRight(),
#         _defaultRect.topLeft(),
#         _defaultRect.bottomRight())

_pathStart = QPointF(_hbw, _hbw)
_pathMidUp = QPointF(_hbw, 0)
_pathLeftUp = QPointF(0, 0)
_pathRightUp = QPointF(_bw, 0)

_pathMidDown = QPointF(_hbw, _bw)
_pathLeftDown = QPointF(0, _bw)
_pathRightDown = QPointF(_bw, _bw)

_modPathUp = QPainterPath()
_tGen(_modPathUp, _pathStart, _pathMidUp, _pathLeftUp, _pathRightUp)
_modPathUp.translate(_offset1, 0)

_modPathDown = QPainterPath()
_tGen(_modPathDown, _pathStart, _pathMidDown, _pathLeftDown, _pathRightDown)
_modPathDown.translate(_offset1, 0)


class ModificationPath(object):
    """
    This is just the shape of the Modification item
    """

    def __init__(self):
        super(ModificationPath, self).__init__()
    # end def

    def getPen(self):
        return _bpen
    # end def

    def getModification(self, istop):
        if istop:
            return _modPathUp
        else:
            return _modPathDown
    # end def
# end class

_modificationPath = ModificationPath()


class ChemModificationItem(QGraphicsPathItem):
    """
    Item containing chemical modification data
    """

    def __init__(self, virtualHelixItem, strand, decorator):
        super(ChemModificationItem, self).__init__(virtualHelixItem)
        self.hide()
        self._strand = strand
        self._decorator = decorator
        self._seqItem = QGraphicsPathItem(parent=self)
        self._isOnTop = isOnTop = virtualHelixItem.isStrandOnTop(strand)
        y = 0 if isOnTop else _bw
        self.setPos(_bw * decorator.idx(), y)
        self.setZValue(styles.ZINSERTHANDLE)
        self._initLabel()
        self._initClickArea()
        self.updateItem()
        self.show()
    # end def

    def _initLabel(self,):
        """Display the length of the insertion."""
        self._label = label = QGraphicsTextItem("", parent=self)
        label.setFont(_font)
        label.setDefaultTextColor(QColor(self._strand.oligo().color()))
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        label.inputMethodEvent = self.inputMethodEventHandler
        label.keyPressEvent = self.textkeyPressEvent
        label.mousePressEvent = self.labelMousePressEvent
        label.mouseDoubleClickEvent = self.mouseDoubleClickEvent
        label.setTextWidth(-1)

        self._label = label
        self._seqItem = QGraphicsPathItem(parent=self)
        self._seqText = None
        self.updateItem()
        self.show()
    # end def

    def _initClickArea(self):
        """docstring for _initClickArea"""
        self._clickArea = cA = QGraphicsRectItem(_defaultRect, self)
        cA.setPen(_noPen)
        cA.mousePressEvent = self.mousePressEvent
        cA.mouseDoubleClickEvent = self.mouseDoubleClickEvent
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def remove(self):
        """
        Called from the following stranditem methods:
            strandRemovedSlot
            strandInsertionRemovedSlot
            refreshInsertionItems
        """
        scene = self.scene()
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self._label.clearFocus()
        scene.removeItem(self._label)
        self._label = None
        scene.removeItem(self._seqItem)
        self._seqItem = None
        scene.removeItem(self)
        self._insertion = None
        self._strand = None
    # end def

    def updateItem(self):
        self._updatePath()
        self._updateLabel()
        self._resetPosition()
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _focusOut(self):
        lbl = self._label
        if lbl is None:
            return
        cursor = lbl.textCursor()
        cursor.clearSelection()
        lbl.setTextCursor(cursor)
        lbl.clearFocus()
    # end def

    def _updateLabel(self):
        self._label.setPlainText(self._decorator.name())
    # end def

    def _updatePath(self):
        strand = self._strand
        if strand is None:
            self.hide()
            return
        else:
            self.show()
        self.setPen(QPen(QColor(strand.oligo().color()), styles.INSERTWIDTH))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.setPath(_modificationPath.getModification(self._isOnTop))
    # end def

    def _resetPosition(self):
        """
        Set the label position based on orientation and text alignment.
        """
        lbl = self._label
        if lbl is None:
            return
        txtOffset = lbl.boundingRect().width() / 2
        decorator = self._decorator
        y = -_bw if self._isOnTop else _bw
        lbl.setPos(_offset2 - txtOffset, y)
        if decorator.name():
            lbl.show()
        else:
            lbl.hide()
    # end def

    ### EVENT HANDLERS ###
    def mouseDoubleClickEvent(self, event):
        """Double clicks remove the decorator."""
        self._strand.removeDecorator(self._decorator.idx())

    def mousePressEvent(self, event):
        """This needs to be present for mouseDoubleClickEvent to work."""
        pass

    def labelMousePressEvent(self, event):
        """
        Pre-selects the text for editing when you click
        the label.
        """
        lbl = self._label
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        cursor = lbl.textCursor()
        cursor.setPosition(0)
        cursor.movePosition(QTextCursor.MoveOperation.End, mode=QTextCursor.MoveMode.KeepAnchor)
        lbl.setTextCursor(cursor)

    def textkeyPressEvent(self, event):
        """
        Must intercept invalid input events.  Make changes here
        """
        a = event.key()
        if a in [Qt.Key.Key_Space, Qt.Key.Key_Tab]:
            return
        elif a in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self.inputMethodEventHandler(event)
            return
        else:
            return QGraphicsTextItem.keyPressEvent(self._label, event)

    def inputMethodEventHandler(self, event):
        """
        This is run on the label being changed
        or losing focus
        """
        lbl = self._label
        if lbl is None:
            return
        new_name = str(lbl.toPlainText())
        decor = self._decorator
        if new_name and new_name != decor.name():
            self._strand.changeDecorator(decor.idx(), new_name)
            if decor.name():
                self._resetPosition()
        # end if
        self._focusOut()
    # end def
# end class
