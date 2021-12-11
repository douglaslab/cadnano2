#!/usr/bin/env python
# encoding: utf-8

import cadnano2.util as util
from cadnano2.views import styles

from cadnano2.model.enum import StrandType

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QPointF', 'QRectF', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QBrush',
                                       'QFont',
                                       'QFontMetrics',
                                       'QPainterPath',
                                       'QPolygonF',
                                       'QPen',
                                       'QUndoCommand'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsPathItem',
                                           'QGraphicsRectItem',
                                           'QGraphicsSimpleTextItem'])

# construct paths for breakpoint handles
def _hashMarkGen(path, p1, p2, p3):
    path.moveTo(p1)
    path.lineTo(p2)
    path.lineTo(p3)
# end

# create hash marks QPainterPaths only once
_ppRect = QRectF(0, 0, styles.PATH_BASE_WIDTH, styles.PATH_BASE_WIDTH)
_pathCenter = QPointF(styles.PATH_BASE_WIDTH / 2,\
                          styles.PATH_BASE_WIDTH / 2)
_pathUCenter = QPointF(styles.PATH_BASE_WIDTH / 2, 0)
_pathDCenter = QPointF(styles.PATH_BASE_WIDTH / 2, styles.PATH_BASE_WIDTH)
_ppathLU = QPainterPath()
_hashMarkGen(_ppathLU, _ppRect.bottomLeft(), _pathDCenter, _pathCenter)
_ppathRU = QPainterPath()
_hashMarkGen(_ppathRU, _ppRect.bottomRight(), _pathDCenter, _pathCenter)
_ppathRD = QPainterPath()
_hashMarkGen(_ppathRD, _ppRect.topRight(), _pathUCenter, _pathCenter)
_ppathLD = QPainterPath()
_hashMarkGen(_ppathLD, _ppRect.topLeft(), _pathUCenter, _pathCenter)

_scafpen = QPen(styles.pxi_scaf_stroke, styles.PATH_STRAND_STROKE_WIDTH)
_scafpen.setCapStyle(Qt.PenCapStyle.FlatCap)  # or Qt.RoundCap
_scafpen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
_stappen = QPen(styles.pxi_stap_stroke, styles.PATH_STRAND_STROKE_WIDTH)
_stappen.setCapStyle(Qt.PenCapStyle.FlatCap)  # or Qt.RoundCap
_stappen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
_disabpen = QPen(styles.pxi_disab_stroke, styles.PATH_STRAND_STROKE_WIDTH)
_disabpen.setCapStyle(Qt.PenCapStyle.FlatCap)
_disabpen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
_disabbrush = QBrush(styles.pxi_disab_stroke)  # For the helix number label
_enabbrush = QBrush(Qt.BrushStyle.SolidPattern)  # Also for the helix number label
_baseWidth = styles.PATH_BASE_WIDTH
_rect = QRectF(0, 0, styles.PATH_BASE_WIDTH, 1.2*styles.PATH_BASE_WIDTH)
_toHelixNumFont = styles.XOVER_LABEL_FONT
# precalculate the height of a number font.  Assumes a fixed font
# and that only numbers will be used for labels
_fm = QFontMetrics(_toHelixNumFont)

