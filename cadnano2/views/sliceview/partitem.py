from cadnano2.controllers.itemcontrollers.partitemcontroller import PartItemController
from .emptyhelixitem import EmptyHelixItem
from .virtualhelixitem import VirtualHelixItem
from .activesliceitem import ActiveSliceItem
from cadnano2.views import styles
import cadnano2.util as util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QRectF', 'QPointF', 'QEvent', 'Qt',
                                        'pyqtSignal', 'pyqtSlot', 'QObject'])
util.qtWrapImport('QtGui', globals(), ['QBrush',
                                       'QPainterPath',
                                       'QPen'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsItem',
                                           'QGraphicsEllipseItem'])

_radius = styles.SLICE_HELIX_RADIUS
_defaultRect = QRectF(0, 0, 2 * _radius, 2 * _radius)
highlightWidth = styles.SLICE_HELIX_MOD_HILIGHT_WIDTH
delta = (highlightWidth - styles.SLICE_HELIX_STROKE_WIDTH)/2.
_hoverRect = _defaultRect.adjusted(-delta, -delta, delta, delta)
_modPen = QPen(styles.bluestroke, highlightWidth)


class PartItem(QGraphicsItem):
    _radius = styles.SLICE_HELIX_RADIUS

    def __init__(self, modelPart, parent=None):
        """
        Parent should be either a SliceRootItem, or an AssemblyItem.

        Invariant: keys in _emptyhelixhash = range(_nrows) x range(_ncols)
        where x is the cartesian product.

        Order matters for deselector, probe, and setlattice
        """
        super(PartItem, self).__init__(parent)
        self._part = modelPart
        self._controller = PartItemController(self, modelPart)
        self._activeSliceItem = ActiveSliceItem(self, modelPart.activeBaseIndex())
        self._scaleFactor = self._radius/modelPart.radius()
        self._emptyhelixhash = {}
        self._virtualHelixHash = {}
        self._nrows, self._ncols = 0, 0
        self._rect = QRectF(0, 0, 0, 0)
        self._initDeselector()
        # Cache of VHs that were active as of last call to activeSliceChanged
        # If None, all slices will be redrawn and the cache will be filled.
        # Connect destructor. This is for removing a part from scenes.
        self.probe = self.IntersectionProbe(self)
        # initialize the PartItem with an empty set of old coords
        self._setLattice([], modelPart.generatorFullLattice())
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemHasNoContents)  # never call paint
        self.setZValue(styles.ZPARTITEM)
        self._initModifierCircle()
    # end def

    def _initDeselector(self):
        """
        The deselector grabs mouse events that missed a slice and clears the
        selection when it gets one.
        """
        self.deselector = ds = PartItem.Deselector(self)
        ds.setParentItem(self)
        ds.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)
        ds.setZValue(styles.ZDESELECTOR)

    def _initModifierCircle(self):
        self._canShowModCirc = False
        self._modCirc = mC = QGraphicsEllipseItem(_hoverRect, self)
        mC.setPen(_modPen)
        mC.hide()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def partActiveVirtualHelixChangedSlot(self, part, virtualHelix):
        pass

    def partDimensionsChangedSlot(self, sender):
        pass
    # end def

    def partHideSlot(self, sender):
        self.hide()
    # end def

    def partParentChangedSlot(self, sender):
        """docstring for partParentChangedSlot"""
        # print "PartItem.partParentChangedSlot"
        pass

    def partRemovedSlot(self, sender):
        """docstring for partRemovedSlot"""
        self._activeSliceItem.removed()
        self.parentItem().removePartItem(self)

        scene = self.scene()

        self._virtualHelixHash = None

        for item in list(self._emptyhelixhash.items()):
            key, val = item
            scene.removeItem(val)
            del self._emptyhelixhash[key]
        self._emptyhelixhash = None

        scene.removeItem(self)

        self._part = None
        self.probe = None
        self._modCirc = None

        self.deselector = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partVirtualHelicesReorderedSlot(self, sender, orderedCoordList):
        pass
    # end def

    def partPreDecoratorSelectedSlot(self, sender, row, col, baseIdx):
        """docstring for partPreDecoratorSelectedSlot"""
        vhi = self.getVirtualHelixItemByCoord(row, col)
        view = self.window().sliceGraphicsView
        view.sceneRootItem.resetTransform()
        view.centerOn(vhi)
        view.zoomIn()
        mC = self._modCirc
        x,y = self._part.latticeCoordToPositionXY(row, col, self.scaleFactor())
        mC.setPos(x,y)
        if self._canShowModCirc:
            mC.show()
    # end def

    def partVirtualHelixAddedSlot(self, sender, virtualHelix):
        vh = virtualHelix
        coords = vh.coord()

        emptyHelixItem = self._emptyhelixhash[coords]
        # TODO test to see if self._virtualHelixHash is necessary
        vhi = VirtualHelixItem(vh, emptyHelixItem)
        self._virtualHelixHash[coords] = vhi
    # end def

    def partVirtualHelixRenumberedSlot(self, sender, coord):
        pass
    # end def

    def partVirtualHelixResizedSlot(self, sender, coord):
        pass
    # end def

    def updatePreXoverItemsSlot(self, sender, virtualHelix):
        pass
    # end def

    ### ACCESSORS ###
    def boundingRect(self):
        return self._rect
    # end def

    def part(self):
        return self._part
    # end def

    def scaleFactor(self):
        return self._scaleFactor
    # end def

    def setPart(self, newPart):
        self._part = newPart
    # end def

    def window(self):
        return self.parentItem().window()
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _upperLeftCornerForCoords(self, row, col):
        pass  # subclass
    # end def

    def _updateGeometry(self):
        self._rect = QRectF(0, 0, *self.part().dimensions())
    # end def

    def _spawnEmptyHelixItemAt(self, row, column):
        helix = EmptyHelixItem(row, column, self)
        # helix.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent, True)
        self._emptyhelixhash[(row, column)] = helix
    # end def

    def _killHelixItemAt(row, column):
        s = self._emptyhelixhash[(row, column)]
        s.scene().removeItem(s)
        del self._emptyhelixhash[(row, column)]
    # end def

    def _setLattice(self, oldCoords, newCoords):
        """A private method used to change the number of rows,
        cols in response to a change in the dimensions of the
        part represented by the receiver"""
        oldSet = set(oldCoords)
        oldList = list(oldSet)
        newSet = set(newCoords)
        newList = list(newSet)
        for coord in oldList:
            if coord not in newSet:
                self._killHelixItemAt(*coord)
        # end for
        for coord in newList:
            if coord not in oldSet:
                self._spawnEmptyHelixItemAt(*coord)
        # end for
        # self._updateGeometry(newCols, newRows)
        # self.prepareGeometryChange()
        # the Deselector copies our rect so it changes too
        self.deselector.prepareGeometryChange()
        self.zoomToFit()
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def getVirtualHelixItemByCoord(self, row, column):
        if (row, column) in self._emptyhelixhash:
            return self._virtualHelixHash[(row, column)]
        else:
            return None
    # end def

    def paint(self, painter, option, widget=None):
        pass
    # end def

    def selectionWillChange(self, newSel):
        if self.part() == None:
            return
        if self.part().selectAllBehavior():
            return
        for sh in self._emptyhelixhash.values():
            sh.setSelected(sh.virtualHelix() in newSel)
    # end def

    def setModifyState(self, bool):
        """Hides the modRect when modify state disabled."""
        self._canShowModCirc = bool
        if bool == False:
            self._modCirc.hide()

    def updateStatusBar(self, statusString):
        """Shows statusString in the MainWindow's status bar."""
        pass  # disabled for now.
        # self.window().statusBar().showMessage(statusString, timeout)

    def vhAtCoordsChanged(self, row, col):
        self._emptyhelixhash[(row, col)].update()
    # end def

    def zoomToFit(self):
        thescene = self.scene()
        theview = thescene.views()[0]
        theview.zoomToFit()
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        # self.createOrAddBasesToVirtualHelix()
        QGraphicsItem.mousePressEvent(self, event)
    # end def

    class Deselector(QGraphicsItem):
        """The deselector lives behind all the slices and observes mouse press
        events that miss slices, emptying the selection when they do"""
        def __init__(self, parentHGI):
            super(PartItem.Deselector, self).__init__()
            self.parentHGI = parentHGI

        def mousePressEvent(self, event):
            self.parentHGI.part().setSelection(())
            super(PartItem.Deselector, self).mousePressEvent(event)

        def boundingRect(self):
            return self.parentHGI.boundingRect()

        def paint(self, painter, option, widget=None):
            pass

    class IntersectionProbe(QGraphicsItem):
        def boundingRect(self):
            return QRectF(0, 0, .1, .1)
        def paint(self, painter, option, widget=None):
            pass
