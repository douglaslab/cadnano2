"""
xoveritem.py
Created by Nick on 2011-05-25.
"""

from cadnano2.views import styles
import cadnano2.util as util

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QPointF', 'QRectF', 'Qt', 'QEvent'])
util.qtWrapImport('QtGui', globals(), ['QBrush',
                                       'QFont',
                                       'QPen',
                                       'QPolygonF',
                                       'QPainterPath',
                                       'QColor',
                                       'QFontMetrics'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsItem',
                                           'QGraphicsSimpleTextItem',
                                           'QGraphicsRectItem',
                                           'QGraphicsPathItem'])

_baseWidth = styles.PATH_BASE_WIDTH
_toHelixNumFont = styles.XOVER_LABEL_FONT
# precalculate the height of a number font.  Assumes a fixed font
# and that only numbers will be used for labels
_fm = QFontMetrics(_toHelixNumFont)
_enabbrush = QBrush(Qt.BrushStyle.SolidPattern)  # Also for the helix number label
_nobrush = QBrush(Qt.BrushStyle.NoBrush)
# _rect = QRectF(0, 0, baseWidth, baseWidth)
_xScale = styles.PATH_XOVER_LINE_SCALE_X  # control point x constant
_yScale = styles.PATH_XOVER_LINE_SCALE_Y  # control point y constant
_rect = QRectF(0, 0, _baseWidth, _baseWidth)


class XoverNode3(QGraphicsRectItem):
    """
    This is a QGraphicsRectItem to allow actions and also a
    QGraphicsSimpleTextItem to allow a label to be drawn
    """
    def __init__(self, virtualHelixItem, xoverItem, strand3p, idx):
        super(XoverNode3, self).__init__(virtualHelixItem)
        self._vhi = virtualHelixItem
        self._xoverItem = xoverItem
        self._idx = idx
        self._isOnTop = virtualHelixItem.isStrandOnTop(strand3p)
        self._isDrawn5to3 = strand3p.strandSet().isDrawn5to3()
        self._strandType = strand3p.strandSet().strandType()

        self.setPartnerVirtualHelix(strand3p)

        self.setPen(QPen(Qt.PenStyle.NoPen))
        self._label = None
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(_nobrush)
        self.setRect(_rect)
        self.setZValue(styles.ZXOVERITEM)
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        self.scene().views()[0].addToPressList(self)
        self._vhi.setActive(self._idx)
        xoi = self._xoverItem
        toolMethodName = str(xoi.activeTool()) + "MousePress"
        if hasattr(xoi, toolMethodName):
            getattr(xoi, toolMethodName)()
    # end def

    def customMouseRelease(self, event):
        pass
    # end def

    def virtualHelix(self):
        return self._vhi.virtualHelix()
    # end def

    def strandType(self):
        return self._strandType
    # end def

    def refreshXover(self):
        self._xoverItem.refreshXover()
    # end def

    def setPartnerVirtualHelix(self,strand):
        if strand.connection5p():
            self._partnerVirtualHelix = strand.connection5p().virtualHelix()
        else:
            self._partnerVirtualHelix = None
    # end def

    def idx(self):
        return self._idx
    # end def

    def setIdx(self, idx):
        self._idx = idx
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

    def updatePositionAndAppearance(self):
        """
        Sets position by asking the VirtualHelixItem
        Sets appearance by choosing among pre-defined painterpaths (from
        normalstrandgraphicsitem) depending on drawing direction.
        """
        self.setPos(*self.point())
        # We can only expose a 5' end. But on which side?
        isLeft = True if self._isDrawn5to3 else False
        self._updateLabel(isLeft)
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
        if scene:
            scene.removeItem(self._label)
            self._label = None
            scene.removeItem(self)
    # end def

    def _updateLabel(self, isLeft):
        """
        Called by updatePositionAndAppearance during init, or later by
        updateConnectivity. Updates drawing and position of the label.
        """
        lbl = self._label
        if self._idx != None:
            if lbl == None:
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
                lbl = QGraphicsSimpleTextItem(str(num), self)
                lbl.setPos(labelX, labelY)
                lbl.setBrush(_enabbrush)
                lbl.setFont(_toHelixNumFont)
                self._label = lbl
            # end if
            lbl.setText( str(self._partnerVirtualHelix.number()) )
        # end if
    # end def

# end class


