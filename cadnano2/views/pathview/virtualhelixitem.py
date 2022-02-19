#!/usr/bin/env python
# encoding: utf-8

from math import floor
from cadnano2.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano2.model.enum import StrandType
from .strand.stranditem import StrandItem
from cadnano2.views import styles
from .virtualhelixhandleitem import VirtualHelixHandleItem
import cadnano2.util as util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject', 'Qt', 'QRectF'])
util.qtWrapImport('QtGui', globals(), ['QBrush',
                                       'QPainterPath',
                                       'QPen',
                                       'QBrush',
                                       'QColor'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsItem',
                                           'QGraphicsPathItem',
                                           'QGraphicsRectItem'])


_baseWidth = styles.PATH_BASE_WIDTH
# _gridPen = QPen(styles.minorgridstroke, styles.MINOR_GRID_STROKE_WIDTH)
# _gridPen.setCosmetic(True)


class VirtualHelixItem(QGraphicsPathItem):
    """VirtualHelixItem for PathView"""
    findChild = util.findChild  # for debug

    def __init__(self, partItem, modelVirtualHelix, viewroot, activeTool):
        super(VirtualHelixItem, self).__init__(partItem.proxy())
        self._partItem = partItem
        self._modelVirtualHelix = modelVirtualHelix
        self._viewroot = viewroot
        self._activeTool = activeTool
        self._controller = VirtualHelixItemController(self, modelVirtualHelix)

        self._handle = VirtualHelixHandleItem(modelVirtualHelix, partItem, viewroot)
        self._lastStrandSet = None
        self._lastIdx = None
        self._scaffoldBackground = None
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        view = viewroot.scene().views()[0]
        view.levelOfDetailChangedSignal.connect(self.levelOfDetailChangedSlot)
        shouldShowDetails = view.shouldShowDetails()

        pen = QPen(styles.minorgridstroke, styles.MINOR_GRID_STROKE_WIDTH)
        pen.setCosmetic(shouldShowDetails)
        self.setPen(pen)

        self.refreshPath()
        self.setAcceptHoverEvents(True)  # for pathtools
        self.setZValue(styles.ZPATHHELIX)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def levelOfDetailChangedSlot(self, boolval):
        """Not connected to the model, only the QGraphicsView"""
        pen = self.pen()
        pen.setCosmetic(boolval)
        self.setPen(pen)
    # end def

    def strandAddedSlot(self, sender, strand):
        """
        Instantiates a StrandItem upon notification that the model has a
        new Strand.  The StrandItem is responsible for creating its own
        controller for communication with the model, and for adding itself to
        its parent (which is *this* VirtualHelixItem, i.e. 'self').
        """
        StrandItem(strand, self, self._viewroot)
    # end def

    def decoratorAddedSlot(self, decorator):
        """
        Instantiates a DecoratorItem upon notification that the model has a
        new Decorator.  The Decorator is responsible for creating its own
        controller for communication with the model, and for adding itself to
        its parent (which is *this* VirtualHelixItem, i.e. 'self').
        """
        pass

    def virtualHelixNumberChangedSlot(self, virtualHelix, number):
        self._handle.setNumber()
    # end def

    def virtualHelixRemovedSlot(self, virtualHelix):
        self._controller.disconnectSignals()
        self._controller = None
        scene = self.scene()
        self._handle.remove()
        scene.removeItem(self)
        self._partItem.removeVirtualHelixItem(self)
        self._partItem = None
        self._modelVirtualHelix = None
        self._activeTool = None
        self._handle = None
    # end def

    ### ACCESSORS ###
    def activeTool(self):
        return self._activeTool

    def coord(self):
        return self._modelVirtualHelix.coord()
    # end def

    def viewroot(self):
        return self._viewroot
    # end def

    def handle(self):
        return self._handle
    # end def

    def part(self):
        return self._partItem.part()
    # end def

    def partItem(self):
        return self._partItem
    # end def

    def number(self):
        if self._modelVirtualHelix is None:
            return ""
        return self._modelVirtualHelix.number()
    # end def

    def virtualHelix(self):
        return self._modelVirtualHelix
    # end def

    def window(self):
        return self._partItem.window()
    # end def

    ### DRAWING METHODS ###
    def isStrandOnTop(self, strand):
        sS = strand.strandSet()
        isEvenParity = self._modelVirtualHelix.isEvenParity()
        return isEvenParity and sS.isScaffold() or\
               not isEvenParity and sS.isStaple()
    # end def

    def isStrandTypeOnTop(self, strandType):
        isEvenParity = self._modelVirtualHelix.isEvenParity()
        return isEvenParity and strandType == StrandType.Scaffold or \
               not isEvenParity and strandType == StrandType.Staple
    # end def

    def upperLeftCornerOfBase(self, idx, strand):
        x = idx * _baseWidth
        y = 0 if self.isStrandOnTop(strand) else _baseWidth
        return x, y
    # end def

    def upperLeftCornerOfBaseType(self, idx, strandType):
        x = idx * _baseWidth
        y = 0 if self.isStrandTypeOnTop(strandType) else _baseWidth
        return x, y
    # end def

    def refreshPath(self):
        """
        Returns a QPainterPath object for the minor grid lines.
        The path also includes a border outline and a midline for
        dividing scaffold and staple bases.
        """
        bw = _baseWidth
        bw2 = 2 * bw
        part = self.part()
        path = QPainterPath()
        subStepSize = part.subStepSize()
        canvasSize = part.maxBaseIdx()+1
        # border
        path.addRect(0, 0, bw * canvasSize, 2 * bw)
        # minor tick marks
        for i in range(canvasSize):
            x = round(bw * i) + .5
            if i % subStepSize == 0:
                path.moveTo(x-.5, 0)
                path.lineTo(x-.5, bw2)
                path.lineTo(x-.25, bw2)
                path.lineTo(x-.25, 0)
                path.lineTo(x, 0)
                path.lineTo(x, bw2)
                path.lineTo(x+.25, bw2)
                path.lineTo(x+.25, 0)
                path.lineTo(x+.5, 0)
                path.lineTo(x+.5, bw2)

                # path.moveTo(x-.5, 0)
                # path.lineTo(x-.5, 2 * bw)
                # path.lineTo(x+.5, 2 * bw)
                # path.lineTo(x+.5, 0)

            else:
                path.moveTo(x, 0)
                path.lineTo(x, 2 * bw)

        # staple-scaffold divider
        path.moveTo(0, bw)
        path.lineTo(bw * canvasSize, bw)

        self.setPath(path)

        if self._modelVirtualHelix.scaffoldIsOnTop():
            scaffoldY = 0
        else:
            scaffoldY = bw
        # if self._scaffoldBackground == None:
        #     highlightr = QGraphicsRectItem(0, scaffoldY, bw * canvasSize, bw, self)
        #     highlightr.setBrush(QBrush(styles.scaffold_bkg_fill))
        #     highlightr.setPen(QPen(Qt.PenStyle.NoPen))
        #     highlightr.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)
        #     self._scaffoldBackground = highlightr
        # else:
        #     self._scaffoldBackground.setRect(0, scaffoldY, bw * canvasSize, bw)

    # end def

    def resize(self):
        """Called by part on resize."""
        self.refreshPath()

    ### PUBLIC SUPPORT METHODS ###
    def setActive(self, idx):
        """Makes active the virtual helix associated with this item."""
        self.part().setActiveVirtualHelix(self._modelVirtualHelix, idx)
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        self.scene().views()[0].addToPressList(self)
        strandSet, idx = self.baseAtPoint(event.pos())
        self.setActive(idx)
        toolMethodName = str(self._activeTool()) + "MousePress"

        ### uncomment for debugging modifier selection
        # strandSet, idx = self.baseAtPoint(event.position())
        # row, col = strandSet.virtualHelix().coord()
        # self._partItem.part().selectPreDecorator([(row,col,idx)])

        if hasattr(self, toolMethodName):
            self._lastStrandSet, self._lastIdx = strandSet, idx
            getattr(self, toolMethodName)(strandSet, idx)
        else:
            event.setAccepted(False)
    # end def

    def mouseMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        toolMethodName = str(self._activeTool()) + "MouseMove"
        if hasattr(self, toolMethodName):
            strandSet, idx = self.baseAtPoint(event.pos())
            if self._lastStrandSet != strandSet or self._lastIdx != idx:
                self._lastStrandSet, self._lastIdx = strandSet, idx
                getattr(self, toolMethodName)(strandSet, idx)
        else:
            event.setAccepted(False)
    # end def

    def customMouseRelease(self, event):
        """
        Parses a mouseReleaseEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        toolMethodName = str(self._activeTool()) + "MouseRelease"
        if hasattr(self, toolMethodName):
            getattr(self, toolMethodName)(self._lastStrandSet, self._lastIdx)
        else:
            event.setAccepted(False)
    # end def

    ### COORDINATE UTILITIES ###
    def baseAtPoint(self, pos):
        """
        Returns the (strandType, index) under the location x,y or None.

        It shouldn't be possible to click outside a pathhelix and still call
        this function. However, this sometimes happens if you click exactly
        on the top or bottom edge, resulting in a negative y value.
        """
        x, y = pos.x(), pos.y()
        mVH = self._modelVirtualHelix
        baseIdx = int(floor(x / _baseWidth))
        minBase, maxBase = 0, mVH.part().maxBaseIdx()
        if baseIdx < minBase or baseIdx >= maxBase:
            baseIdx = util.clamp(baseIdx, minBase, maxBase)
        if y < 0:
            y = 0  # HACK: zero out y due to erroneous click
        strandIdx = floor(y * 1. / _baseWidth)
        if strandIdx < 0 or strandIdx > 1:
            strandIdx = int(util.clamp(strandIdx, 0, 1))
        strandSet = mVH.getStrandSetByIdx(strandIdx)
        return (strandSet, baseIdx)
    # end def

    def keyPanDeltaX(self):
        """How far a single press of the left or right arrow key should move
        the scene (in scene space)"""
        dx = self._partItem.part().stepSize() * _baseWidth
        return self.mapToScene(QRectF(0, 0, dx, 1)).boundingRect().width()
    # end def

    def hoverLeaveEvent(self, event):
        self._partItem.updateStatusBar("")
    # end def

    def hoverMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        baseIdx = int(floor(event.pos().x() / _baseWidth))
        loc = "%d[%d]" % (self.number(), baseIdx)
        self._partItem.updateStatusBar(loc)

        activeTool = self._activeTool()
        toolMethodName = str(activeTool) + "HoverMove"
        if hasattr(self, toolMethodName):
            strandType, idxX, idxY = activeTool.baseAtPoint(self, event.pos())
            getattr(self, toolMethodName)(strandType, idxX, idxY)
    # end def

    ### TOOL METHODS ###
    def pencilToolMousePress(self, strandSet, idx):
        """strand.getDragBounds"""
        # print "%s: %s[%s]" % (util.methodName(), strandSet, idx)
        activeTool = self._activeTool()
        if not activeTool.isDrawingStrand():
            activeTool.initStrandItemFromVHI(self, strandSet, idx)
            activeTool.setIsDrawingStrand(True)
    # end def

    def pencilToolMouseMove(self, strandSet, idx):
        """strand.getDragBounds"""
        # print "%s: %s[%s]" % (util.methodName(), strandSet, idx)
        activeTool = self._activeTool()
        if activeTool.isDrawingStrand():
            activeTool.updateStrandItemFromVHI(self, strandSet, idx)
    # end def

    def pencilToolMouseRelease(self, strandSet, idx):
        """strand.getDragBounds"""
        # print "%s: %s[%s]" % (util.methodName(), strandSet, idx)
        activeTool = self._activeTool()
        if activeTool.isDrawingStrand():
            activeTool.setIsDrawingStrand(False)
            activeTool.attemptToCreateStrand(self, strandSet, idx)
    # end def

    def pencilToolHoverMove(self, strandType, idxX, idxY):
        """Pencil the strand is possible."""
        partItem = self.partItem()
        activeTool = self._activeTool()
        if not activeTool.isFloatingXoverBegin():
            tempXover = activeTool.floatingXover()
            tempXover.updateFloatingFromVHI(self, strandType, idxX, idxY)
    # end def
