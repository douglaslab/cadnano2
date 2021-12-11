from ..ui.dialogs.ui_preferences import Ui_Preferences
from ..views import styles
import cadnano2.util as util
from .. import cadnano
import os.path, zipfile, shutil, platform, subprocess, tempfile, errno
util.qtWrapImport('QtCore', globals(), ['QObject', 'QSettings', 'pyqtSlot', 'Qt'])
util.qtWrapImport('QtWidgets', globals(), ['QWidget', 'QDialogButtonBox',
                                           'QTableWidgetItem', 'QFileDialog',
                                           'QMessageBox'])


class Preferences(object):
    """docstring for Preferences"""
    def __init__(self):
        self.qs = QSettings()
        self.uiPrefs = Ui_Preferences()
        self.widget = QWidget()
        self.uiPrefs.setupUi(self.widget)
        self.readPreferences()
        self.widget.addAction(self.uiPrefs.actionClose)
        self.uiPrefs.actionClose.triggered.connect(self.hideDialog)
        self.uiPrefs.honeycombRowsSpinBox.valueChanged.connect(self.setHoneycombRows)
        self.uiPrefs.honeycombColsSpinBox.valueChanged.connect(self.setHoneycombCols)
        self.uiPrefs.honeycombStepsSpinBox.valueChanged.connect(self.setHoneycombSteps)
        self.uiPrefs.squareRowsSpinBox.valueChanged.connect(self.setSquareRows)
        self.uiPrefs.squareColsSpinBox.valueChanged.connect(self.setSquareCols)
        self.uiPrefs.squareStepsSpinBox.valueChanged.connect(self.setSquareSteps)
        self.uiPrefs.autoScafComboBox.currentIndexChanged.connect(self.setAutoScaf)
        self.uiPrefs.defaultToolComboBox.currentIndexChanged.connect(self.setStartupTool)
        self.uiPrefs.zoomSpeedSlider.valueChanged.connect(self.setZoomSpeed)
        # self.uiPrefs.helixAddCheckBox.toggled.connect(self.setZoomToFitOnHelixAddition)
        self.uiPrefs.buttonBox.clicked.connect(self.handleButtonClick)
        self.uiPrefs.addPluginButton.clicked.connect(self.addPlugin)

    def showDialog(self):
        # self.exec_()
        self.readPreferences()
        self.widget.show()  # launch prefs in mode-less dialog

    def hideDialog(self):
        self.widget.hide()

    # @pyqtSlot(object)
    def handleButtonClick(self, button):
        """
        Restores defaults. Other buttons are ignored because connections
        are already set up in qt designer.
        """
        if self.uiPrefs.buttonBox.buttonRole(button) == QDialogButtonBox.ButtonRole.ResetRole:
            self.restoreDefaults()

    def readPreferences(self):
        self.qs.beginGroup("Preferences")
        self.honeycombRows = self.qs.value("honeycombRows", styles.HONEYCOMB_PART_MAXROWS)
        self.honeycombCols = self.qs.value("honeycombCols", styles.HONEYCOMB_PART_MAXCOLS)
        self.honeycombSteps = self.qs.value("honeycombSteps", styles.HONEYCOMB_PART_MAXSTEPS)
        self.squareRows = self.qs.value("squareRows", styles.SQUARE_PART_MAXROWS)
        self.squareCols = self.qs.value("squareCols", styles.SQUARE_PART_MAXCOLS)
        self.squareSteps = self.qs.value("squareSteps", styles.SQUARE_PART_MAXSTEPS)
        self.autoScafIndex = self.qs.value("autoScaf", styles.PREF_AUTOSCAF_INDEX)
        self.startupToolIndex = self.qs.value("startupTool", styles.PREF_STARTUP_TOOL_INDEX)
        self.zoomSpeed = self.qs.value("zoomSpeed", styles.PREF_ZOOM_SPEED)
        self.zoomOnHelixAdd = self.qs.value("zoomOnHelixAdd", styles.PREF_ZOOM_AFTER_HELIX_ADD)
        self.qs.endGroup()
        self.uiPrefs.honeycombRowsSpinBox.setProperty("value", self.honeycombRows)
        self.uiPrefs.honeycombColsSpinBox.setProperty("value", self.honeycombCols)
        self.uiPrefs.honeycombStepsSpinBox.setProperty("value", self.honeycombSteps)
        self.uiPrefs.squareRowsSpinBox.setProperty("value", self.squareRows)
        self.uiPrefs.squareColsSpinBox.setProperty("value", self.squareCols)
        self.uiPrefs.squareStepsSpinBox.setProperty("value", self.squareSteps)
        self.uiPrefs.autoScafComboBox.setCurrentIndex(self.autoScafIndex)
        self.uiPrefs.defaultToolComboBox.setCurrentIndex(self.startupToolIndex)
        self.uiPrefs.zoomSpeedSlider.setProperty("value", self.zoomSpeed)
        ptw = self.uiPrefs.pluginTableWidget
        loadedPluginPaths = list(cadnano.loadedPlugins.keys())
        ptw.setRowCount(len(loadedPluginPaths))
        for i in range(len(loadedPluginPaths)):
            row = QTableWidgetItem(loadedPluginPaths[i])
            row.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            ptw.setItem(i, 0, row)
        # self.uiPrefs.helixAddCheckBox.setChecked(self.zoomOnHelixAdd)

    def restoreDefaults(self):
        self.uiPrefs.honeycombRowsSpinBox.setProperty("value", styles.HONEYCOMB_PART_MAXROWS)
        self.uiPrefs.honeycombColsSpinBox.setProperty("value", styles.HONEYCOMB_PART_MAXCOLS)
        self.uiPrefs.honeycombStepsSpinBox.setProperty("value", styles.HONEYCOMB_PART_MAXSTEPS)
        self.uiPrefs.squareRowsSpinBox.setProperty("value", styles.SQUARE_PART_MAXROWS)
        self.uiPrefs.squareColsSpinBox.setProperty("value", styles.SQUARE_PART_MAXCOLS)
        self.uiPrefs.squareStepsSpinBox.setProperty("value", styles.SQUARE_PART_MAXSTEPS)
        self.uiPrefs.autoScafComboBox.setCurrentIndex(styles.PREF_AUTOSCAF_INDEX)
        self.uiPrefs.defaultToolComboBox.setCurrentIndex(styles.PREF_STARTUP_TOOL_INDEX)
        self.uiPrefs.zoomSpeedSlider.setProperty("value", styles.PREF_ZOOM_SPEED)
        # self.uiPrefs.helixAddCheckBox.setChecked(styles.PREF_ZOOM_AFTER_HELIX_ADD)

    def setHoneycombRows(self, rows):
        self.honeycombRows = rows
        self.qs.beginGroup("Preferences")
        self.qs.setValue("honeycombRows", self.honeycombRows)
        self.qs.endGroup()

    def setHoneycombCols(self, cols):
        self.honeycombCols = cols
        self.qs.beginGroup("Preferences")
        self.qs.setValue("honeycombCols", self.honeycombCols)
        self.qs.endGroup()

    def setHoneycombSteps(self, steps):
        self.honeycombSteps = steps
        self.qs.beginGroup("Preferences")
        self.qs.setValue("honeycombSteps", self.honeycombSteps)
        self.qs.endGroup()

    def setSquareRows(self, rows):
        self.squareRows = rows
        self.qs.beginGroup("Preferences")
        self.qs.setValue("squareRows", self.squareRows)
        self.qs.endGroup()

    def setSquareCols(self, cols):
        self.squareCols = cols
        self.qs.beginGroup("Preferences")
        self.qs.setValue("squareCols", self.squareCols)
        self.qs.endGroup()

    def setSquareSteps(self, steps):
        self.squareSteps = steps
        self.qs.beginGroup("Preferences")
        self.qs.setValue("squareSteps", self.squareSteps)
        self.qs.endGroup()

    def setAutoScaf(self, index):
        self.autoScafIndex = index
        self.qs.beginGroup("Preferences")
        self.qs.setValue("autoScaf", self.autoScafIndex)
        self.qs.endGroup()

    def setStartupTool(self, index):
        self.startupToolIndex = index
        self.qs.beginGroup("Preferences")
        self.qs.setValue("startupTool", self.startupToolIndex)
        self.qs.endGroup()

    def setZoomSpeed(self, speed):
        self.zoomSpeed = speed
        self.qs.beginGroup("Preferences")
        self.qs.setValue("zoomSpeed", self.zoomSpeed)
        self.qs.endGroup()

    # def setZoomToFitOnHelixAddition(self, checked):
    #     self.zoomOnHelixAdd = checked
    #     self.qs.beginGroup("Preferences")
    #     self.qs.setValue("zoomOnHelixAdd", self.zoomOnHelixAdd)
    #     self.qs.endGroup()

    def getAutoScafType(self):
        return ['Mid-seam', 'Raster'][self.autoScafIndex]

    def getStartupToolName(self):
        return ['Select', 'Pencil', 'Paint', 'AddSeq'][self.startupToolIndex]

    def addPlugin(self):
        fdialog = QFileDialog(
                    self.widget,
                    "Install Plugin",
                    cadnano.path(),
                    "Cadnano Plugins (*.cnp)")
        fdialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        fdialog.setWindowFlags(Qt.WindowType.Sheet)
        fdialog.setWindowModality(Qt.WindowModality.WindowModal)
        fdialog.filesSelected.connect(self.addPluginAtPath)
        self.fileopendialog = fdialog
        fdialog.open()

    def addPluginAtPath(self, fname):
        self.fileopendialog.close()
        fname = str(fname[0])
        print("Attempting to open plugin %s"%fname)
        try:
            zf = zipfile.ZipFile(fname, 'r')
        except Exception as e:
            self.failWithMsg("Plugin file seems corrupt: %s."%e)
            return
        tdir = tempfile.mkdtemp()
        try:
            for f in zf.namelist():
                if f.endswith('/'):
                    os.makedirs(os.path.join(tdir,f))
            for f in zf.namelist():
                if not f.endswith('/'):
                    zf.extract(f, tdir)
        except Exception as e:
            self.failWithMsg("Extraction of plugin archive failed: %s."%e)
            return
        filesInZip = [(f, os.path.join(tdir, f)) for f in os.listdir(tdir)]
        try:
            self.confirmDestructiveIfNecessary(filesInZip)
            self.removePluginsToBeOverwritten(filesInZip)
            self.movePluginsIntoPluginsFolder(filesInZip)
        except OSError:
            print("Couldn't copy files into plugin directory, attempting\
                   again after boosting privileges.")
            if platform.system() == 'Darwin':
                self.darwinAuthedMvPluginsIntoPluginsFolder(filesInZip)
            elif platform.system() == 'Linux':
                self.linuxAuthedMvPluginsIntoPluginsFolder(filesInZip)
            else:
                print("Can't boost privelages on platform %s"%platform.system())
        loadedAPlugin = cadnano.loadAllPlugins()
        if not loadedAPlugin:
            print("Unable to load anythng from plugin %s"%fname)
        self.readPreferences()
        shutil.rmtree(tdir)

    def darwinAuthedMvPluginsIntoPluginsFolder(self, filesInZip):
        envirn={"DST":cadnano.path()+'/plugins'}
        srcstr = ''
        for i in range(len(filesInZip)):
            fileName, filePath = filesInZip[i]
            srcstr += ' \\"$SRC' + str(i) + '\\"'
            envirn['SRC'+str(i)] = filePath
        proc = subprocess.Popen(['osascript','-e',\
                          'do shell script "cp -fR ' + srcstr +\
                          ' \\"$DST\\"" with administrator privileges'],\
                          env=envirn)
        retval = self.waitForProcExit(proc)
        if retval != 0:
            self.failWithMsg('cp failed with code %i'%retval)

    def linuxAuthedMvPluginsIntoPluginsFolder(self, filesInZip):
        args = ['gksudo', 'cp', '-fR']
        args.extend(filePath for fileName, filePath in filesInZip)
        args.append(cadnano.path()+'/plugins')
        proc = subprocess.Popen(args)
        retval = self.waitForProcExit(proc)
        if retval != 0:
            self.failWithMsg('cp failed with code %i'%retval)

    def confirmDestructiveIfNecessary(self, filesInZip):
        for fileName, filePath in filesInZip:
            target = os.path.join(cadnano.path(), 'plugins', fileName)
            if os.path.isfile(target):
                return self.confirmDestructive()
            elif os.path.isdir(target):
                return self.confirmDestructive()

    def confirmDestructive(self):
        mb = QMessageBox(self.widget)
        mb.setIcon(QMessageBox.Warning)
        mb.setInformativeText("The plugin you are trying to install\
has already been installed. Replace the currently installed one?")
        mb.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        mb.exec_()
        return mb.clickedButton() == mb.button(QMessageBox.Yes)
        
    def removePluginsToBeOverwritten(self, filesInZip):
        for fileName, filePath in filesInZip:
            target = os.path.join(cadnano.path(), 'plugins', fileName)
            if os.path.isfile(target):
                os.unlink(target)
            elif os.path.isdir(target):
                shutil.rmtree(target)

    def movePluginsIntoPluginsFolder(self, filesInZip):
        for fileName, filePath in filesInZip:
            target = os.path.join(cadnano.path(), 'plugins', fileName)
            shutil.move(filePath, target)

    def waitForProcExit(self, proc):
        procexit = False
        while not procexit:
            try:
                retval = proc.wait()
                procexit = True
            except OSError as e:
                if e.errno != errno.EINTR:
                    raise ose
        return retval

    def failWithMsg(self, str):
        mb = QMessageBox(self.widget)
        mb.setIcon(QMessageBox.Warning)
        mb.setInformativeText(str)
        mb.buttonClicked.connect(self.closeFailDialog)
        self.failMessageBox = mb
        mb.open()

    def closeFailDialog(self, button):
        self.failMessageBox.close()
        del self.failMessageBox