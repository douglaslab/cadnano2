from math import floor
from .abstractpathtool import AbstractPathTool
from cadnano2.views import styles

import cadnano2.util as util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['Qt', 'QEvent', 'QPointF', 'QRectF'])
util.qtWrapImport('QtGui', globals(), ['QBrush',
                                       'QColor',
                                       'QFont',
                                       'QFontMetrics',
                                       'QPainterPath',
                                       'QPolygonF',
                                       'QPen'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsItem',
                                           'QGraphicsLineItem',
                                           'QGraphicsPathItem',
                                           'QGraphicsRectItem',
                                           'QGraphicsSimpleTextItem'])


_baseWidth = styles.PATH_BASE_WIDTH
_pencilcolor = styles.redstroke
_defaultRect = QRectF(0,0, _baseWidth, _baseWidth)
_noPen = QPen(Qt.PenStyle.NoPen)


class PencilTool(AbstractPathTool):
    """
    docstring for PencilTool
    """
    def __init__(self, controller):
        super(PencilTool, self).__init__(controller)
        self._tempXover = ForcedXoverItem(self, None, None)
        self._tempStrandItem = ForcedStrandItem(self, None)
        self._tempStrandItem.hide()
        self._moveIdx = None
        self._isFloatingXoverBegin = True
        self._isDrawingStrand = False

    def __repr__(self):
        return "pencilTool"  # first letter should be lowercase

    def strandItem(self):
        return self._tempStrandItem
    # end def

    def isDrawingStrand(self):
        return self._isDrawingStrand
    # end def

    def setIsDrawingStrand(self, boolval):
        self._isDrawingStrand = boolval
        if boolval == False:
            self._tempStrandItem.hideIt()
    # end def

    def initStrandItemFromVHI(self, virtualHelixItem, strandSet, idx):
        sI = self._tempStrandItem
        self._startIdx = idx
        self._startStrandSet = strandSet
        sI.resetStrandItem(virtualHelixItem, strandSet.isDrawn5to3())
        self._lowDragBound, self._highDragBound = strandSet.getBoundsOfEmptyRegionContaining(idx)
    # end def

    def updateStrandItemFromVHI(self, virtualHelixItem, strandSet, idx):
        sI = self._tempStrandItem
        sIdx = self._startIdx
        if abs(sIdx-idx) > 1 and self.isWithinBounds(idx):
            idxs = (idx, sIdx) if self.isDragLow(idx) else (sIdx, idx)
            sI.strandResizedSlot(idxs)
            sI.showIt()
        # end def
    # end def

    def isDragLow(self, idx):
        sIdx = self._startIdx
        if sIdx-idx > 0:
            return True
        else:
            return False
    # end def

    def isWithinBounds(self, idx):
        return self._lowDragBound <= idx <= self._highDragBound
    # end def

    def attemptToCreateStrand(self, virtualHelixItem, strandSet, idx):
        self._tempStrandItem.hideIt()
        sIdx = self._startIdx
        if abs(sIdx-idx) > 1:
            idx = util.clamp(idx, self._lowDragBound, self._highDragBound)
            idxs = (idx, sIdx) if self.isDragLow(idx) else (sIdx, idx)
            self._startStrandSet.createStrand(*idxs)
    # end def

    def floatingXover(self):
        return self._tempXover
    # end def

    def isFloatingXoverBegin(self):
        return self._isFloatingXoverBegin
    # end def

    def setFloatingXoverBegin(self, boolval):
        self._isFloatingXoverBegin = boolval
        if boolval:
            self._tempXover.hideIt()
        else:
            self._tempXover.showIt()
    # end def

    def attemptToCreateXover(self, virtualHelixItem, strand3p, idx):
        xoi = self._tempXover
        n5 = xoi._node5 
        idx5 = n5._idx
        strand5p = n5._strand
        part = virtualHelixItem.part()
        part.createXover(strand5p, idx5, strand3p, idx)
    # end def
# end class


