"""
config
Created by Jonathan deWerd on 2012-01-19.
"""
import util, cadnano
from . import autobreakconfig_ui
from . import autobreak
util.qtWrapImport('QtGui', globals(), ['QKeySequence'])
util.qtWrapImport('QtCore', globals(), ['Qt'])
util.qtWrapImport('QtWidgets', globals(), ['QDialog', 'QDialogButtonBox'])


class AutobreakConfig(QDialog, autobreakconfig_ui.Ui_Dialog):
    def __init__(self, parent, handler):
        QDialog.__init__(self, parent, Qt.Sheet)
        self.setupUi(self)
        self.handler = handler
        fb = self.buttonBox.button(QDialogButtonBox.Cancel)
        fb.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_R ))

    def keyPressEvent(self, e):
        return QDialog.keyPressEvent(self, e)

    def closeDialog(self):
        self.close()

    def accept(self):
        part = self.handler.doc.controller().activePart()
        if part != None:
            settings = {\
                'stapleScorer'    : autobreak.tgtLengthStapleScorer,\
                'minStapleLegLen' : self.minLegLengthSpinBox.value(),\
                'minStapleLen'    : self.minLengthSpinBox.value(),\
                'maxStapleLen'    : self.maxLengthSpinBox.value(),\
            }
            self.handler.win.pathGraphicsView.setViewportUpdateOn(False)
            # print "pre verify"
            # part.verifyOligos()
            # print "breakStaples"
            autobreak.breakStaples(part, settings)
            # print "post break verify"
            # part.verifyOligos()
            self.handler.win.pathGraphicsView.setViewportUpdateOn(True)
        self.close()
