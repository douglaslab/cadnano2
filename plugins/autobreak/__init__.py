from .autobreakconfig import AutobreakConfig
import cadnano, util
util.qtWrapImport('QtGui', globals(), ['QIcon', 'QPixmap'])
util.qtWrapImport('QtWidgets', globals(), ['QAction'])


class AutobreakHandler(object):
    def __init__(self, document, window):
        self.doc, self.win = document, window
        icon10 = QIcon()
        icon10.addPixmap(QPixmap(":/pathtools/autobreak"), QIcon.Normal, QIcon.Off)
        self.actionAutoBreak = QAction(window)
        self.actionAutoBreak.setIcon(icon10)
        self.actionAutoBreak.setText('AutoBreak')
        self.actionAutoBreak.setToolTip("Click this button to generate a default set of staples.")
        self.actionAutoBreak.setObjectName("actionAutoBreak")
        self.actionAutoBreak.triggered.connect(self.actionAutobreakSlot)
        self.win.menuPlugins.addAction(self.actionAutoBreak)
        # add to main tool bar
        self.win.topToolBar.insertAction(self.win.actionFiltersLabel, self.actionAutoBreak)
        self.win.topToolBar.insertSeparator(self.win.actionFiltersLabel)
        self.configDialog = None

    def actionAutobreakSlot(self):
        """Only show the dialog if staple strands exist."""
        part = self.doc.controller().activePart()
        if part != None:  # is there a part?
            for o in list(part.oligos()):
                if o.isStaple():  # is there a staple oligo?
                    if self.configDialog == None:
                        self.configDialog = AutobreakConfig(self.win, self)
                    self.configDialog.show()
                    return


def documentWindowWasCreatedSlot(doc, win):
    doc.autobreakHandler = AutobreakHandler(doc, win)

# Initialization
for c in cadnano.app().documentControllers:
    doc, win = c.document(), c.window()
    doc.autobreakHandler = AutobreakHandler(doc, win)
cadnano.app().documentWindowWasCreatedSignal.connect(documentWindowWasCreatedSlot)