class ForcedStrandItem(QGraphicsLineItem):
    def __init__(self, tool, virtualHelixItem):
        """The parent should be a VirtualHelixItem."""
        super(ForcedStrandItem, self).__init__(virtualHelixItem)
        self._virtualHelixItem = virtualHelixItem
        self._tool = tool

        isDrawn5to3 = True

        # caps
        self._lowCap = EndpointItem(self, 'low', isDrawn5to3)
        self._highCap = EndpointItem(self, 'high', isDrawn5to3)
        self._lowCap.disableEvents()
        self._highCap.disableEvents()
        
        # orientation
        self._isDrawn5to3 = isDrawn5to3

        # create a larger click area rect to capture mouse events
        self._clickArea = cA = QGraphicsRectItem(_defaultRect, self)
        cA.mousePressEvent = self.mousePressEvent
        cA.setPen(_noPen)

        # cA.setBrush(QBrush(Qt.white))
        self.setZValue(styles.ZENDPOINTITEM+1)
        cA.setZValue(styles.ZENDPOINTITEM)
        self._lowCap.setZValue(styles.ZENDPOINTITEM+2)
        self._highCap.setZValue(styles.ZENDPOINTITEM+2)
        cA.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)

        self._updatePensAndBrushes()
        self.hideIt()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def strandResizedSlot(self, idxs):
        """docstring for strandResizedSlot"""
        lowMoved = self._lowCap.updatePosIfNecessary(idxs[0])
        highMoved = self._highCap.updatePosIfNecessary(idxs[1])
        if lowMoved:
            self.updateLine(self._lowCap)
        if highMoved:
            self.updateLine(self._highCap)
    # end def

    def strandRemovedSlot(self):
        scene = self.scene()
        scene.removeItem(self._clickArea)
        scene.removeItem(self._highCap)
        scene.removeItem(self._lowCap)

        self._clickArea = None
        self._highCap = None
        self._lowCap = None

        scene.removeItem(self)
    # end def

    ### ACCESSORS ###

    def virtualHelixItem(self):
        return self._virtualHelixItem

    def activeTool(self):
        return self._tool
    # end def

    def hideIt(self):
        self.hide()
        self._lowCap.hide()
        self._highCap.hide()
        self._clickArea.hide()
    # end def

    def showIt(self):
        self._lowCap.show()
        self._highCap.show()
        self._clickArea.show()
        self.show()
    # end def

    def resetStrandItem(self, virtualHelixItem, isDrawn5to3):
        self.setParentItem(virtualHelixItem)
        self._virtualHelixItem = virtualHelixItem
        self.resetEndPointItems(isDrawn5to3)
    # end def

    def resetEndPointItems(self, isDrawn5to3):
        bw = _baseWidth
        self._isDrawn5to3 = isDrawn5to3
        self._lowCap.resetEndPoint(isDrawn5to3)
        self._highCap.resetEndPoint(isDrawn5to3)
        line = self.line()
        p1 = line.p1()
        p2 = line.p2()
        if isDrawn5to3:
            p1.setY(bw/2)
            p2.setY(bw/2)
            self._clickArea.setY(0)
        else:
            p1.setY(3*bw/2)
            p2.setY(3*bw/2)
            self._clickArea.setY(bw)
        line.setP1(p1)
        line.setP2(p2)
        self.setLine(line)
    # end def

    ### PUBLIC METHODS FOR DRAWING / LAYOUT ###
    def updateLine(self, movedCap):
        # setup
        bw = _baseWidth
        cA = self._clickArea
        line = self.line()
        # set new line coords
        if movedCap == self._lowCap:
            p1 = line.p1()
            newX = self._lowCap.pos().x() + bw
            p1.setX(newX)
            line.setP1(p1)
            temp = cA.rect()
            temp.setLeft(newX-bw)
            cA.setRect(temp)
        else:
            p2 = line.p2()
            newX = self._highCap.pos().x()
            p2.setX(newX)
            line.setP2(p2)
            temp = cA.rect()
            temp.setRight(newX+bw)
            cA.setRect(temp)
        self.setLine(line)
    # end def

    def _updatePensAndBrushes(self):
        color = QColor(_pencilcolor)
        penWidth = styles.PATH_STRAND_STROKE_WIDTH
        pen = QPen(color, penWidth)
        brush = QBrush(color)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        self.setPen(pen)
        self._lowCap.setBrush(brush)
        self._highCap.setBrush(brush)
    # end def
# end class

