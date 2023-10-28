from cadnano2.views import styles
import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), ['QRectF', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QBrush', 'QFont'])
util.qtWrapImport('QtWidgets', globals(),  ['QApplication',
                                            'QColorDialog',
                                            'QGraphicsItem',
                                            'QGraphicsSimpleTextItem'])

_font = QFont(styles.thefont, 12, QFont.Weight.Bold)


class ColorPanel(QGraphicsItem):
    _scafColors = styles.scafColors
    _stapColors = styles.stapColors
    _pen = Qt.PenStyle.NoPen

    def __init__(self, parent=None):
        super(ColorPanel, self).__init__(parent)
        self.rect = QRectF(0, 0, 30, 30)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.colordialog = QColorDialog()
        # self.colordialog.setOption(QColorDialog.DontUseNativeDialog)
        self._scafColorIndex = 0  # init on -1, painttool will cycle to 0
        self._stapColorIndex = -1  # init on -1, painttool will cycle to 0
        self._scafColor = self._scafColors[self._scafColorIndex]
        self._stapColor = self._stapColors[self._stapColorIndex]
        self._scafBrush = QBrush(self._scafColor)
        self._stapBrush = QBrush(self._stapColor)
        self._initLabel()
        self.hide()

    def _initLabel(self):
        self._label = label = QGraphicsSimpleTextItem("scaf\nstap", parent=self)
        label.setPos(32, 0)
        label.setFont(_font)
        # label.setBrush(_labelbrush)
        # label.hide()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        painter.setPen(self._pen)
        painter.setBrush(self._scafBrush)
        painter.drawRect(0, 0, 30, 15)
        painter.setBrush(self._stapBrush)
        painter.drawRect(0, 15, 30, 15)

    def nextColor(self):
        if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier:
            self._scafColorIndex += 1
            if self._scafColorIndex == len(self._scafColors):
                self._scafColorIndex = 0
            self._scafColor = self._scafColors[self._scafColorIndex]
            self._scafBrush.setColor(self._scafColor)
        else:
            self._stapColorIndex += 1
            if self._stapColorIndex == len(self._stapColors):
                self._stapColorIndex = 0
            self._stapColor = self._stapColors[self._stapColorIndex]
            self._stapBrush.setColor(self._stapColor)
        self.update()

    def prevColor(self):
        self._scafColorIndex -= 1
        self._stapColorIndex -= 1

    def color(self):
        return self._stapColor

    def scafColorName(self):
        return self._scafColor.name()

    def stapColorName(self):
        return self._stapColor.name()

    def changeScafColor(self):
        self.update()

    def changeStapColor(self):
        self._stapColor = self.colordialog.currentColor()
        self._stapBrush = QBrush(self._stapColor)
        self.update()

    def mousePressEvent(self, event):
        if event.pos().y() < 10:
            newColor = self.colordialog.getColor(self._scafColor)
            if newColor.isValid() and newColor.name() != self._scafColor.name():
                self._scafColor = newColor
                self._scafBrush = QBrush(newColor)
                if not newColor in self._scafColors:
                    self._scafColors.insert(self._scafColorIndex, newColor)
                self.update()
        else:
            newColor = self.colordialog.getColor(self._stapColor)
            if newColor.isValid() and newColor.name() != self._stapColor.name():
                self._stapColor = newColor
                self._stapBrush = QBrush(newColor)
                if not newColor in self._stapColors:
                    self._stapColors.insert(self._stapColorIndex, newColor)
                self.update()

