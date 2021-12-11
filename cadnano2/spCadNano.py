###############################################################################
#
# Copyright 2011 Autodesk, Inc.  All rights reserved.
#
# The MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
###############################################################################


import os
import sys
import maya
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI
import maya.mel as mel
import sip

sys.path.insert(0, os.environ['CADNANO_PATH'])
# cmds.flushUndo()
# cmds.undoInfo(state=False)

import cadnano2.views.solidview.mayaHotKeys as mayaHotKeys
import cadnano2.views.solidview.mayaUI as mayaUI

import cadnano2.util as util
util.qtFrameworkList = ['PyQt'] # necessary to overide defaults
util.qtWrapImport('QtGui', globals(), ['qApp', 'QDockWidget', 'QSizePolicy'])

util.qtWrapImport('QtCore', globals(), ['Qt', 'QObject'])

kPluginName = "spCadNano"
gCadNanoButton = None
gCadNanoToolbar = None
fMayaExitingCB = None

gCadNanoApp = None

gIconPath = (
        os.environ['CADNANO_PATH'] +
        "/ui/mainwindow/images/cadnano2-app-icon_shelf.png")


# command
class openCadNano(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    def doIt(self, argList):
        openCN()

    @staticmethod
    def creator():
        return OpenMayaMPx.asMPxPtr(openCadNano())


class closeCadNano(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    def doIt(self, argList):
        closeCN()

    @staticmethod
    def creator():
        return OpenMayaMPx.asMPxPtr(closeCadNano())


def onExitingMaya(clientData):
    closeCN()
    mel.eval("savePrefs;")


def onHideEvent():
    closeCN()


# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerCommand("openCadNano", openCadNano.creator)
        mplugin.registerCommand("closeCadNano", closeCadNano.creator)
    except:
        sys.stderr.write("Failed to register command: %s\n" % kPluginName)
        raise
    addUIButton()
    global fMayaExitingCB
    fMayaExitingCB = OpenMaya.MSceneMessage.addCallback(
                                OpenMaya.MSceneMessage.kMayaExiting,
                                onExitingMaya)


# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    global gCadNanoApp
    closeCN()
    removeUIButton()

    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand("openCadNano")
        mplugin.deregisterCommand("closeCadNano")
    except:
        sys.stderr.write("Failed to unregister command: %s\n" % kPluginName)
        raise

    global fMayaExitingCB
    if (fMayaExitingCB != None):
        OpenMaya.MSceneMessage.removeCallback(fMayaExitingCB)


def openCN():
    global gCadNanoApp
    modifyMayaUI()
    isInit = False
    if gCadNanoApp:
        for x in gCadNanoApp.documentControllers:
            if x.win:
                x.windock.setVisible(True)
                x.win.setVisible(True)
    else:
        # begin program
        import cadnano
        gCadNanoApp =  cadnano.initAppMaya()
        isInit = True
        
    if gCadNanoApp.activeDocument:
        if hasattr(gCadNanoApp.activeDocument, 'solidHelixGrp'):
            if gCadNanoApp.activeDocument.solidHelixGrp:
                gCadNanoApp.activeDocument.solidHelixGrp.onPersistentDataChanged()

    pluginPath = os.path.join(os.environ['CADNANO_PATH'],
                                "controllers", "mayacontrollers")
    hmPath = os.path.join(pluginPath, "helixManip.py")
    msPath = os.path.join(pluginPath, "mayaSelectionContex.py")
    rmPath = os.path.join(pluginPath, "removedMsgCmd.py")
    if not cmds.pluginInfo(rmPath, query=True, loaded=True):
        cmds.loadPlugin(rmPath)
        cmds.spRemovedMsg()
    if not cmds.pluginInfo(msPath, query=True, loaded=True):
        cmds.loadPlugin(msPath)
        cmds.spMayaCtxCmd("spMayaCtxCmd1")
        cmds.setToolTo("spMayaCtxCmd1")
    if not cmds.pluginInfo(hmPath, query=True, loaded=True):
            cmds.loadPlugin(hmPath)
    
    if isInit:
        gCadNanoApp.finishInit()
# end def

def changed(self, event):
    print(str(event.type()))
    if (event.type() == QEvent.ActivationChange or
        event.type() == QEvent.WindowActivate or
        event.type() == QEvent.ApplicationActivate):
            print(self.win.windowTitle())
            app().activeDocument = self


def modifyMayaUI():
    mayaHotKeys.disableAllHotKeys()
    mayaUI.simplifyUI()
    mayaUI.setViewportQuality()

    myWindow = cmds.window()
    myForm = cmds.formLayout(parent=myWindow)
    global gCadNanoToolbar
    gCadNanoToolbar = cmds.toolBar(
                                "cadnanoBox",
                                area='top',
                                allowedArea='top',
                                content=myWindow)

    global gIconPath
    closeCadNanoCmd = 'import maya.cmds;maya.cmds.closeCadNano()'
    myButton = cmds.iconTextButton(
                               label='Quit cadnano',
                               annotation='Quit cadnano interface',
                               image1=gIconPath,
                               parent=myForm,
                               command=closeCadNanoCmd)
    cmds.formLayout(
                myForm,
                edit=True,
                attachForm=[(myButton, 'right', 10)])


def restoreMayaUI():
    mayaHotKeys.restoreAllHotKeys()
    mayaUI.restoreUI()
    mayaUI.restoreViewportQuality()

    if gCadNanoToolbar:
        if cmds.toolBar(gCadNanoToolbar, exists=True):
            cmds.deleteUI(gCadNanoToolbar)


def closeCN():
    global gCadNanoApp
    if gCadNanoApp:
        if gCadNanoApp.activeDocument:
            gCadNanoApp.activeDocument.win.setVisible(False)
            gCadNanoApp.activeDocument.windock.setVisible(False)
        for x in gCadNanoApp.documentControllers:
            if x.win:
                x.windock.setVisible(False)
                x.win.setVisible(False)
    restoreMayaUI()


def addUIButton():
    global gCadNanoButton
    global gIconPath
    mayaMainToolbar = (
            'MayaWindow|toolBar1|MainStatusLineLayout|formLayout5|formLayout8')
    if cmds.formLayout(mayaMainToolbar, ex=True):
        cmds.setParent(mayaMainToolbar)
        gCadNanoButton = cmds.iconTextButton(
                         label='cadnano',
                         annotation='Launch cadnano interface',
                         image1=gIconPath,
                         parent=mayaMainToolbar,
                         command='import maya.cmds; maya.cmds.openCadNano()')
        cmds.formLayout(
                    mayaMainToolbar,
                    edit=True,
                    attachForm=[(gCadNanoButton, 'right', 10)])


def removeUIButton():
    global gCadNanoButton
    cmds.deleteUI(gCadNanoButton)