_toHelixNumFont = styles.XOVER_LABEL_FONT
# precalculate the height of a number font.  Assumes a fixed font
# and that only numbers will be used for labels
_fm = QFontMetrics(_toHelixNumFont)
_enabbrush = QBrush(Qt.BrushStyle.SolidPattern)  # Also for the helix number label
_noBrush = QBrush(Qt.BrushStyle.NoBrush)

# _rect = QRectF(0, 0, baseWidth, baseWidth)
_xScale = styles.PATH_XOVER_LINE_SCALE_X  # control point x constant
_yScale = styles.PATH_XOVER_LINE_SCALE_Y  # control point y constant
_rect = QRectF(0, 0, _baseWidth, _baseWidth)
_blankRect = QRectF(0, 0, 2*_baseWidth, _baseWidth)

ppL5 = QPainterPath()  # Left 5' PainterPath
ppR5 = QPainterPath()  # Right 5' PainterPath
ppL3 = QPainterPath()  # Left 3' PainterPath
ppR3 = QPainterPath()  # Right 3' PainterPath

# set up ppL5 (left 5' blue square)
ppL5.addRect(0.25*_baseWidth, 0.125*_baseWidth,0.75*_baseWidth, 0.75*_baseWidth)
# set up ppR5 (right 5' blue square)
ppR5.addRect(0, 0.125*_baseWidth, 0.75*_baseWidth, 0.75*_baseWidth)
# set up ppL3 (left 3' blue triangle)
l3poly = QPolygonF()
l3poly.append(QPointF(_baseWidth, 0))
l3poly.append(QPointF(0.25*_baseWidth, 0.5*_baseWidth))
l3poly.append(QPointF(_baseWidth, _baseWidth))
ppL3.addPolygon(l3poly)
# set up ppR3 (right 3' blue triangle)
r3poly = QPolygonF()
r3poly.append(QPointF(0, 0))
r3poly.append(QPointF(0.75*_baseWidth, 0.5*_baseWidth))
r3poly.append(QPointF(0, _baseWidth))
ppR3.addPolygon(r3poly)

