from .abstractpathtool import AbstractPathTool
from cadnano2.views import styles
import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), ['QPointF', 'QRectF', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QBrush', 'QFont', 'QPainterPath',
                                       'QPen', 'QPolygonF'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsItem'])

_bw = styles.PATH_BASE_WIDTH
_pen = QPen(styles.redstroke, 1)
_rect = QRectF(0, 0, _bw, _bw)
_pathArrowLeft = QPainterPath()
_l3poly = QPolygonF()
_l3poly.append(QPointF(_bw, 0))
_l3poly.append(QPointF(0.25 * _bw, 0.5 * _bw))
_l3poly.append(QPointF(_bw, _bw))
_pathArrowLeft.addPolygon(_l3poly)
_pathArrowRight = QPainterPath()
_r3poly = QPolygonF()  # right-hand 3' arr
_r3poly.append(QPointF(0, 0))
_r3poly.append(QPointF(0.75 * _bw, 0.5 * _bw))
_r3poly.append(QPointF(0, _bw))
_pathArrowRight.addPolygon(_r3poly)


class BreakTool(AbstractPathTool):
    """
    docstring for BreakTool
    """
    def __init__(self, controller):
        super(BreakTool, self).__init__(controller)
        self._isTopStrand = True

    def __repr__(self):
        return "breakTool"  # first letter should be lowercase

    def paint(self, painter, option, widget=None):
        super(BreakTool, self).paint(painter, option, widget)
        painter.setPen(_pen)
        if self._isTopStrand:
            painter.drawPath(self._pathArrowRight)
        else:
            painter.drawPath(self._pathArrowLeft)

    def setTopStrand(self, isTop):
        """
        Called in hoverMovePathHelix to set whether breaktool is hovering
        over a top strand (goes 5' to 3' left to right) or bottom strand.
        """
        self._isTopStrand = isTop

    def hoverMove(self, item, event, flag=None):
        """
        flag is for the case where an item in the path also needs to
        implement the hover method
        """
        self.updateLocation(item, item.mapToScene(QPointF(event.position())))
        posScene = item.mapToScene(QPointF(event.position()))
        posItem = item.mapFromScene(posScene)
        self.setTopStrand(self.helixIndex(posItem)[1] == 0)
        newPosition = self.helixPos(posItem)
        if newPosition != None:
            self.setPos(newPosition)
