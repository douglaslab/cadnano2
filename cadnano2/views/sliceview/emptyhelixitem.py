"""
helixitem.py
Created by Nick on 2011-09-28.
"""
import re
from cadnano2.cadnano import app
from cadnano2.model.enum import StrandType
from cadnano2.views import styles
import cadnano2.util as util

try:
    from OpenGL import GL
except:
    GL = False

GL = False

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QPointF', 'QRectF', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QBrush', 'QFont', 'QPen', 'QDrag',
                                       'QTransform',
                                       'QUndoCommand'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsPathItem',
                                           'QGraphicsEllipseItem',
                                           'QGraphicsItem',
                                           'QGraphicsRectItem',
                                           'QGraphicsSimpleTextItem',
                                           'QGraphicsTextItem',
                                           'QStyle'])

# strand addition stores some meta information in the UndoCommand's text
_strand_re = re.compile("\((\d+),(\d+)\)\.0\^(\d+)")


class EmptyHelixItem(QGraphicsEllipseItem):
    """docstring for EmptyHelixItem"""
    # set up default, hover, and active drawing styles
    _defaultBrush = QBrush(styles.grayfill)
    _defaultPen = QPen(styles.graystroke, styles.SLICE_HELIX_STROKE_WIDTH)
    _hoverBrush = QBrush(styles.bluefill)
    _hoverPen = QPen(styles.bluestroke, styles.SLICE_HELIX_HILIGHT_WIDTH)
    _radius = styles.SLICE_HELIX_RADIUS
    temp = styles.SLICE_HELIX_STROKE_WIDTH
    _defaultRect = QRectF(0, 0, 2 * _radius, 2 * _radius)
    temp = (styles.SLICE_HELIX_HILIGHT_WIDTH - temp)/2
    _hoverRect = _defaultRect.adjusted(-temp, -temp, temp, temp)
    _ZDefault = styles.ZSLICEHELIX 
    _ZHovered = _ZDefault+1 
    temp /= 2
    _adjustmentPlus = (temp, temp)
    _adjustmentMinus = (-temp, -temp)
    # _PI = 3.141592
    # _temp = [x*_PI*0.1 for x in range(20)]
    # _temp = [(math.sin(angle) * _radius, math.cos(angle) * _radius) for angle in _temp]

    def __init__(self, row, column, partItem):
        """
        row, column is a coordinate in Lattice terms
        partItem is a PartItem that will act as a QGraphicsItem parent
        """
        super(EmptyHelixItem, self).__init__(parent=partItem)
        self._partItem = partItem
        self._lastvh = None  # for decideAction
        self.hide()
        self._isHovered = False
        self.setAcceptHoverEvents(True)

        self.setNotHovered()

        x, y = partItem.part().latticeCoordToPositionXY(row, column, partItem.scaleFactor())
        self.setPos(x, y)
        self._coord = (row, column)
        self.show()
    # end def

    def virtualHelix(self):
        """
        virtualHelixItem should be the HelixItems only child if it exists
        and virtualHelix should be it member
        """
        temp = self.virtualHelixItem()
        if temp:
            return temp.virtualHelix()
        else:
            return None
    # end def

    def virtualHelixItem(self):
        """
        virtualHelixItem should be the HelixItems only child if it exists
        and virtualHelix should be it member
        """
        temp = self.childItems()
        if len(temp) > 0:
            return temp[0]
        else:
            return None
    # end def

    def part(self):
        return self._partItem.part()
    # end def

    def translateVH(self, delta):
        """
        used to update a child virtual helix position on a hover event
        delta is a tuple of x and y values to translate

        positive delta happens when hover happens
        negative delta when something unhovers
        """
        temp = self.virtualHelixItem()

        # xor the check to translate, 
        # convert to a QRectF adjustment if necessary
        check = (delta > 0) ^ self._isHovered
        if temp and check:
            pass
            # temp.translate(*delta)
    # end def

    def setHovered(self):
        # self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemHasNoContents, False)
        self.setBrush(self._hoverBrush)
        self.setPen(self._hoverPen)
        self.update(self.boundingRect())
        # self.translateVH(self._adjustmentPlus)
        self._isHovered = True
        self.setZValue(self._ZHovered)
        self.setRect(self._hoverRect)

        self._partItem.updateStatusBar("(%d, %d)" % self._coord)
    # end def

    def hoverEnterEvent(self, event):
        """
        hoverEnterEvent changes the HelixItem brush and pen from default
        to the hover colors if necessary.
        """
        self.setHovered()
    # end def

    def setNotHovered(self):
        """
        """
        # drawMe = False if self.virtualHelixItem() else True
        # self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemHasNoContents, drawMe)
        self.setBrush(self._defaultBrush)
        self.setPen(self._defaultPen)
        # self.translateVH(self._adjustmentMinus)
        self._isHovered = False
        self.setZValue(self._ZDefault)
        self.setRect(self._defaultRect)

        self._partItem.updateStatusBar("")
    # end def

    def hoverLeaveEvent(self, event):
        """
        hoverEnterEvent changes the HelixItem brush and pen from hover
        to the default colors if necessary.
        """
        self.setNotHovered()
    # end def

    def mousePressEvent(self, event):
        action = self.decideAction(event.modifiers())
        action(self)
        self.dragSessionAction = action
    # end def

    def mouseMoveEvent(self, event):
        partItem = self._partItem
        posInParent = partItem.mapFromItem(self, QPointF(event.pos()))
        # Qt doesn't have any way to ask for graphicsitem(s) at a
        # particular position but it *can* do intersections, so we
        # just use those instead
        partItem.probe.setPos(posInParent)
        for ci in partItem.probe.collidingItems():
            if isinstance(ci, EmptyHelixItem):
                self.dragSessionAction(ci)
    # end def

    def autoScafMidSeam(self, strands):
        """docstring for autoScafMidSeam"""
        part = self.part()
        strandType = StrandType.Scaffold
        idx = part.activeBaseIndex()
        for i in range(1, len(strands)):
            row1, col1, sSidx1 = strands[i-1]  # previous strand
            row2, col2, sSidx2 = strands[i]  # current strand
            vh1 = part.virtualHelixAtCoord((row1, col1))
            vh2 = part.virtualHelixAtCoord((row2, col2))
            strand1 = vh1.scaffoldStrandSet()._strandList[sSidx1]
            strand2 = vh2.scaffoldStrandSet()._strandList[sSidx2]
            # determine if the pair of strands are neighbors
            neighbors = part.getVirtualHelixNeighbors(vh1)
            if vh2 in neighbors:
                p2 = neighbors.index(vh2)
                if vh2.number() % 2 == 1:
                    # resize and install external xovers
                    try:
                        # resize to the nearest prexover on either side of idx
                        newLo = util.nearest(idx, part.getPreXoversHigh(strandType, p2, maxIdx=idx-10))
                        newHi = util.nearest(idx, part.getPreXoversLow(strandType, p2, minIdx=idx+10))
                        if strand1.canResizeTo(newLo, newHi) and \
                           strand2.canResizeTo(newLo, newHi):
                            # do the resize
                            strand1.resize((newLo, newHi))
                            strand2.resize((newLo, newHi))
                            # install xovers
                            part.createXover(strand1, newHi, strand2, newHi)
                            part.createXover(strand2, newLo, strand1, newLo)
                    except ValueError:
                        pass  # nearest not found in the expanded list

                    # go back an install the internal xovers
                    if i > 2:
                        row0, col0, sSidx0 = strands[i-2]  # two strands back
                        vh0 = part.virtualHelixAtCoord((row0, col0))
                        strand0 = vh0.scaffoldStrandSet()._strandList[sSidx0]
                        if vh0 in neighbors:
                            p0 = neighbors.index(vh0)
                            l0, h0 = strand0.idxs()
                            l1, h1 = strand1.idxs()
                            oLow, oHigh = util.overlap(l0, h0, l1, h1)
                            try:
                                lList = [x for x in part.getPreXoversLow(strandType, p0) if x>oLow and x<oHigh]
                                lX = lList[len(lList)//2]
                                hList = [x for x in part.getPreXoversHigh(strandType, p0) if x>oLow and x<oHigh]
                                hX = hList[len(hList)//2]
                                # install high xover first
                                part.createXover(strand0, hX, strand1, hX)
                                # install low xover after getting new strands
                                # following the breaks caused by the high xover
                                strand3 = vh0.scaffoldStrandSet()._strandList[sSidx0]
                                strand4 = vh1.scaffoldStrandSet()._strandList[sSidx1]
                                part.createXover(strand4, lX, strand3, lX)
                            except IndexError:
                                pass  # filter was unhappy

    def autoScafRaster(self, strands):
        """docstring for autoScafRaster"""
        part = self.part()
        idx = part.activeBaseIndex()
        for i in range(1, len(strands)):
            row1, col1, sSidx1 = strands[i-1]  # previous strand
            row2, col2, sSidx2 = strands[i]  # current strand
            vh1 = part.virtualHelixAtCoord((row1, col1))
            vh2 = part.virtualHelixAtCoord((row2, col2))
            strand1 = vh1.scaffoldStrandSet()._strandList[sSidx1]
            strand2 = vh2.scaffoldStrandSet()._strandList[sSidx2]
            # determine if the pair of strands are neighbors
            neighbors = part.getVirtualHelixNeighbors(vh1)
            if vh2 in neighbors:
                p2 = neighbors.index(vh2)
                if vh2.number() % 2 == 1:
                    # resize and install external xovers
                    try:
                        # resize to the nearest prexover on either side of idx
                        newLo1 = newLo2 = util.nearest(idx, part.getPreXoversHigh(StrandType.Scaffold, p2, maxIdx=idx-8))
                        newHi = util.nearest(idx, part.getPreXoversLow(StrandType.Scaffold, p2, minIdx=idx+8))

                        if vh1.number() != 0:  # after the first helix
                            newLo1 = strand1.lowIdx()  # leave alone the lowIdx

                        if vh2.number() != len(strands)-1:  # before the last
                            newLo2 = strand2.lowIdx()  # leave alone the lowIdx

                        if strand1.canResizeTo(newLo1, newHi) and \
                           strand2.canResizeTo(newLo2, newHi):
                            strand1.resize((newLo1, newHi))
                            strand2.resize((newLo2, newHi))
                        else:
                            raise ValueError
                        # install xovers
                        part.createXover(strand1, newHi, strand2, newHi)
                    except ValueError:
                        pass  # nearest not found in the expanded list
                else:
                    # resize and install external xovers
                    idx = part.activeBaseIndex()
                    try:
                        # resize to the nearest prexover on either side of idx
                        newLo = util.nearest(idx, part.getPreXoversHigh(StrandType.Scaffold, p2, maxIdx=idx-8))

                        if strand1.canResizeTo(newLo, strand1.highIdx()) and \
                           strand2.canResizeTo(newLo, strand2.highIdx()):
                            strand1.resize((newLo, strand1.highIdx()))
                            strand2.resize((newLo, strand2.highIdx()))
                            # install xovers
                            part.createXover(strand1, newLo, strand2, newLo)
                        else:
                            raise ValueError
                    except ValueError:
                        pass  # nearest not found in the expanded list

    def mouseReleaseEvent(self, event):
        """docstring for mouseReleaseEvent"""
        part = self.part()
        uS = part.undoStack()
        strands = []
        # Look at the undo stack in reverse order
        for i in range(uS.index()-1, 0, -1):
            # Check for contiguous strand additions
            m = _strand_re.match(uS.text(i))
            if m:
                strands.insert(0, list(map(int, m.groups())))
            else:
                break

        if len(strands) > 1:
            autoScafType = app().prefs.getAutoScafType()
            util.beginSuperMacro(part, "Auto-connect")
            if autoScafType == "Mid-seam":
                self.autoScafMidSeam(strands)
            elif autoScafType == "Raster":
                self.autoScafRaster(strands)
            util.endSuperMacro(part)

    def decideAction(self, modifiers):
        """ On mouse press, an action (add scaffold at the active slice, add
        segment at the active slice, or create virtualhelix if missing) is
        decided upon and will be applied to all other slices happened across by
        mouseMoveEvent. The action is returned from this method in the form of a
        callable function."""
        vh = self.virtualHelix()
        part = self.part()

        if vh == None:
            return EmptyHelixItem.addVHIfMissing

        idx = part.activeBaseIndex()
        scafSSet, stapSSet = vh.getStrandSets()
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            if not stapSSet.hasStrandAt(idx-1, idx+1):
                return EmptyHelixItem.addStapAtActiveSliceIfMissing
            else:
                return EmptyHelixItem.nop

        if not scafSSet.hasStrandAt(idx-1, idx+1):
            return EmptyHelixItem.addScafAtActiveSliceIfMissing
        return EmptyHelixItem.nop
    # end def

    def nop(self):
        self._partItem.updateStatusBar("(%d, %d)" % self._coord)

    def addScafAtActiveSliceIfMissing(self):
        vh = self.virtualHelix()
        part = self.part()
        if vh == None:
            return

        idx = part.activeBaseIndex()
        startIdx = max(0,idx-1)
        endIdx = min(idx+1, part.maxBaseIdx())
        vh.scaffoldStrandSet().createStrand(startIdx, endIdx)

        self._partItem.updateStatusBar("(%d, %d)" % self._coord)
    # end def

    def addStapAtActiveSliceIfMissing(self):
        vh = self.virtualHelix()
        part = self.part()

        if vh == None:
            return

        idx = part.activeBaseIndex()
        startIdx = max(0,idx-1)
        endIdx = min(idx+1, part.maxBaseIdx())
        vh.stapleStrandSet().createStrand(startIdx, endIdx)

        self._partItem.updateStatusBar("(%d, %d)" % self._coord)
    # end def

    def addVHIfMissing(self):
        vh = self.virtualHelix()
        coord = self._coord
        part = self.part()

        if vh != None:
            return
        uS = part.undoStack()
        uS.beginMacro("Slice Click")
        part.createVirtualHelix(*coord)
        # vh.scaffoldStrandSet().createStrand(startIdx, endIdx)
        uS.endMacro()

        self._partItem.updateStatusBar("(%d, %d)" % self._coord)
    # end def

    # if GL:
    #     def paint(self, painter, option, widget):
    #         painter.beginNativePainting()
    # 
    #         radius = self._radius
    # 
    #         # GL.glPushAttrib(GL.GL_ALL_ATTRIB_BITS)
    #         # GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    # 
    #         # Draw the filled circle
    # 
    #         GL.glColor3f (1, 0.5, 0)       # Set to orange
    # 
    #         GL.glBegin (GL.GL_POLYGON)
    #         for X, Y in self._temp:
    #             GL.glVertex2f (X,Y)
    #         # end for
    #         GL.glEnd()
    # 
    #         # Draw the anti-aliased outline
    # 
    #         # GL.glEnable(GL.GL_BLEND)
    #         # GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    #         # GL.glEnable(GL.GL_LINE_SMOOTH)
    # 
    #         # GL.glBegin(GL.GL_LINE_LOOP)
    #         # for angle in [x*PI*0.01 for x in range(200)]:
    #         #     GL.glVertex2f(X + math.sin(angle) * radius, Y + math.cos(angle) * radius)
    #         # # end for
    #         # GL.glDisable(GL.GL_BLEND)
    #         # GL.glEnd()
    #         # GL.glPopAttrib()
    #         painter.endNativePainting()
    #     # end def
    # # end if