class ForcedXoverNode3(QGraphicsRectItem):
    """
    This is a QGraphicsRectItem to allow actions and also a 
    QGraphicsSimpleTextItem to allow a label to be drawn
    """
    def __init__(self, virtualHelixItem, xoverItem, strand3p, idx):
        super(ForcedXoverNode3, self).__init__(virtualHelixItem)
        self._vhi = virtualHelixItem
        self._xoverItem = xoverItem
        self._idx = idx
        self._isOnTop = virtualHelixItem.isStrandOnTop(strand3p)
        self._isDrawn5to3 = strand3p.strandSet().isDrawn5to3()
        self._strandType = strand3p.strandSet().strandType()

        self._partnerVirtualHelix = virtualHelixItem

        self._blankThing = QGraphicsRectItem(_blankRect, self)
        self._blankThing.setBrush(QBrush(Qt.GlobalColor.white))
        self._pathThing = QGraphicsPathItem(self)
        self.configurePath()

        self.setPen(_noPen)
        self._label = None
        self.setPen(_noPen)
        self.setBrush(_noBrush)
        self.setRect(_rect)

        self.setZValue(styles.ZENDPOINTITEM+1)
    # end def

    def updateForFloatFromVHI(self, virtualHelixItem, strandType, idxX, idxY):
        """

        """
        self._vhi = virtualHelixItem
        self.setParentItem(virtualHelixItem)
        self._strandType = strandType
        self._idx = idxX
        self._isOnTop = self._isDrawn5to3 = True if idxY == 0 else False
        self.updatePositionAndAppearance(isFromStrand=False)
    # end def

    def updateForFloatFromStrand(self, virtualHelixItem, strand3p, idx):
        """

        """
        self._vhi = virtualHelixItem
        self._strand = strand3p
        self.setParentItem(virtualHelixItem)
        self._idx = idx
        self._isOnTop = virtualHelixItem.isStrandOnTop(strand3p)
        self._isDrawn5to3 = strand3p.strandSet().isDrawn5to3()
        self._strandType = strand3p.strandSet().strandType()
        self.updatePositionAndAppearance()
    # end def

    def strandType(self):
        return self._strandType
    # end def

    def configurePath(self):
        self._pathThing.setBrush(QBrush(styles.redstroke))
        path = ppR3 if self._isDrawn5to3 else ppL3
        offset = -_baseWidth if self._isDrawn5to3 else _baseWidth
        self._pathThing.setPath(path)
        self._pathThing.setPos(offset, 0)

        offset = -_baseWidth if self._isDrawn5to3 else 0
        self._blankThing.setPos(offset, 0)

        self._blankThing.show()
        self._pathThing.show()
    # end def

    def refreshXover(self):
        self._xoverItem.refreshXover()
    # end def

    def setPartnerVirtualHelix(self, virtualHelixItem):
        self._partnerVirtualHelix = virtualHelixItem
    # end def

    def idx(self):
        return self._idx
    # end def

    def virtualHelixItem(self):
        return self._vhi
    # end def

    def point(self):
        return self._vhi.upperLeftCornerOfBaseType(self._idx, self._strandType)
    # end def

    def floatPoint(self):
        pt = self.pos()
        return pt.x(), pt.y()
    # end def

    def isOnTop(self):
        return self._isOnTop
    # end def

    def isDrawn5to3(self):
        return self._isDrawn5to3
    # end def

    def updatePositionAndAppearance(self, isFromStrand=True):
        """
        Sets position by asking the VirtualHelixItem
        Sets appearance by choosing among pre-defined painterpaths (from
        normalstrandgraphicsitem) depending on drawing direction.
        """
        self.setPos(*self.point())
        n5 = self._xoverItem._node5
        if isFromStrand:
            fromStrand, fromIdx = (n5._strand, n5._idx) if n5 != self else (None, None)
            if self._strand.canInstallXoverAt(self._idx, fromStrand, fromIdx):
                self.configurePath()
                # We can only expose a 5' end. But on which side?
                isLeft = True if self._isDrawn5to3 else False
                self._updateLabel(isLeft)
            else:
                self.hideItems()
        else:
            self.hideItems()
    # end def

    def updateConnectivity(self):
        isLeft = True if self._isDrawn5to3 else False
        self._updateLabel(isLeft)
    # end def

    def remove(self):
        """
        Clean up this joint
        """
        scene = self.scene()
        scene.removeItem(self._label)
        self._label = None
        scene.removeItem(self._pathThing)
        self._pathThing = None
        scene.removeItem(self._blankThing)
        self._blankThing = None
        scene.removeItem(self)
    # end def

    def _updateLabel(self, isLeft):
        """
        Called by updatePositionAndAppearance during init, or later by
        updateConnectivity. Updates drawing and position of the label.
        """
        lbl = self._label
        if self._idx != None:
            bw = _baseWidth
            num = self._partnerVirtualHelix.number()
            tBR = _fm.tightBoundingRect(str(num))
            halfLabelH = tBR.height()/2.0
            halfLabelW = tBR.width()/2.0
            # determine x and y positions
            labelX = bw/2.0 - halfLabelW
            if self._isOnTop:
                labelY = -0.25*halfLabelH - 0.5 - 0.5*bw
            else:
                labelY = 2*halfLabelH + 0.5 + 0.5*bw
            # adjust x for left vs right
            labelXoffset = 0.25*bw if isLeft else -0.25*bw
            labelX += labelXoffset
            # adjust x for numeral 1
            if num == 1: labelX -= halfLabelW/2.0
            # create text item
            if lbl == None:
                lbl = QGraphicsSimpleTextItem(str(num), self)
            lbl.setPos(labelX, labelY)
            lbl.setBrush(_enabbrush)
            lbl.setFont(_toHelixNumFont)
            self._label = lbl

            lbl.setText( str(self._partnerVirtualHelix.number()) )
            lbl.show()
        # end if
    # end def

    def hideItems(self):
        if self._label:
            self._label.hide()
        if self._blankThing:
            self._pathThing.hide()
        if self._blankThing:
            self._blankThing.hide()
    # end def
# end class