class XoverNode5(XoverNode3):
    """
    XoverNode5 is the partner of XoverNode3. It dif
    XoverNode3 handles:
    1. Drawing of the 5' end of an xover, and its text label. Drawing style
    is determined by the location of the xover with in a vhelix (is it a top
    or bottom vstrand?).
    2. Notifying XoverStrands in the model when connectivity changes.

    """
    def __init__(self, virtualHelixItem, xoverItem, strand5p, idx):
        super(XoverNode5, self).__init__(virtualHelixItem, xoverItem, strand5p, idx)
    # end def

    def setPartnerVirtualHelix(self, strand):
        if strand.connection3p():
            self._partnerVirtualHelix = strand.connection3p().virtualHelix()
        else:
            self._partnerVirtualHelix = None
    # end def

    def updatePositionAndAppearance(self):
        """Same as XoverItem3, but exposes 3' end"""
        self.setPos(*self.point())
        # # We can only expose a 3' end. But on which side?
        isLeft = False if self._isDrawn5to3 else True
        self._updateLabel(isLeft)
    # end def
# end class


class XoverItem(QGraphicsPathItem):
    """
    This class handles:
    1. Drawing the spline between the XoverNode3 and XoverNode5 graphics
    items in the path view.

    XoverItem should be a child of a PartItem.
    """
    _filterName = "xover"

    def __init__(self, strandItem, virtualHelixItem):
        """
        strandItem is a the model representation of the 5prime most strand
        of a Xover
        """
        super(XoverItem, self).__init__(virtualHelixItem.partItem())
        self._strandItem = strandItem
        self._virtualHelixItem = virtualHelixItem
        self._strand5p = None
        self._node5 = None
        self._node3 = None
        self.hide()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        # for easier mouseclick
        self._clickArea = cA = QGraphicsRectItem(self)
        # self._clickArea.setAcceptHoverEvents(True)
        # cA.hoverMoveEvent = self.hoverMoveEvent
        cA.mousePressEvent = self.mousePressEvent
        cA.mouseMoveEvent = self.mouseMoveEvent
        cA.setPen(QPen(Qt.PenStyle.NoPen))
    # end def

    ### SLOTS ###

    ### ACCESSORS ###
    def activeTool(self):
        return self._strandItem._activeTool()
    # end def

    def partItem(self):
        return self._virtualHelixItem.partItem()
    # end def

    def remove(self):
        scene = self.scene()
        if self._node3:
            self._node3.remove()
            self._node5.remove()
            self._node3 = None
            self._node5 = None
        self._strand5p = None
        scene.removeItem(self._clickArea)
        self._clickArea = None
        scene.removeItem(self)
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def hideIt(self):
        self.hide()
        if self._node3:
            self._node3.hide()
            self._node5.hide()
            self._node3.remove()
            self._node3 = None
    # end def

    def showIt(self):
        self.show()
        if self._node3:
            self._node3.show()
            self._node5.show()
    # end def

    def refreshXover(self):
        strand5p = self._strand5p
        node3 = self._node3
        if strand5p:
            strand3p = strand5p.connection3p()
            if strand3p != None and node3:
                if node3.virtualHelix():
                    self.update(self._strand5p)
                else:
                    node3.remove()
                    self._node3 = None
            elif node3:
                node3.remove()
                self._node3 = None
        elif node3:
            node3.remove()
            self._node3 = None
    # end def

    def update(self, strand5p, idx=None):
        """
        Pass idx to this method in order to install a floating
        Xover for the forced xover tool
        """
        self._strand5p = strand5p
        strand3p = strand5p.connection3p()
        vhi5p = self._virtualHelixItem
        partItem = vhi5p.partItem()

        # This condition is for floating xovers
        idx3Prime = idx if idx else strand5p.idx3Prime()

        if self._node5 == None:
            self._node5 = XoverNode5(vhi5p, self, strand5p, idx3Prime)
        if strand3p != None:
            if self._node3 == None:
                vhi3p = partItem.itemForVirtualHelix(strand3p.virtualHelix())
                self._node3 = XoverNode3(vhi3p, self, strand3p, strand3p.idx5Prime())
            else:
                self._node5.setIdx(idx3Prime)
                self._node3.setIdx(strand3p.idx5Prime())
            self._node5.setPartnerVirtualHelix(strand5p)
            self._updatePath(strand5p)
        else:
            if self._node3:
                self._node3.remove()
                self._node3 = None
        # end if
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _updatePath(self, strand5p):
        """
        Draws a quad curve from the edge of the fromBase
        to the top or bottom of the toBase (q5), and
        finally to the center of the toBase (toBaseEndpoint).

        If floatPos!=None, this is a floatingXover and floatPos is the
        destination point (where the mouse is) while toHelix, toIndex
        are potentially None and represent the base at floatPos.

        """
        group = self.group()
        self.tempReparent()

        node3 = self._node3
        node5 = self._node5

        bw = _baseWidth

        parent = self.partItem()

        vhi5 = self._virtualHelixItem
        pt5 = vhi5.mapToItem(parent, *node5.point())

        fiveIsTop = node5.isOnTop()
        fiveIs5to3 = node5.isDrawn5to3()

        vhi3 = node3.virtualHelixItem()
        pt3 = vhi3.mapToItem(parent, *node3.point())

        threeIsTop = node3.isOnTop()
        threeIs5to3 = node3.isDrawn5to3()
        sameStrand = (node5.strandType() == node3.strandType()) and vhi3 == vhi5
        sameParity = fiveIs5to3 == threeIs5to3

        # Enter/exit are relative to the direction that the path travels
        # overall.
        fiveEnterPt = pt5 + QPointF(0 if fiveIs5to3 else 1, .5)*bw
        fiveCenterPt = pt5 + QPointF(.5, .5)*bw
        fiveExitPt = pt5 + QPointF(.5, 0 if fiveIsTop else 1)*bw

        threeEnterPt = pt3 + QPointF(.5, 0 if threeIsTop else 1)*bw
        threeCenterPt = pt3 + QPointF(.5, .5)*bw
        threeExitPt = pt3 + QPointF(1 if threeIs5to3 else 0, .5)*bw

        c1 = QPointF()
        # case 1: same strand
        if sameStrand:
            dx = abs(threeEnterPt.x() - fiveExitPt.x())
            c1.setX(0.5 * (fiveExitPt.x() + threeEnterPt.x()))
            if fiveIsTop:
                c1.setY(fiveExitPt.y() - 0.05 * _yScale * dx)  # almost flat
            else:
                c1.setY(fiveExitPt.y() + 0.05 * _yScale * dx)  # almost flat
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

        # The xover5's non-crossing-over end (3') has a connection
        painterpath.quadTo(c1, threeEnterPt)
        painterpath.lineTo(threeCenterPt)
        painterpath.lineTo(threeExitPt)

        tempR = painterpath.boundingRect()
        tempR.adjust(-bw/2, 0, bw, 0)
        self._clickArea.setRect(tempR)
        self.setPath(painterpath)
        node3.updatePositionAndAppearance()
        node5.updatePositionAndAppearance()

        if group:
            group.addToGroup(self)

        self._updateColor(strand5p)
    # end def

    def updateLabels(self):
        if self._node3:
            self._node3._updateLabel()
        if self._node5:
            self._node5._updateLabel()

    def _updateColor(self, strand):
        oligo = strand.oligo()
        color = self.pen().color() if self.isSelected() else QColor(oligo.color())
        # print "update xover color", color.value(), self.isSelected(), self.group(), self.parentItem()
        penWidth = styles.PATH_STRAND_STROKE_WIDTH
        if oligo.shouldHighlight():
            penWidth = styles.PATH_STRAND_HIGHLIGHT_STROKE_WIDTH
            color.setAlpha(128)

        pen = QPen(color, penWidth)

        if self._node3 and self._node5:
            vhi5 = self._node5.virtualHelixItem()
            vhi3 = self._node3.virtualHelixItem()
            sameStrand = (self._node5.strandType() == self._node3.strandType()) and vhi3 == vhi5
            if sameStrand:
                pen.setStyle(Qt.PenStyle.DashLine)
                pen.setDashPattern([3, 2])

        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        self.setPen(pen)
    # end def

    ### EVENT HANDERS ###
    def mousePressEvent(self, event):
        """
        Special case for xovers and select tool, for now
        """
        if str(self.activeTool()) == "selectTool":
            event.setAccepted(False)
            sI = self._strandItem
            viewroot = sI.viewroot()
            currentFilterDict = viewroot.selectionFilterDict()
            if sI.strandFilter() in currentFilterDict and self._filterName in currentFilterDict:
                event.setAccepted(True)
                selectionGroup = viewroot.strandItemSelectionGroup()
                mod = Qt.KeyboardModifier.MetaModifier
                if not (event.modifiers() & mod):
                    selectionGroup.clearSelection(False)
                selectionGroup.setSelectionLock(selectionGroup)
                # self.setSelectedColor(True)
                selectionGroup.pendToAdd(self)
                selectionGroup.processPendingToAddList()
                return selectionGroup.mousePressEvent(event)
        else:
            event.setAccepted(False)
    # end def

    def eraseToolMousePress(self):
        """Erase the strand."""
        self._strandItem.eraseToolMousePress(None, None)
    # end def

    def paintToolMousePress(self):
        """Paint the strand."""
        self._strandItem.paintToolMousePress(None, None)
    # end def

    def selectToolMousePress(self):
        """Remove the xover."""
        # make sure the selection is clear
        sI = self._strandItem
        viewroot = sI.viewroot()
        selectionGroup = viewroot.strandItemSelectionGroup()
        selectionGroup.clearSelection(False)

        strand5p = self._strand5p
        strand3p = strand5p.connection3p()
        self._virtualHelixItem.part().removeXover(strand5p, strand3p)
    # end def

    def restoreParent(self, pos=None):
        """
        Required to restore parenting and positioning in the partItem
        """
        # map the position
        self.tempReparent(pos)
        self.setSelectedColor(False)
        self.setSelected(False)
    # end def

    def tempReparent(self, pos=None):
        partItem = self.partItem()
        if pos == None:
            pos = self.scenePos()
        self.setParentItem(partItem)
        tempP = partItem.mapFromScene(pos)
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
        pen = self.pen()
        pen.setColor(color)
        self.setPen(pen)
    # end def

    def itemChange(self, change, value):
        # for selection changes test against QGraphicsItem.GraphicsItemChange.ItemSelectedChange
        # intercept the change instead of the has changed to enable features.
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange and self.scene():
            activeTool = self.activeTool()
            if str(activeTool) == "selectTool":
                sI = self._strandItem
                viewroot = sI.viewroot()
                currentFilterDict = viewroot.selectionFilterDict()
                selectionGroup = viewroot.strandItemSelectionGroup()
                # only add if the selectionGroup is not locked out
                if value == True and (self._filterName in currentFilterDict or not selectionGroup.isNormalSelect()):
                    if sI.strandFilter() in currentFilterDict:
                        # print "might add a xoi"
                        if self.group() != selectionGroup and selectionGroup.isNormalSelect():
                            # print "adding an xoi"
                            selectionGroup.pendToAdd(self)
                            selectionGroup.setSelectionLock(selectionGroup)
                        self.setSelectedColor(True)
                        return True
                    else:
                        # print "Doh"
                        return False
                # end if
                elif value == True:
                    # print "DOink"
                    return False
                else:
                    # Deselect
                    # Check if the strand is being added to the selection group still
                    if not selectionGroup.isPending(self._strandItem):
                        selectionGroup.pendToRemove(self)
                        self.tempReparent()
                        self.setSelectedColor(False)
                        return False
                    else:   # don't deselect it, because the strand is selected still
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
                    self.paintToolMousePress()
            return False
        # end if
        return QGraphicsPathItem.itemChange(self, change, value)
    # end def

    def modelDeselect(self, document):
        strand5p = self._strand5p
        strand3p = strand5p.connection3p()
        test5p = document.isModelStrandSelected(strand5p)
        lowVal5p, highVal5p = document.getSelectedStrandValue(strand5p) if test5p else (False, False)
        if strand5p.isDrawn5to3():
            highVal5p = False
        else:
            lowVal5p = False
        test3p = document.isModelStrandSelected(strand3p)
        lowVal3p, highVal3p = document.getSelectedStrandValue(strand3p) if test3p else (False, False)
        if strand3p.isDrawn5to3():
            lowVal3p = False
        else:
            highVal3p = False

        if not lowVal5p and not highVal5p and test5p:
            document.removeStrandFromSelection(strand5p)
        elif test5p:
            document.addStrandToSelection(strand5p, (lowVal5p, highVal5p))
        if not lowVal3p and not highVal3p and test3p:
            document.removeStrandFromSelection(strand3p)
        elif test3p:
            document.addStrandToSelection(strand3p, (lowVal3p, highVal3p))
        self.restoreParent()
    # end def

    def modelSelect(self, document):
        strand5p = self._strand5p
        strand3p = strand5p.connection3p()

        test5p = document.isModelStrandSelected(strand5p)
        lowVal5p, highVal5p = document.getSelectedStrandValue(strand5p) if test5p else (False, False)
        if strand5p.isDrawn5to3():
            highVal5p = True
        else:
            lowVal5p = True
        test3p = document.isModelStrandSelected(strand3p)
        lowVal3p, highVal3p = document.getSelectedStrandValue(strand3p) if test3p else (False, False)
        if strand3p.isDrawn5to3():
            lowVal3p = True
        else:
            highVal3p = True
        self.setSelectedColor(True)
        self.setSelected(True)
        document.addStrandToSelection(strand5p, (lowVal5p, highVal5p))
        document.addStrandToSelection(strand3p, (lowVal3p, highVal3p))
    # end def

    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawPath(self.path())
    # end def
# end class XoverItem
