from cadnano2.views import styles
from cadnano2.model.virtualhelix import VirtualHelix
from cadnano2.model.enum import Parity, StrandType
from cadnano2.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController

import cadnano2.util as util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['Qt', 'QEvent', 'QRectF', 'QPointF'])
util.qtWrapImport('QtGui', globals(), ['QBrush',
                                       'QPen',
                                       'QPainterPath',
                                       'QPolygonF',
                                       'QColor'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsEllipseItem',
                                           'QGraphicsItem',
                                           'QGraphicsLineItem',
                                           'QGraphicsSimpleTextItem',
                                           ])


class VirtualHelixItem(QGraphicsEllipseItem):
    """
    The VirtualHelixItem is an individual circle that gets drawn in the SliceView
    as a child of the PartItem. Taken as a group, many SliceHelix
    instances make up the crossection of the DNAPart. Clicking on a SliceHelix
    adds a VirtualHelix to the DNAPart. The SliceHelix then changes appearence
    and paints its corresponding VirtualHelix number.
    """
    # set up default, hover, and active drawing styles
    _useBrush = QBrush(styles.orangefill)
    _usePen = QPen(styles.orangestroke, styles.SLICE_HELIX_STROKE_WIDTH)
    _radius = styles.SLICE_HELIX_RADIUS
    _outOfSlicePen = QPen(styles.lightorangestroke,
                          styles.SLICE_HELIX_STROKE_WIDTH)
    _outOfSliceBrush = QBrush(styles.lightorangefill)
    _rect = QRectF(0, 0, 2 * _radius, 2 * _radius)
    _font = styles.SLICE_NUM_FONT
    _ZVALUE = styles.ZSLICEHELIX+3

    def __init__(self, modelVirtualHelix, emptyHelixItem):
        """
        emptyHelixItem is a EmptyHelixItem that will act as a QGraphicsItem parent
        """
        super(VirtualHelixItem, self).__init__(parent=emptyHelixItem)
        self._virtualHelix = modelVirtualHelix
        self._emptyHelixItem = emptyHelixItem
        self.hide()
        # drawing related

        self.isHovered = False
        self.setAcceptHoverEvents(True)
        # self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setZValue(self._ZVALUE)
        self.lastMousePressAddedBases = False

        self.setBrush(self._outOfSliceBrush)
        self.setPen(self._outOfSlicePen)
        self.setRect(self._rect)

        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()
        self.createArrow()

        self._controller = VirtualHelixItemController(self, modelVirtualHelix)

        self.show()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def virtualHelixNumberChangedSlot(self, virtualHelix):
        """
        receives a signal containing a virtualHelix and the oldNumber 
        as a safety check
        """
        self.setNumber()
    # end def

    def virtualHelixRemovedSlot(self, virtualHelix):
        self._controller.disconnectSignals()
        self._controller = None
        self._emptyHelixItem.setNotHovered()
        self._virtualHelix = None
        self._emptyHelixItem = None
        self.scene().removeItem(self._label)
        self._label = None
        self.scene().removeItem(self)
    # end def

    def strandAddedSlot(self, sender, strand):
        pass
    # end def

    ###

    def createLabel(self):
        label = QGraphicsSimpleTextItem("%d" % self._virtualHelix.number())
        label.setFont(self._font)
        label.setZValue(self._ZVALUE)
        label.setParentItem(self)
        return label
    # end def

    def createArrow(self):
        rad = self._radius
        pen = QPen()
        pen.setWidth(3)
        color = QColor(Qt.GlobalColor.blue)
        color.setAlphaF(0.25)
        pen.setBrush(color)
        if self._virtualHelix.isEvenParity():
            arrow = QGraphicsLineItem(rad, rad, 2*rad, rad, self)
        else:
            arrow = QGraphicsLineItem(0, rad, rad, rad, self)
        arrow.setTransformOriginPoint(rad, rad)
        arrow.setZValue(400)
        arrow.setPen(pen)
        self.arrow = arrow
        self.arrow.hide()
    # end def

    def updateArrow(self, idx):
        part = self.part()
        tpb = part._twistPerBase
        angle = idx*tpb
        self.arrow.setRotation(angle + part._twistOffset)
    # end def

    def setNumber(self):
        """docstring for setNumber"""
        vh = self._virtualHelix
        num = vh.number()
        label = self._label
        radius = self._radius

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

    def part(self):
        return self._emptyHelixItem.part()

    def virtualHelix(self):
        return self._virtualHelix
    # end def

    def number(self):
        return self.virtualHelix().number()

    def setActiveSliceView(self, isActiveNow, idx):
        if isActiveNow:
            self.setPen(self._usePen)
            self.setBrush(self._useBrush)
            self.updateArrow(idx)
            self.arrow.show()
        else:
            self.setPen(self._outOfSlicePen)
            self.setBrush(self._outOfSliceBrush)
            self.arrow.hide()
    # end def

    ############################ User Interaction ############################
    def sceneEvent(self, event):
        """Included for unit testing in order to grab events that are sent
        via QGraphicsScene.sendEvent()."""
        # if self._parent.sliceController.testRecorder:
        #     coord = (self._row, self._col)
        #     self._parent.sliceController.testRecorder.sliceSceneEvent(event, coord)
        if event.type() == QEvent.Type.MouseButtonPress:
            self.mousePressEvent(event)
            return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.mouseReleaseEvent(event)
            return True
        elif event.type() == QEvent.Type.MouseMove:
            self.mouseMoveEvent(event)
            return True
        QGraphicsItem.sceneEvent(self, event)
        return False

    def hoverEnterEvent(self, event):
        """
        If the selection is configured to always select
        everything, we don't draw a focus ring around everything,
        instead we only draw a focus ring around the hovered obj.
        """
        # if self.selectAllBehavior():
        #     self.setSelected(True)
        # forward the event to the emptyHelixItem as well
        self._emptyHelixItem.hoverEnterEvent(event)
    # end def

    def hoverLeaveEvent(self, event):
        # if self.selectAllBehavior():
        #     self.setSelected(False)
        self._emptyHelixItem.hoverEnterEvent(event)
    # end def

    # def mousePressEvent(self, event):
    #     action = self.decideAction(event.modifiers())
    #     action(self)
    #     self.dragSessionAction = action
    # 
    # def mouseMoveEvent(self, event):
    #     parent = self._helixItem
    #     posInParent = parent.mapFromItem(self, QPointF(event.position()))
    #     # Qt doesn't have any way to ask for graphicsitem(s) at a
    #     # particular position but it *can* do intersections, so we
    #     # just use those instead
    #     parent.probe.setPos(posInParent)
    #     for ci in parent.probe.collidingItems():
    #         if isinstance(ci, SliceHelix):
    #             self.dragSessionAction(ci)
    # # end def

    # def mouseReleaseEvent(self, event):
    #     self.part().needsFittingToView.emit()

    # def decideAction(self, modifiers):
    #     """ On mouse press, an action (add scaffold at the active slice, add
    #     segment at the active slice, or create virtualhelix if missing) is
    #     decided upon and will be applied to all other slices happened across by
    #     mouseMoveEvent. The action is returned from this method in the form of a
    #     callable function."""
    #     vh = self.virtualHelix()
    #     if vh == None: return SliceHelix.addVHIfMissing
    #     idx = self.part().activeSlice()
    #     if modifiers & Qt.KeyboardModifier.ShiftModifier:
    #         if vh.stap().get(idx) == None:
    #             return SliceHelix.addStapAtActiveSliceIfMissing
    #         else:
    #             return SliceHelix.nop
    #     if vh.scaf().get(idx) == None:
    #         return SliceHelix.addScafAtActiveSliceIfMissing
    #     return SliceHelix.nop
    # 
    # def nop(self):
    #     pass