class ForcedXoverNode5(ForcedXoverNode3):
    """
    XoverNode5 is the partner of XoverNode3. It dif
    XoverNode3 handles:
    1. Drawing of the 5' end of an xover, and its text label. Drawing style
    is determined by the location of the xover with in a vhelix (is it a top
    or bottom vstrand?).
    2. Notifying XoverStrands in the model when connectivity changes.

    """
    def __init__(self, virtualHelixItem, xoverItem, strand5p, idx):
        super(ForcedXoverNode5, self).__init__(virtualHelixItem, xoverItem, strand5p, idx)
    # end def

    def configurePath(self):
        self._pathThing.setBrush(QBrush(styles.redstroke))
        path = ppL5 if self._isDrawn5to3 else ppR5
        offset = _baseWidth if self._isDrawn5to3 else -_baseWidth
        self._pathThing.setPath(path)
        self._pathThing.setPos(offset, 0)

        offset = 0 if self._isDrawn5to3 else -_baseWidth
        self._blankThing.setPos(offset, 0)

        self._blankThing.show()
        self._pathThing.show()
    # end def

    def updatePositionAndAppearance(self, isFromStrand=True):
        """Same as XoverItem3, but exposes 3' end"""
        self.setPos(*self.point())
        self.configurePath()
        # # We can only expose a 3' end. But on which side?
        isLeft = False if self._isDrawn5to3 else True
        self._updateLabel(isLeft)
    # end def
# end class

