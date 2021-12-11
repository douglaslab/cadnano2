# Copyright 2011 Autodesk, Inc.  All rights reserved.
#
# The MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

"""
mayaSelectionContex.py
Created by Simon Breslav on 2011-09-27
Maya Selection Context, generates callbacks when things are selected
in Maya 3D view
"""

import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
from controllers.mayacontrollers.mayaObjectManager import Mom

contextCmdName = "spMayaCtxCmd"


def selectionCallback(clientData):
    """
    Callback function that is called when the selection changes in Maya.
    """
    clientData.deleteManipulators()
    #print "mayaSelcectionContex: selectionCallback called"
    selectionList = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList(selectionList)
    selectionIter = OpenMaya.MItSelectionList(selectionList)
    decoratorList = []
    helixList = []

    m = Mom()

    manipulator = None
    manipObject = OpenMaya.MObject()

    while not selectionIter.isDone():
        transformNode = OpenMaya.MObject()
        dagNode = OpenMaya.MFnDagNode()
        try:
            selectionIter.getDependNode(transformNode)
            if transformNode.isNull() or not transformNode.hasFn( \
                                    OpenMaya.MFn.kDependencyNode):
                next(selectionIter)
                continue
            dagNode = OpenMaya.MFnDagNode(transformNode)
        except:
            next(selectionIter)
            continue
        if dagNode.name().startswith(m.decoratorTransformName):
            if dagNode.name() not in decoratorList:
                decoratorList.append(dagNode.name())
        elif dagNode.name().startswith(m.helixTransformName):
            Unused, HNumber = dagNode.name().split("_")
            helixName = "%s%s" % (m.helixNodeName, HNumber)
            helixNode = m.getNodeFromName(helixName)
            if helixNode:
                helixList.append(helixName)
                if manipulator is None:
                    manipulator = \
                            OpenMayaMPx.MPxManipContainer.newManipulator(
                                                "spHelixManip", manipObject)
                    if manipulator is not None:
                        clientData.addManipulator(manipObject)
                manipulator.addHelix(HNumber)
                #print "selectionCallback ", dagNode.name(), helixNode
        next(selectionIter)
    m.staplePreDecoratorSelected(decoratorList)
    if manipulator is not None:
        manipulator.finishedAddingHelices()
    m.strandsSelected(helixList)

    m.updateSelectionBoxes()


class mayaSelectionContext(OpenMayaMPx.MPxSelectionContext):
    """
    Maya Command that adds a callback function when something is selected
    """
    def __init__(self):
        """Initialize the commands"""
        OpenMayaMPx.MPxSelectionContext.__init__(self)

    def toolOnSetup(self, event):
        """Add the callback"""
        OpenMaya.MModelMessage.addCallback( \
                        OpenMaya.MModelMessage.kActiveListModified,
                                            selectionCallback, self)


class mayaSelctionCtxCmd(OpenMayaMPx.MPxContextCommand):
    def __init__(self):
        OpenMayaMPx.MPxContextCommand.__init__(self)

    def makeObj(self):
        return OpenMayaMPx.asMPxPtr(mayaSelectionContext())


def contextCmdCreator():
    """Wrapper function that created the command"""
    return OpenMayaMPx.asMPxPtr(mayaSelctionCtxCmd())


# initialize the script plug-in
def initializePlugin(mobject):
    """Register the context command with Maya"""
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerContextCommand(contextCmdName, contextCmdCreator)
    except:
        print("Failed to register context command: %s" % contextCmdName)
        raise


# uninitialize the script plug-in
def uninitializePlugin(mobject):
    """Remove the context command"""
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterContextCommand(contextCmdName)
    except:
        print("Failed to deregister context command: %s" % contextCmdName)
        raise
