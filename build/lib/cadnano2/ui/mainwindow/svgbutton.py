import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), ['QObject', 'pyqtSignal', 'Qt'])
util.qtWrapImport('QtWidgets', globals(), ['QGraphicsObject'])
util.qtWrapImport('QtSvg', globals(), ['QSvgRenderer'])


class SVGButton(QGraphicsObject):
    def __init__(self, fname, parent=None):
        super(SVGButton, self).__init__(parent)
        self.svg = QSvgRenderer(fname)

    def paint(self, painter, options, widget):
        self.svg.render(painter, self.boundingRect())

    def boundingRect(self):
        return self.svg.viewBoxF()

    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        self.clicked.emit()