class ForcedXoverItem(QGraphicsPathItem):
    """
    This class handles:
    1. Drawing the spline between the XoverNode3 and XoverNode5 graphics
    items in the path view.

    XoverItem should be a child of a PartItem.
    """

    def __init__(self, tool, partItem, virtualHelixItem):
        """
        strandItem is a the model representation of the 5prime most strand
        of a Xover
        """
        super(ForcedXoverItem, self).__init__(partItem)
        self._tool = tool
        self._virtualHelixItem = virtualHelixItem
        self._strandType = None
        self._node5 = None
        self._node3 = None
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable) # for keyPressEvents
        self.setZValue(styles.ZPATHTOOL)
        self.hide()
    # end def

    ### SLOTS ###

    ### METHODS ###
    def remove(self):
        scene = self.scene()
        if self._node3:
            scene.removeItem(self._node3)
            scene.removeItem(self._node5)
        scene.removeItem(self)
    # end def

    def strandType(self):
        return self._strandType
    # end def
    
    def hide5prime(self):
        self._node5._pathThing.hide()

    def hide3prime(self):
        self._node3._pathThing.hide()
        
    def show3prime(self):
        if self._node3._blankThing.isVisible():
            self._node3._pathThing.show()

    def hideIt(self):
        self.hide()
        self.clearFocus()
        if self._node3:
            self._node3.hide()
            self._node5.hide()
    # end def

    def showIt(self):
        self.show()
        self.setFocus()
        if self._node3:
            self._node3.show()
            self._node5.show()
    # end def

    def keyPressEvent(self, event):
        """
        Must intercept invalid input events.  Make changes here
        """
        a = event.key()
        if a in [Qt.Key.Key_Control, Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down]:
            QGraphicsPathItem.keyPressEvent(self, event)
        else:
            self._tool.setFloatingXoverBegin(True)
    # end def

    def updateBase(self, virtualHelixItem, strand5p, idx):
        # floating Xover!
        self._virtualHelixItem = virtualHelixItem
        self.setParentItem(virtualHelixItem.partItem())
        self._strandType = strand5p.strandSet().strandType()
        if self._node5 == None:
            self._node5 = ForcedXoverNode5(virtualHelixItem, self, strand5p, idx)
            self._node3 = ForcedXoverNode3(virtualHelixItem, self, strand5p, idx)
        self._node5.updateForFloatFromStrand(virtualHelixItem, strand5p, idx)
        self._node3.updateForFloatFromStrand(virtualHelixItem, strand5p, idx)
        self.updateFloatPath()
    # end def

    def updateFloatingFromVHI(self, virtualHelixItem, strandType, idxX, idxY):
        # floating Xover!
        self._node5.setPartnerVirtualHelix(virtualHelixItem)
        self._node5.updatePositionAndAppearance()
        self._node3.setPartnerVirtualHelix(self._virtualHelixItem)
        self._node3.updateForFloatFromVHI(virtualHelixItem, strandType, idxX, idxY)
        self.updateFloatPath()
    # end def

    def updateFloatingFromStrandItem(self, virtualHelixItem, strand3p, idx):
        # floating Xover!
        self._node3.updateForFloatFromStrand(virtualHelixItem, strand3p, idx)
        self.updateFloatPath()
    # end def

    def updateFloatingFromPartItem(self, partItem, pt):
        self._node3.hideItems()
        self.updateFloatPath(pt)
    # end def

    def updateFloatPath(self, point=None):
        """
        Draws a quad curve from the edge of the fromBase
        to the top or bottom of the toBase (q5), and
        finally to the center of the toBase (toBaseEndpoint).

        If floatPos!=None, this is a floatingXover and floatPos is the
        destination point (where the mouse is) while toHelix, toIndex
        are potentially None and represent the base at floatPos.

        """
        node3 = self._node3
        node5 = self._node5

        bw = _baseWidth

        vhi5 = self._virtualHelixItem
        partItem = vhi5.partItem()
        pt5 = vhi5.mapToItem(partItem, *node5.floatPoint())

        fiveIsTop = node5.isOnTop()
        fiveIs5to3 = node5.isDrawn5to3()

        # Enter/exit are relative to the direction that the path travels
        # overall.
        fiveEnterPt = pt5 + QPointF(0 if fiveIs5to3 else 1, .5)*bw
        fiveCenterPt = pt5 + QPointF(.5, .5)*bw
        fiveExitPt = pt5 + QPointF(.5, 0 if fiveIsTop else 1)*bw

        vhi3 = node3.virtualHelixItem()

        if point:
            pt3 = point
            threeIsTop = True
            threeIs5to3 = True
            sameStrand = False
            sameParity = False
            threeEnterPt = threeCenterPt = threeExitPt = pt3
        else: 
            pt3 = vhi3.mapToItem(partItem, *node3.point())
            threeIsTop = node3.isOnTop()
            threeIs5to3 = node3.isDrawn5to3()
            sameStrand = (node5.strandType() == node3.strandType()) and vhi3 == vhi5
            sameParity = fiveIs5to3 == threeIs5to3

            threeEnterPt = pt3 + QPointF(.5, 0 if threeIsTop else 1)*bw
            threeCenterPt = pt3 + QPointF(.5, .5)*bw
            threeExitPt = pt3 + QPointF(1 if threeIs5to3 else 0, .5)*bw

        c1 = QPointF()
        # case 1: same strand
        if sameStrand:
            dx = abs(threeEnterPt.x() - fiveExitPt.x())
            c1.setX(0.5 * (fiveExitPt.x() + threeEnterPt.x()))
            if fiveIsTop:
                c1.setY(fiveExitPt.y() - _yScale * dx)
            else:
                c1.setY(fiveExitPt.y() + _yScale * dx)
            # case 2: same parity
        elif sameParity:
             dy = abs(threeEnterPt.y() - fiveExitPt.y())
             c1.setX(fiveExitPt.x() + _xScale * dy)
             c1.setY(0.5 * (fiveExitPt.y() + threeEnterPt.y()))
        # case 3: different parity
        else:
            if fiveIsTop and fiveIs5to3:
                c1.setX(fiveExitPt.x() - _xScale *\
                        abs(threeEnterPt.y() - fiveExitPt.y()))
            else:
                c1.setX(fiveExitPt.x() + _xScale *\
                        abs(threeEnterPt.y() - fiveExitPt.y()))
            c1.setY(0.5 * (fiveExitPt.y() + threeEnterPt.y()))

        # Construct painter path
        painterpath = QPainterPath()
        painterpath.moveTo(fiveEnterPt)
        painterpath.lineTo(fiveCenterPt)
        painterpath.lineTo(fiveExitPt)
        painterpath.quadTo(c1, threeEnterPt)
        painterpath.lineTo(threeCenterPt)
        painterpath.lineTo(threeExitPt)

        self.setPath(painterpath)
        self._updateFloatPen()
    # end def

    # def _updatePen(self, strand5p):
    #     oligo = strand5p.oligo()
    #     color = QColor(oligo.color())
    #     penWidth = styles.PATH_STRAND_STROKE_WIDTH
    #     if oligo.shouldHighlight():
    #         penWidth = styles.PATH_STRAND_HIGHLIGHT_STROKE_WIDTH
    #         color.setAlpha(128)
    #     pen = QPen(color, penWidth)
    #     pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    #     self.setPen(pen)
    # # end def

    def _updateFloatPen(self):
        penWidth = styles.PATH_STRAND_STROKE_WIDTH
        pen = QPen(_pencilcolor, penWidth)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        self.setPen(pen)
    # end def
