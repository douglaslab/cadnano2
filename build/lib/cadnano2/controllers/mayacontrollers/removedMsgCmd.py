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

# Example Code:
# from maya import cmds
# cmds.loadPlugin("removedMsgCmd.py")
# cmds.spRemovedMsg()

"""
removedMsgCmd.py
Created by Simon Breslav on 2011/09/06
A command that adds a callback function when Maya Nodes are deleted
"""

import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
from controllers.mayacontrollers.mayaObjectManager import Mom

kPluginCmdName = "spRemovedMsg"
messageId = 0
messageIdSet = False


def removeCallback(id):
    """
    Function to remove the callback function from Maya, given the ID of the
    function, the id is created in createParentRemovedCallback function
    """
    try:
        OpenMaya.MMessage.removeCallback(id)
    except:
        sys.stderr.write("Failed to remove callback\n")


def dagParentRemovedCallback(child, parent, clientData):
    """
    Callback function that removes the strands from the model if the
    3D strand is delete in 3D view.
    """
    mom = Mom()
    children = child.fullPathName().split("|")
    for c in children:
        if c.startswith(mom.helixMeshName):
            if c in mom.mayaToCn:
                strand = mom.mayaToCn[c]
                if strand:
                    # print "Strand %s : %s needs removal" % (c, strand)
                    mID = mom.strandMayaID(strand)
                    mom.removeIDMapping(mID, strand)
                    strand.strandSet().removeStrand(strand)
                else:
                    print("Error: no Strand inside mayaObjectModel")
            else:
                pass
                # print "dagParentRemovedCallback: %s already deleted" % c
        elif c.startswith(mom.decoratorMeshName):
            if c in mom.decoratorToVirtualHelixItem:
                pass
                #decoratorObject = mom.decoratorToVirtualHelixItem[ c ]
                #virtualHelixItem = decoratorObject[0]
                #virtualHelixItem.updateDecorators()


def createParentRemovedCallback(stringData):
    """
    Function that creates the actual callback function and returns its ID
    """
    # global declares module level variables that will be assigned
    global messageIdSet
    try:
        id = OpenMaya.MDagMessage.addParentRemovedCallback( \
                                    dagParentRemovedCallback, stringData)
    except:
        sys.stderr.write("Failed to install dag parent removed callback\n")
        messageIdSet = False
    else:
        messageIdSet = True
    return id


# command
class scriptedCommand(OpenMayaMPx.MPxCommand):
    """
    Maya Command that adds a callback function when something is removed
    """
    def __init__(self):
        """Initialize the commands"""
        OpenMayaMPx.MPxCommand.__init__(self)

    def doIt(self, argList):
        """Execute the command"""
        global messageId
        if (messageIdSet):
            print("Message callback already installed")
        else:
            print("Installing parent removed callback message")
            messageId = createParentRemovedCallback("_noData_")


# Creator
def cmdCreator():
    """Wrapper function that created the command"""
    return OpenMayaMPx.asMPxPtr(scriptedCommand())

# Initialize the script plug-in
def initializePlugin(mobject):
    """Register the command with Maya""" 
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerCommand(kPluginCmdName, cmdCreator)
    except:
        sys.stderr.write("Failed to register command: %s\n" % name)
        raise


# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    """Remove the command and the callback""" 
    # Remove the callback
    if (messageIdSet):
        removeCallback(messageId)
    # Remove the plug-in command
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand(kPluginCmdName)
    except:
        sys.stderr.write("Failed to unregister command: %s\n" % kPluginCmdName)
        raise
