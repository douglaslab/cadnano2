import io
import os
from ..cadnano import app
from ..model.document import Document
from ..model.io.decoder import decode
from ..model.io.encoder import encode
from ..views.documentwindow import DocumentWindow
from ..views import styles
import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), ['QDir', 'QFileInfo', 'QRect',
                                        'QSettings',
                                        'QSize', 'Qt'])
util.qtWrapImport('QtGui', globals(), [
                                       'QIcon',
                                       'QKeySequence',
                                       'QPainter'
                                       ])
util.qtWrapImport('QtWidgets', globals(), ['QApplication',
                                           'QDialog',
                                           'QDockWidget',
                                           'QFileDialog',
                                           'QGraphicsItem',
                                           'QMainWindow',
                                           'QMessageBox',
                                           'QStyleOptionGraphicsItem'])
util.qtWrapImport('QtSvg', globals(), ['QSvgGenerator'])


class DocumentController():
    """
    Connects UI buttons to their corresponding actions in the model.
    """
    ### INIT METHODS ###
    def __init__(self):
        """docstring for __init__"""
        # initialize variables
        self._document = Document()
        self._document.setController(self)
        self._activePart = None
        self._filename = None
        self._fileOpenPath = None  # will be set in _readSettings
        self._hasNoAssociatedFile = True
        self._pathViewInstance = None
        self._sliceViewInstance = None
        self._undoStack = None
        self.win = None
        self.fileopendialog = None
        self.filesavedialog = None

        self.settings = QSettings()
        self._readSettings()

        QDir.addSearchPath('icons', 'ui/mainwindow/images/')

        # call other init methods
        self._initWindow()
        if app().isInMaya():
            self._initMaya()
        app().documentControllers.add(self)

    def _initWindow(self):
        """docstring for initWindow"""
        self.win = DocumentWindow(docCtrlr=self)
        self.win.setWindowIcon(QIcon('icons:cadnano2-app-icon.png'))
        app().documentWindowWasCreatedSignal.emit(self._document, self.win)
        self._connectWindowSignalsToSelf()
        self.win.show()

    def _initMaya(self):
        """
        Initialize Maya-related state. Delete Maya nodes if there
        is an old document left over from the same session. Set up
        the Maya window.
        """
        # There will only be one document
        if (app().activeDocument and app().activeDocument.win and
                                not app().activeDocument.win.close()):
            return
        del app().activeDocument
        app().activeDocument = self

        import maya.OpenMayaUI as OpenMayaUI
        import sip
        ptr = OpenMayaUI.MQtUtil.mainWindow()
        mayaWin = sip.wrapinstance(int(ptr), QMainWindow)
        self.windock = QDockWidget("cadnano")
        self.windock.setFeatures(QDockWidget.DockWidgetMovable
                                 | QDockWidget.DockWidgetFloatable)
        self.windock.setAllowedAreas(Qt.LeftDockWidgetArea
                                     | Qt.RightDockWidgetArea)
        self.windock.setWidget(self.win)
        mayaWin.addDockWidget(Qt.DockWidgetArea(Qt.LeftDockWidgetArea),
                                self.windock)
        self.windock.setVisible(True)

    def destroyDC(self):
        self.disconnectSignalsToSelf()
        if self.win is not None:
            self.win.destroyWin()
            self.win = None
    # end def

    def disconnectSignalsToSelf(self):
        win = self.win
        if win is not None:
            win.actionNew.triggered.disconnect(self.actionNewSlot)
            win.actionOpen.triggered.disconnect(self.actionOpenSlot)
            win.actionDrop.triggered.disconnect(self.actionDropSlot)
            win.actionClose.triggered.disconnect(self.actionCloseSlot)
            win.actionSave.triggered.disconnect(self.actionSaveSlot)
            win.actionSave_As.triggered.disconnect(self.actionSaveAsSlot)
            win.actionSVG.triggered.disconnect(self.actionSVGSlot)
            win.actionAutoStaple.triggered.disconnect(self.actionAutostapleSlot)
            win.actionExportStaples.triggered.disconnect(self.actionExportStaplesSlot)
            win.actionPreferences.triggered.disconnect(self.actionPrefsSlot)
            win.actionModify.triggered.disconnect(self.actionModifySlot)
            win.actionNewHoneycombPart.triggered.disconnect(self.actionAddHoneycombPartSlot)
            win.actionNewSquarePart.triggered.disconnect(self.actionAddSquarePartSlot)
            win.closeEvent = self.windowCloseEventHandler
            win.actionAbout.triggered.disconnect(self.actionAboutSlot)
            win.actionCadnanoWebsite.triggered.disconnect(self.actionCadnanoWebsiteSlot)
            win.actionFeedback.triggered.disconnect(self.actionFeedbackSlot)
            win.actionFilterHandle.triggered.disconnect(self.actionFilterHandleSlot)
            win.actionFilterEndpoint.triggered.disconnect(self.actionFilterEndpointSlot)
            win.actionFilterStrand.triggered.disconnect(self.actionFilterStrandSlot)
            win.actionFilterXover.triggered.disconnect(self.actionFilterXoverSlot)
            win.actionFilterScaf.triggered.disconnect(self.actionFilterScafSlot)
            win.actionFilterStap.triggered.disconnect(self.actionFilterStapSlot)
            win.actionRenumber.triggered.disconnect(self.actionRenumberSlot)
    # end def

    def _connectWindowSignalsToSelf(self):
        """This method serves to group all the signal & slot connections
        made by DocumentController"""
        self.win.actionNew.triggered.connect(self.actionNewSlot)
        self.win.actionOpen.triggered.connect(self.actionOpenSlot)
        self.win.actionDrop.triggered.connect(self.actionDropSlot)
        self.win.actionClose.triggered.connect(self.actionCloseSlot)
        self.win.actionSave.triggered.connect(self.actionSaveSlot)
        self.win.actionSave_As.triggered.connect(self.actionSaveAsSlot)
        self.win.actionSVG.triggered.connect(self.actionSVGSlot)
        self.win.actionAutoStaple.triggered.connect(self.actionAutostapleSlot)
        self.win.actionExportStaples.triggered.connect(self.actionExportStaplesSlot)
        self.win.actionPreferences.triggered.connect(self.actionPrefsSlot)
        self.win.actionModify.triggered.connect(self.actionModifySlot)
        self.win.actionNewHoneycombPart.triggered.connect(self.actionAddHoneycombPartSlot)
        self.win.actionNewSquarePart.triggered.connect(self.actionAddSquarePartSlot)
        self.win.closeEvent = self.windowCloseEventHandler
        self.win.actionAbout.triggered.connect(self.actionAboutSlot)
        self.win.actionCadnanoWebsite.triggered.connect(self.actionCadnanoWebsiteSlot)
        self.win.actionFeedback.triggered.connect(self.actionFeedbackSlot)
        self.win.actionFilterHandle.triggered.connect(self.actionFilterHandleSlot)
        self.win.actionFilterEndpoint.triggered.connect(self.actionFilterEndpointSlot)
        self.win.actionFilterStrand.triggered.connect(self.actionFilterStrandSlot)
        self.win.actionFilterXover.triggered.connect(self.actionFilterXoverSlot)
        self.win.actionFilterScaf.triggered.connect(self.actionFilterScafSlot)
        self.win.actionFilterStap.triggered.connect(self.actionFilterStapSlot)
        self.win.actionRenumber.triggered.connect(self.actionRenumberSlot)


    ### SLOTS ###
    def undoStackCleanChangedSlot(self):
        """The title changes to include [*] on modification."""
        self.win.setWindowModified(not self.undoStack().isClean())
        self.win.setWindowTitle(self.documentTitle())

    def actionAboutSlot(self):
        """Displays the about cadnano dialog."""
        from cadnano2.ui.dialogs.ui_about import Ui_About
        dialog = QDialog()
        dialogAbout = Ui_About()  # reusing this dialog, should rename
        dialog.setStyleSheet("QDialog { background-image: url(ui/dialogs/images/cadnano2-about.png); background-repeat: none; }")
        dialogAbout.setupUi(dialog)
        dialog.exec()

    filterList = ["strand", "endpoint", "xover", "virtualHelix"]
    def actionFilterHandleSlot(self):
        """Disables all other selection filters when active."""
        fH = self.win.actionFilterHandle
        fE = self.win.actionFilterEndpoint
        fS = self.win.actionFilterStrand
        fX = self.win.actionFilterXover
        fH.setChecked(True)
        if fE.isChecked():
            fE.setChecked(False)
        if fS.isChecked():
            fS.setChecked(False)
        if fX.isChecked():
            fX.setChecked(False)
        self._document.documentSelectionFilterChangedSignal.emit(["virtualHelix"])

    def actionFilterEndpointSlot(self):
        """
        Disables handle filters when activated.
        Remains checked if no other item-type filter is active.
        """
        fH = self.win.actionFilterHandle
        fE = self.win.actionFilterEndpoint
        fS = self.win.actionFilterStrand
        fX = self.win.actionFilterXover
        if fH.isChecked():
            fH.setChecked(False)
        if not fS.isChecked() and not fX.isChecked():
            fE.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def actionFilterStrandSlot(self):
        """
        Disables handle filters when activated.
        Remains checked if no other item-type filter is active.
        """
        fH = self.win.actionFilterHandle
        fE = self.win.actionFilterEndpoint
        fS = self.win.actionFilterStrand
        fX = self.win.actionFilterXover
        if fH.isChecked():
            fH.setChecked(False)
        if not fE.isChecked() and not fX.isChecked():
            fS.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def actionFilterXoverSlot(self):
        """
        Disables handle filters when activated.
        Remains checked if no other item-type filter is active.
        """
        fH = self.win.actionFilterHandle
        fE = self.win.actionFilterEndpoint
        fS = self.win.actionFilterStrand
        fX = self.win.actionFilterXover
        if fH.isChecked():
            fH.setChecked(False)
        if not fE.isChecked() and not fS.isChecked():
            fX.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def actionFilterScafSlot(self):
        """Remains checked if no other strand-type filter is active."""
        fSc = self.win.actionFilterScaf
        fSt = self.win.actionFilterStap
        if not fSc.isChecked() and not fSt.isChecked():
            fSc.setChecked(True)
        self._strandFilterUpdate()

    def actionFilterStapSlot(self):
        """Remains checked if no other strand-type filter is active."""
        fSc = self.win.actionFilterScaf
        fSt = self.win.actionFilterStap
        if not fSc.isChecked() and not fSt.isChecked():
            fSt.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def _strandFilterUpdate(self):
        win = self.win
        filterList = []
        if win.actionFilterEndpoint.isChecked():
            filterList.append("endpoint")
        if win.actionFilterStrand.isChecked():
            filterList.append("strand")
        if win.actionFilterXover.isChecked():
            filterList.append("xover")
        if win.actionFilterScaf.isChecked():
            filterList.append("scaffold")
        if win.actionFilterStap.isChecked():
            filterList.append("staple")
        self._document.documentSelectionFilterChangedSignal.emit(filterList)
    # end def

    def actionNewSlot(self):
        """
        1. If document is has no parts, do nothing.
        2. If document is dirty, call maybeSave and continue if it succeeds.
        3. Create a new document and swap it into the existing ctrlr/window.
        """
        # clear/reset the view!

        if len(self._document.parts()) == 0:
            return  # no parts
        if self.maybeSave() == False:
            return  # user canceled in maybe save
        else:  # user did not cancel
            if self.filesavedialog != None:
                self.filesavedialog.finished.connect(self.newClickedCallback)
            else:  # user did not save
                self.newClickedCallback()  # finalize new

    def actionOpenSlot(self):
        """
        1. If document is untouched, proceed to open dialog.
        2. If document is dirty, call maybesave and continue if it succeeds.
        Downstream, the file is selected in openAfterMaybeSave,
        and the selected file is actually opened in openAfterMaybeSaveCallback.
        """
        if self.maybeSave() == False:
            return  # user canceled in maybe save
        else:  # user did not cancel
            if hasattr(self, "filesavedialog"): # user did save
                if self.filesavedialog != None:
                    self.filesavedialog.finished.connect(self.openAfterMaybeSave)
                else:
                    self.openAfterMaybeSave()  # windows
            else:  # user did not save
                self.openAfterMaybeSave()  # finalize new

    def actionDropSlot(self):
        """
        1. If document is untouched, proceed to open dialog.
        2. If document is dirty, call maybesave and continue if it succeeds.
        Equivalent to actionOpenSlot() for Drag and Drop Event.
        """
        if self.maybeSave() is False:
            return  # user canceled in maybe save
        else:  # user did not cancel
            if hasattr(self, "filesavedialog"):  # user did save
                if self.filesavedialog is not None:
                    self.filesavedialog.finished.connect(self.openDropAfterMaybeSave)
                else:
                    self.openDropAfterMaybeSave()  # windows
            else:  # user did not save
                self.openDropAfterMaybeSave()  # finalize new

    def actionCloseSlot(self):
        """This will trigger a Window closeEvent."""
        if util.isWindows():
            #print "close win"
            if self.win is not None:
                self.win.close()
            if not app().isInMaya():
                #print "exit app"
                import sys
                sys.exit(1)

    def actionSaveSlot(self):
        """SaveAs if necessary, otherwise overwrite existing file."""
        if self._hasNoAssociatedFile:
            self.saveFileDialog()
            return
        self.writeDocumentToFile()

    def actionSaveAsSlot(self):
        """Open a save file dialog so user can choose a name."""
        self.saveFileDialog()

    def actionSVGSlot(self):
        """docstring for actionSVGSlot"""
        fname = os.path.basename(str(self.filename()))
        if fname == None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()

        fdialog = QFileDialog(
                    self.win,
                    "%s - Save As" % QApplication.applicationName(),
                    directory,
                    "%s (*.svg)" % QApplication.applicationName())
        fdialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        fdialog.setWindowFlags(Qt.WindowType.Sheet)
        fdialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.svgsavedialog = fdialog
        self.svgsavedialog.filesSelected.connect(self.saveSVGDialogCallback)
        fdialog.open()

    class DummyChild(QGraphicsItem):
        def boundingRect(self):
            return QRect(200, 200) # self.parentObject().boundingRect()
        def paint(self, painter, option, widget=None):
            pass

    def saveSVGDialogCallback(self, selected):
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        if not fname or fname is None or os.path.isdir(fname):
            return False
        fname = str(fname)
        if not fname.lower().endswith(".svg"):
            fname += ".svg"
        if self.svgsavedialog != None:
            self.svgsavedialog.filesSelected.disconnect(self.saveSVGDialogCallback)
            del self.svgsavedialog  # prevents hang
            self.svgsavedialog = None

        generator = QSvgGenerator()
        generator.setFileName(fname)
        generator.setSize(QSize(200, 200))
        generator.setViewBox(QRect(0, 0, 2000, 2000))
        painter = QPainter()

        # Render through scene
        # painter.begin(generator)
        # self.win.pathscene.render(painter)
        # painter.end()

        # Render item-by-item
        painter = QPainter()
        styleOption = QStyleOptionGraphicsItem()
        q = [self.win.pathroot]
        painter.begin(generator)
        while q:
            graphicsItem = q.pop()
            transform = graphicsItem.itemTransform(self.win.sliceroot)[0]
            painter.setTransform(transform)
            if graphicsItem.isVisible():
                graphicsItem.paint(painter, styleOption, None)
                q.extend(graphicsItem.childItems())
        painter.end()

    def actionExportStaplesSlot(self):
        """
        Triggered by clicking Export Staples button. Opens a file dialog to
        determine where the staples should be saved. The callback is
        exportStaplesCallback which collects the staple sequences and exports
        the file.
        """
        # Validate that no staple oligos are loops.
        part = self.activePart()
        stapLoopOlgs = part.getStapleLoopOligos()
        if stapLoopOlgs:
            from ui.dialogs.ui_warning import Ui_Warning
            dialog = QDialog()
            dialogWarning = Ui_Warning()  # reusing this dialog, should rename
            dialog.setStyleSheet("QDialog { background-image: url(ui/dialogs/images/cadnano2-about.png); background-repeat: none; }")
            dialogWarning.setupUi(dialog)

            locs = ", ".join([o.locString() for o in stapLoopOlgs])
            msg = "Part contains staple loop(s) at %s.\n\nUse the break tool to introduce 5' & 3' ends before exporting. Loops have been colored red; use undo to revert." % locs
            dialogWarning.title.setText("Staple validation failed")
            dialogWarning.message.setText(msg)
            for o in stapLoopOlgs:
                o.applyColor(styles.stapColors[0].name())
            dialog.exec()
            return

        # Proceed with staple export.
        fname = self.filename()
        if fname == None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()
        if util.isWindows():  # required for native looking file window
            fname = QFileDialog.getSaveFileName(
                            self.win,
                            "%s - Export As" % QApplication.applicationName(),
                            directory,
                            "(*.csv)")
            self.saveStaplesDialog = None
            self.exportStaplesCallback(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(
                            self.win,
                            "%s - Export As" % QApplication.applicationName(),
                            directory,
                            "(*.csv)")
            fdialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            fdialog.setWindowFlags(Qt.WindowType.Sheet)
            fdialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.saveStaplesDialog = fdialog
            self.saveStaplesDialog.filesSelected.connect(self.exportStaplesCallback)
            fdialog.open()
    # end def

    def actionPrefsSlot(self):
        app().prefsClicked()

    def actionAutostapleSlot(self):
        part = self.activePart()
        if part:
            self.win.pathGraphicsView.setViewportUpdateOn(False)
            part.autoStaple()
            self.win.pathGraphicsView.setViewportUpdateOn(True)

    def actionModifySlot(self):
        """
        Notifies that part root items that parts should respond to modifier
        selection signals.
        """
        # uncomment for debugging
        # isChecked = self.win.actionModify.isChecked()
        # self.win.pathroot.setModifyState(isChecked)
        # self.win.sliceroot.setModifyState(isChecked)
        if app().isInMaya():
            isChecked = self.win.actionModify.isChecked()
            self.win.pathroot.setModifyState(isChecked)
            self.win.sliceroot.setModifyState(isChecked)
            self.win.solidroot.setModifyState(isChecked)

    def actionAddHoneycombPartSlot(self):
        """docstring for actionAddHoneycombPartSlot"""
        part = self._document.addHoneycombPart()
        self.setActivePart(part)

    def actionAddSquarePartSlot(self):
        """docstring for actionAddSquarePartSlot"""
        part = self._document.addSquarePart()
        self.setActivePart(part)

    def actionRenumberSlot(self):
        coordList = self.win.pathroot.getSelectedPartOrderedVHList()
        part = self.activePart()
        part.renumber(coordList)
    # end def

    ### ACCESSORS ###
    def document(self):
        return self._document

    def window(self):
        return self.win

    def setDocument(self, doc):
        """
        Sets the controller's document, and informs the document that
        this is its controller.
        """
        self._document = doc
        doc.setController(self)

    def activePart(self):
        if self._activePart == None:
            self._activePart = self._document.selectedPart()
        return self._activePart

    def setActivePart(self, part):
        self._activePart = part

    def undoStack(self):
        return self._document.undoStack()

    ### PRIVATE SUPPORT METHODS ###
    def newDocument(self, doc=None, fname=None):
        """Creates a new Document, reusing the DocumentController."""
        self._document.resetViews()
        self._document.removeAllParts()  # clear out old parts
        self._document.undoStack().clear()  # reset undostack
        self._filename = fname if fname else "untitled.json"
        self._hasNoAssociatedFile = fname == None
        self._activePart = None
        self.win.setWindowTitle(self.documentTitle() + '[*]')

    def saveFileDialog(self):
        fname = self.filename()
        if fname == None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()
        if util.isWindows():  # required for native looking file window
            fname = QFileDialog.getSaveFileName(
                            self.win,
                            "%s - Save As" % QApplication.applicationName(),
                            directory,
                            "%s (*.json)" % QApplication.applicationName())
            self.writeDocumentToFile(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(
                            self.win,
                            "%s - Save As" % QApplication.applicationName(),
                            directory,
                            "%s (*.json)" % QApplication.applicationName())
            fdialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            fdialog.setWindowFlags(Qt.WindowType.Sheet)
            fdialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.filesavedialog = fdialog
            self.filesavedialog.filesSelected.connect(
                                                self.saveFileDialogCallback)
            fdialog.open()
    # end def

    def _readSettings(self):
        self.settings.beginGroup("FileSystem")
        self._fileOpenPath = self.settings.value("openpath", QDir().homePath())
        self.settings.endGroup()

    def _writeFileOpenPath(self, path):
        """docstring for _writePath"""
        self._fileOpenPath = path
        self.settings.beginGroup("FileSystem")
        self.settings.setValue("openpath", path)
        self.settings.endGroup()

    ### SLOT CALLBACKS ###
    def actionNewSlotCallback(self):
        """
        Gets called on completion of filesavedialog after newClicked's
        maybeSave. Removes the dialog if necessary, but it was probably
        already removed by saveFileDialogCallback.
        """
        if self.filesavedialog != None:
            self.filesavedialog.finished.disconnect(self.actionNewSlotCallback)
            del self.filesavedialog  # prevents hang (?)
            self.filesavedialog = None
        self.newDocument()

    def exportStaplesCallback(self, selected):
        """Export all staple sequences to selected CSV file.

        Args:
            selected (Tuple, List or str): if a List or Tuple, the filename
            should be the first element
        """
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        # Return if fname is '', None, or a directory path
        if not fname or fname is None or os.path.isdir(fname):
            return False
        # if not fname.lower().endswith(".txt"):
        #     fname += ".txt"
        if self.saveStaplesDialog is not None:
            self.saveStaplesDialog.filesSelected.disconnect(self.exportStaplesCallback)
            # manual garbage collection to prevent hang (in osx)
            del self.saveStaplesDialog
            self.saveStaplesDialog = None
        # write the file
        ap = self.activePart()
        if ap is not None:
            output = ap.getStapleSequences()
            with open(fname, 'w') as f:
                f.write(output)
    # end def

    def newClickedCallback(self):
        """
        Gets called on completion of filesavedialog after newClicked's
        maybeSave. Removes the dialog if necessary, but it was probably
        already removed by saveFileDialogCallback.
        """

        if self.filesavedialog != None:
            self.filesavedialog.finished.disconnect(self.newClickedCallback)
            del self.filesavedialog  # prevents hang (?)
            self.filesavedialog = None
        self.newDocument()

    def openAfterMaybeSaveCallback(self, selected):
        """
        Receives file selection info from the dialog created by
        openAfterMaybeSave, following user input.

        Extracts the file name and passes it to the decode method, which
        returns a new document doc, which is then set as the open document
        by newDocument. Calls finalizeImport and disconnects dialog signaling.
        """
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        if fname is None or fname == '' or os.path.isdir(fname):
            return False
        if not os.path.exists(fname):
            return False
        self._writeFileOpenPath(os.path.dirname(fname))
        self.newDocument(fname=fname)

        with io.open(fname, 'r', encoding='utf-8') as fd:
            decode(self._document, fd.read())

        if hasattr(self, "filesavedialog"):  # user did save
            if self.fileopendialog is not None:
                self.fileopendialog.filesSelected.disconnect(self.openAfterMaybeSaveCallback)
            # manual garbage collection to prevent hang (in osx)
            del self.fileopendialog
            self.fileopendialog = None

    def saveFileDialogCallback(self, selected):
        """If the user chose to save, write to that file."""
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        if fname is None or os.path.isdir(fname):
            return False
        if not fname.lower().endswith(".json"):
            fname += ".json"
        if self.filesavedialog is not None:
            self.filesavedialog.filesSelected.disconnect(self.saveFileDialogCallback)
            del self.filesavedialog  # prevents hang
            self.filesavedialog = None
        self.writeDocumentToFile(fname)
        self._writeFileOpenPath(os.path.dirname(fname))

    ### EVENT HANDLERS ###
    def windowCloseEventHandler(self, event):
        """Intercept close events when user attempts to close the window."""
        if self.maybeSave():
            event.accept()
            if app().isInMaya():
                self.windock.setVisible(False)
                del self.windock
                self.windock = None
            the_app = app()
            self.destroyDC()
            if the_app.documentControllers:
                the_app.destroyApp()
        else:
            event.ignore()
        self.actionCloseSlot()

    ### FILE INPUT ##
    def documentTitle(self):
        fname = os.path.basename(str(self.filename()))
        if not self.undoStack().isClean():
            fname += '[*]'
        return fname

    def filename(self):
        return self._filename

    def setFilename(self, proposedFName):
        if self._filename == proposedFName:
            return True
        self._filename = proposedFName
        self._hasNoAssociatedFile = False
        self.win.setWindowTitle(self.documentTitle())
        return True

    def openDropAfterMaybeSave(self):
        """
        This is the method that initiates file opening after a drag and Drop event.
        It is called by actionDropSlot.
        """
        fname = self.win._dropped_file
        if fname.endswith(".json"):
            self.openAfterMaybeSaveCallback(fname)
        else:
            print(f"Ignoring dropped file {fname}. Use a cadnano.json file.")

    def openAfterMaybeSave(self):
        """
        This is the method that initiates file opening. It is called by
        actionOpenSlot to spawn a QFileDialog and connect it to a callback
        method.
        """
        path = self._fileOpenPath
        if util.isWindows():  # required for native looking file window#"/",
            fname = QFileDialog.getOpenFileName(
                        None,
                        "Open Document", path,
                        "cadnano1 / cadnano2 Files (*.nno *.json *.cadnano)")
            self.filesavedialog = None
            self.openAfterMaybeSaveCallback(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(
                        self.win,
                        "Open Document",
                        path,
                        "cadnano1 / cadnano2 Files (*.nno *.json *.cadnano)")
            fdialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            fdialog.setWindowFlags(Qt.WindowType.Sheet)
            fdialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.fileopendialog = fdialog
            self.fileopendialog.filesSelected.connect(self.openAfterMaybeSaveCallback)
            fdialog.open()
    # end def

    ### FILE OUTPUT ###
    def maybeSave(self):
        """Save on quit, check if document changes have occured."""
        if app().dontAskAndJustDiscardUnsavedChanges:
            return True
        if not self.undoStack().isClean():    # document dirty?
            savebox = QMessageBox(QMessageBox.Icon.Question,   "Application",
                "The document has been modified.\nDo you want to save your changes?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                self.win,
                Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint | Qt.WindowType.Sheet)
            savebox.setWindowModality(Qt.WindowModality.WindowModal)
            save = savebox.button(QMessageBox.StandardButton.Save)
            discard = savebox.button(QMessageBox.StandardButton.Discard)
            cancel = savebox.button(QMessageBox.StandardButton.Cancel)
            save.setShortcut("Ctrl+S")
            discard.setShortcut(QKeySequence("D,Ctrl+D"))
            cancel.setShortcut(QKeySequence("C,Ctrl+C,.,Ctrl+."))
            ret = savebox.exec()
            del savebox  # manual garbage collection to prevent hang (in osx)
            if ret == QMessageBox.StandardButton.Save:
                return self.actionSaveAsSlot()
            elif ret == QMessageBox.StandardButton.Cancel:
                return False
        return True

    def writeDocumentToFile(self, filename=None):
        if filename == None:
            assert(not self._hasNoAssociatedFile)
            filename = self.filename()
        try:
            if util.isWindows():
                filename = filename[0]
            with open(filename, 'w') as f:
                helixOrderList = self.win.pathroot.getSelectedPartOrderedVHList()
                encode(self._document, helixOrderList, f)
        except IOError:
            flags = Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint | Qt.WindowType.Sheet
            errorbox = QMessageBox(QMessageBox.Critical,
                                   "cadnano",
                                   "Could not write to '%s'." % filename,
                                   QMessageBox.Ok,
                                   self.win,
                                   flags)
            errorbox.setWindowModality(Qt.WindowModality.WindowModal)
            errorbox.open()
            return False
        self.undoStack().setClean()
        self.setFilename(filename)
        return True

    def actionCadnanoWebsiteSlot(self):
        import webbrowser
        webbrowser.open("http://cadnano.org/")

    def actionFeedbackSlot(self):
        import webbrowser
        webbrowser.open("http://cadnano.org/feedback")