class PreXoverItem(QGraphicsPathItem):
    def __init__(self,  fromVirtualHelixItem, toVirtualHelixItem, index, strandType, isLowIdx):
        super(PreXoverItem, self).__init__(fromVirtualHelixItem)
        self._fromVHItem = fromVirtualHelixItem
        self._toVHItem = toVirtualHelixItem
        self._idx = index
        self._strandType = strandType
        # translate from Low to Left for the Path View
        self._isLowIndex = isLowIdx
        self._isActive = False
        self._pen = _scafpen if strandType == StrandType.Scaffold else _stappen
        isOnTop = fromVirtualHelixItem.isStrandTypeOnTop(strandType)

        bw = _baseWidth
        x = bw * index
        y = (-1.25 if isOnTop else 2.25) * bw
        self.setPos(x, y)

        num = toVirtualHelixItem.number()
        tBR = _fm.tightBoundingRect(str(num))
        halfLabelH = tBR.height()/2.0
        halfLabelW = tBR.width()/2.0

        labelX = bw/2.0 - halfLabelW #
        if num == 1:  # adjust for the number one
            labelX -= halfLabelW/2.0

        if isOnTop:
            labelY = -0.25*halfLabelH - .5
        else:
            labelY = 2*halfLabelH + .5

        self._label = QGraphicsSimpleTextItem(self)
        self._label.setPos(labelX, labelY)

        # create a bounding rect item to process click events
        # over a wide area
        self._clickArea = cA = QGraphicsRectItem(_rect, self)
        cA.mousePressEvent = self.mousePress
        yoffset = 0.2*bw if isOnTop else -0.4*bw
        cA.setPos(0, yoffset)
        cA.setPen(QPen(Qt.PenStyle.NoPen))

        self.updateStyle()
        self._updateLabel()
        self.setPainterPath()
    # end def

    ### DRAWING METHODS ###
    def remove(self):
        scene = self.scene()
        if scene:
            scene.removeItem(self._label)
            scene.removeItem(self._clickArea)
            scene.removeItem(self)
        self._label = None
        self._clickArea = None
        self._fromVHItem = None
        self._toVHItem = None
    # end def

    def setPainterPath(self):
        """
        Sets the PainterPath according to the index (low = Left, high = Right)
        and strand position (top = Up, bottom = Down).
        """
        pathLUT = (_ppathRD, _ppathRU, _ppathLD, _ppathLU)  # Lookup table
        vhi = self._fromVHItem
        st = self._strandType
        path = pathLUT[2*int(self._isLowIndex) + int(vhi.isStrandTypeOnTop(st))]
        self.setPath(path)
    # end def

    def updateStyle(self):
        """
        If a PreXover can be installed the pen is a bold color,
        otherwise the PreXover is drawn with a disabled or muted color
        """
        fromVH = self._fromVHItem.virtualHelix()
        toVH = self._toVHItem.virtualHelix()
        part = self._fromVHItem.part()
        pen = _disabpen
        self._labelBrush = _disabbrush
        if part.possibleXoverAt(fromVH, toVH, self._strandType, self._idx):
            pen = self._pen
            self._isActive = True
            self._labelBrush = _enabbrush
        self.setPen(pen)
    # end def

    def _updateLabel(self):
        lbl = self._label
        lbl.setBrush(self._labelBrush)
        lbl.setFont(_toHelixNumFont)
        lbl.setText( str(self._toVHItem.number() ) )
    # end def

    ### TOOL METHODS ###
    def selectToolMousePress(self, event):
        """removexover(fromStrand, fromIdx, toStrand, toIdx)"""
        pass
    # end def

    def mousePress(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return QGraphicsPathItem.mousePressEvent(self, event)

        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            return  # ignore shift click, user is probably trying to merge

        if self._isActive:
            fromVH = self._fromVHItem.virtualHelix()
            toVH = self._toVHItem.virtualHelix()
            fromSS = fromVH.getStrandSetByType(self._strandType)
            toSS = toVH.getStrandSetByType(self._strandType)
            fromStrand = fromSS.getStrand(self._idx)
            toStrand = toSS.getStrand(self._idx)
            part = self._fromVHItem.part()
            # determine if we are a 5' or a 3' end
            if self.path() in [_ppathLU, _ppathRD]:  # 3' end of strand5p clicked
                strand5p = fromStrand
                strand3p = toStrand
            else:  # 5'
                strand5p = toStrand
                strand3p = fromStrand

            # Gotta clear selections when installing a prexover
            # otherwise parenting in screwed up
            self._fromVHItem.viewroot().clearStrandSelections()

            part.createXover(strand5p, self._idx, strand3p, self._idx)
        else:
            event.setAccepted(False)
    # end def
    