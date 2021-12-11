"""
activeslicehandle.py
Created by Shawn on 2011-02-05.
"""

from cadnano2.controllers.itemcontrollers.activesliceitemcontroller import ActiveSliceItemController
import cadnano2.util as util

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QPointF', 'QRectF', 'Qt', 'QObject',\
                                        'pyqtSignal', 'pyqtSlot', 'QEvent'])
util.qtWrapImport('QtGui', globals(), ['QBrush',
                                       'QFont',
                                       'QPen',
                                       'QDrag',
                                       'QUndoCommand'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsItem',
                                           'QGraphicsRectItem',
                                           'QGraphicsSimpleTextItem'])


class ActiveSliceItem(QGraphicsRectItem):
    """ActiveSliceItem for the Slice View"""
    def __init__(self, partItem, activeBaseIndex):
        super(ActiveSliceItem, self).__init__(partItem)
        self._partItem = partItem
        self._controller = ActiveSliceItemController(self, partItem.part())
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemHasNoContents)
    # end def

    ### SLOTS ###
    def strandChangedSlot(self, sender, vh):
        if vh == None:
            return
        partItem = self._partItem
        vhi = partItem.getVirtualHelixItemByCoord(*vh.coord())
        activeBaseIdx = partItem.part().activeBaseIndex()
        isActiveNow = vh.hasStrandAtIdx(activeBaseIdx)
        vhi.setActiveSliceView(isActiveNow, activeBaseIdx)
    # end def

    def updateIndexSlot(self, sender, newActiveSliceZIndex):
        part = self.part()
        if part.numberOfVirtualHelices() == 0:
            return
        newlyActiveVHs = set()
        activeBaseIdx = part.activeBaseIndex()
        for vhi in self._partItem._virtualHelixHash.values():
            vh = vhi.virtualHelix()
            if vh:
                isActiveNow = vh.hasStrandAtIdx(activeBaseIdx)
                vhi.setActiveSliceView(isActiveNow, activeBaseIdx)
    # end def

    def updateRectSlot(self, part):
        pass
    # end def

    ### ACCESSORS ###
    def part(self):
        return self._partItem.part()
    # end def

    ### PUBLIC METHODS FOR DRAWING / LAYOUT ###
    def removed(self):
        self._partItem = None
        self._controller.disconnectSignals()
        self.controller = None
    # end def