# end class XoverItem

util.qtWrapImport('QtGui', globals(), ['QPolygonF'])

ppL5 = QPainterPath()  # Left 5' PainterPath
ppR5 = QPainterPath()  # Right 5' PainterPath
ppL3 = QPainterPath()  # Left 3' PainterPath
ppR3 = QPainterPath()  # Right 3' PainterPath
pp53 = QPainterPath()  # Left 5', Right 3' PainterPath
pp35 = QPainterPath()  # Left 5', Right 3' PainterPath
# set up ppL5 (left 5' blue square)
ppL5.addRect(0.25*_baseWidth, 0.125*_baseWidth,0.75*_baseWidth, 0.75*_baseWidth)
# set up ppR5 (right 5' blue square)
ppR5.addRect(0, 0.125*_baseWidth, 0.75*_baseWidth, 0.75*_baseWidth)
# set up ppL3 (left 3' blue triangle)
l3poly = QPolygonF()
l3poly.append(QPointF(_baseWidth, 0))
l3poly.append(QPointF(0.25*_baseWidth, 0.5*_baseWidth))
l3poly.append(QPointF(_baseWidth, _baseWidth))
ppL3.addPolygon(l3poly)
# set up ppR3 (right 3' blue triangle)
r3poly = QPolygonF()
r3poly.append(QPointF(0, 0))
r3poly.append(QPointF(0.75*_baseWidth, 0.5*_baseWidth))
r3poly.append(QPointF(0, _baseWidth))
ppR3.addPolygon(r3poly)

# single base left 5'->3'
pp53.addRect(0, 0.125*_baseWidth, 0.5*_baseWidth, 0.75*_baseWidth)
poly53 = QPolygonF()
poly53.append(QPointF(0.5*_baseWidth, 0))
poly53.append(QPointF(_baseWidth, 0.5*_baseWidth))
poly53.append(QPointF(0.5*_baseWidth, _baseWidth))
pp53.addPolygon(poly53)
# single base left 3'<-5'
pp35.addRect(0.50*_baseWidth, 0.125*_baseWidth, 0.5*_baseWidth, 0.75*_baseWidth)
poly35 = QPolygonF()
poly35.append(QPointF(0.5*_baseWidth, 0))
poly35.append(QPointF(0, 0.5*_baseWidth))
poly35.append(QPointF(0.5*_baseWidth, _baseWidth))
pp35.addPolygon(poly35)

class EndpointItem(QGraphicsPathItem):
    def __init__(self, strandItem, captype, isDrawn5to3):
        """The parent should be a StrandItem."""
        super(EndpointItem, self).__init__(strandItem.virtualHelixItem())

        self._strandItem = strandItem
        self._activeTool = strandItem.activeTool()
        self._capType = captype
        self._lowDragBound = None
        self._highDragBound = None
        self._initCapSpecificState(isDrawn5to3)
        self.setPen(_noPen)
        # for easier mouseclick
        self._clickArea = cA = QGraphicsRectItem(_defaultRect, self)
        self._clickArea.setAcceptHoverEvents(True)
        cA.hoverMoveEvent = self.hoverMoveEvent
        cA.mousePressEvent = self.mousePressEvent
        cA.mouseMoveEvent = self.mouseMoveEvent
        cA.setPen(_noPen)
        
    # end def

    def __repr__(self):
        return "%s" % self.__class__.__name__

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
        x = int(idx*_baseWidth)
        if x != self.x():
            self.setPos(x, self.y())
            return True
        return False

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
        if activeToolStr == 'pencilTool':
            return self._strandItem.pencilToolMousePress(self.idx())
        toolMethodName = activeToolStr + "MousePress"
        if hasattr(self, toolMethodName):  # if the tool method exists
            modifiers = event.modifiers()
            getattr(self, toolMethodName)(modifiers)  # call tool method

    def hoverMoveEvent(self, event):
        """
        Parses a mousePressEvent, calling the approproate tool method as
        necessary. Stores _moveIdx for future comparison.
        """
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
            idx = int(floor((self.x()+event.position().x()) / _baseWidth))
            if idx != self._moveIdx:  # did we actually move?
                modifiers = event.modifiers()
                self._moveIdx = idx
                getattr(self, toolMethodName)(modifiers, idx)  # call tool method

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
# end class