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
mayaObjectManager.py
Created by Alex Tessier on 2011-08
"""
from cadnano2.cadnano import app
import maya.cmds as cmds
import cadnano2.util as util
import maya.OpenMaya as OpenMaya


class Mom(object):
    """
    A singleton manager for tracking maya to cadnano and reverse lookups of
    strand and pre-decorators
    """
    _instance = None
    strandCount = 0
    selectionCountCache = 0

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Mom, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def myId(self):
        return id(self)

    # uses DNACylinderShape as as the key, stores strand objects
    mayaToCn = {}
    # uses strand objects as the key, stores a list of maya nodes
    cnToMaya = {}
    # uses stapleModIndicatorMesh% objects as the key,
    # stores a object with (virualHelixItem object, baseNumber, strand object)
    decoratorToVirtualHelixItem = {}
    # uses strand object as the key, stores stand id
    idStrandMapping = {}
    # Selection
    ignoreExternalSelectionSignal = False

    # Selection boxes
    selectionBox = cmds.polyCube(
                        constructionHistory=False,
                        createUVs=0,
                        object=True
                        )[0]
    cmds.hide(selectionBox)
    cmds.setAttr(selectionBox + ".overrideEnabled", True)
    cmds.setAttr(selectionBox + ".overrideDisplayType", 2)  # reference
    selectionBoxShader = "SelectionBoxShader"

    selectionBoxShader = cmds.shadingNode('lambert',
                                        asShader=True,
                                        name=selectionBoxShader)
    cmds.sets(name="%sSG" % selectionBoxShader,
                renderable=True,
                noSurfaceShader=True,
                empty=True)
    cmds.connectAttr("%s.outColor" % selectionBoxShader,
                    "%sSG.surfaceShader" % selectionBoxShader)
    cmds.setAttr("%s.transparency" % selectionBoxShader,
                    0.65, 0.65, 0.65, type="double3")
    cmds.setAttr("%s.incandescence" % selectionBoxShader,
                    0.5, 0.5, 0.5, type="double3")
    cmds.sets(
            selectionBox,
            forceElement="%sSG" % selectionBoxShader)

    # Endpoint Selection boxes
    epSelectionBox = cmds.polyCube(
                        constructionHistory=False,
                        createUVs=0,
                        object=True
                        )[0]
    cmds.hide(epSelectionBox)
    cmds.setAttr(epSelectionBox + ".overrideEnabled", True)
    cmds.setAttr(epSelectionBox + ".overrideDisplayType", 2)  # reference
    epSelectionBoxShader = "epSelectionBoxShader"

    epSelectionBoxShader = cmds.shadingNode('lambert',
                                        asShader=True,
                                        name=epSelectionBoxShader)
    cmds.sets(name="%sSG" % epSelectionBoxShader,
            renderable=True,
            noSurfaceShader=True,
            empty=True)
    cmds.connectAttr("%s.outColor" % epSelectionBoxShader,
                    "%sSG.surfaceShader" % epSelectionBoxShader)
    cmds.setAttr("%s.color" % epSelectionBoxShader,
                    0.8, 0.2, 0.2, type="double3")
    cmds.setAttr("%s.transparency" % epSelectionBoxShader,
                    0.75, 0.75, 0.75, type="double3")
    cmds.setAttr("%s.incandescence" % epSelectionBoxShader,
                    0.5, 0.5, 0.5, type="double3")
    cmds.sets(
            epSelectionBox,
            forceElement="%sSG" % epSelectionBoxShader)

    # MayaNames
    helixTransformName = "DNAShapeTransform_"
    helixNodeName = "HalfCylinderHelixNode_"
    helixMeshName = "DNACylinderShape_"
    helixShaderName = "DNAStrandShader_"
    decoratorTransformName = "stapleDecoratorTransform_"
    decoratorNodeName = "spStapleModIndicator_"
    decoratorMeshName = "stapleModIndicatorMesh_"
    decoratorShaderName = "stapleModeIndicatorShader_"

    def getNodeFromName(self, NodeName):
        #print "getNodeFromName ", NodeName
        selList = OpenMaya.MSelectionList()
        dependNode = 0
        if(cmds.objExists(NodeName)):
            selList.add(NodeName)
            dependNode = OpenMaya.MObject()
            selList.getDependNode(0, dependNode)
        return dependNode

    def getSelectionBox(self):
        return self.selectionBox

    def strandsSelected(self, listNames, value=(True, True)):
        if self.ignoreExternalSelectionSignal:
            return

        self.ignoreExternalSelectionSignal = True
        strandList = []
        for nodeName in listNames:
            if(nodeName in self.mayaToCn):
                strandList.append(self.mayaToCn[nodeName])
        doc = app().activeDocument
        # # XXX [SB] THIS IS A HACK, should not need to do this!!!
        # doc.win.pathroot.clearStrandSelections()

        doc.win.solidroot.selectedChanged(strandList, value)
        self.ignoreExternalSelectionSignal = False

    def staplePreDecoratorSelected(self, listNames):
        """
        Callback function that is called from mayaSelectionContext when a
        PreDecorator geometry is called, notifies the Part Model of this
        event. XXX - [SB] In the future we should clean up this interaction.
        """
        if(len(listNames) > 1):
            # If we have more than one PreDecorator Selected, deselect all but
            # the last one
            cmds.select(listNames[0:len(listNames) - 1], deselect=True)

        selectionList = []

        for name in listNames:
            if name in self.decoratorToVirtualHelixItem:
                (virtualHelixItem, baseIdx, strand) = \
                                        self.decoratorToVirtualHelixItem[name]
                selectionList.append((virtualHelixItem.row(),
                                                virtualHelixItem.col(),
                                                baseIdx))
        if len(selectionList) == 0 and \
           self.selectionCountCache == 0:
            # a dumb cache check to prevent deselection to be broadcasted too
            # many times, but could cause problems
            return

        # XXX - [SB] we want to only send the signal to "active part" but
        # not sure how to get that
        for doc in app().documentControllers:
            if doc.win.actionModify.isChecked():
                for partItem in doc.win.solidroot.partItems():
                    partModel = partItem.part()
                    partModel.selectPreDecorator(selectionList)
        self.selectionCountCache = len(selectionList)

    def removeDecoratorMapping(self, id):
        """Remove all mappings related to Pre-Decorators"""
        key1 = "%s%s" % (self.decoratorMeshName, id)
        key2 = "%s%s" % (self.decoratorTransformName, id)
        if key1 in self.decoratorToVirtualHelixItem:
            del self.decoratorToVirtualHelixItem[key1]
        if key2 in self.decoratorToVirtualHelixItem:
            del self.decoratorToVirtualHelixItem[key2]

    def removeIDMapping(self, id, strand):
        """Remove all mappings related to Strands"""
        key1 = "%s%s" % (self.helixMeshName, id)
        key2 = "%s%s" % (self.helixNodeName, id)
        if key1 in self.mayaToCn:
            del self.mayaToCn[key1]
        if key2 in self.mayaToCn:
            del self.mayaToCn[key2]
        self.deleteStrandMayaID(strand)

    def strandMayaID(self, strand):
        """
        Get a Maya ID for a given strand, if one does not exits, it
        will create a new one.
        """
        if(strand in self.idStrandMapping):
            return self.idStrandMapping[strand]
        else:
            self.strandCount += 1
            # XXX [SB+AT] NOT THREAD SAFE
            while cmds.objExists("%s%s" %
                                 (self.helixTransformName,
                                  self.strandCount)):
                self.strandCount += 1
            val = "%d" % self.strandCount
            self.idStrandMapping[strand] = val
            # print self.idStrandMapping
            return val
    # end def

    def deleteStrandMayaID(self, strand):
        """
        Removes just the Cadnano -> Maya mapping.
        It is called from removeIDMapping function
        """
        if strand in self.cnToMaya:
            del self.cnToMaya[strand]
        if strand in self.idStrandMapping:
            del self.idStrandMapping[strand]

    def updateSelectionBoxes(self):
        selectedItems = cmds.ls(self.helixTransformName + "*", selection=True)
        if selectedItems:
            bbox = cmds.exactWorldBoundingBox(selectedItems)
            cmds.setAttr(
                    self.selectionBox + ".scale",
                    bbox[3] - bbox[0],
                    bbox[4] - bbox[1],
                    bbox[5] - bbox[2],
                    type="double3")
            cmds.setAttr(
                    self.selectionBox + ".translate",
                    (bbox[0] + bbox[3]) / 2,
                    (bbox[1] + bbox[4]) / 2,
                    (bbox[2] + bbox[5]) / 2,
                    type="double3")
            cmds.showHidden(self.selectionBox)

            selectionDict = app().activeDocument.document().selectionDict()

            frontEp = 0
            backEp = 0

            for strandSetDict in selectionDict.values():
                for strand, value in strandSetDict.items():
                    frontEp += int(value[0])
                    backEp += int(value[1])

            if (frontEp == 0) ^ (backEp == 0):
                epBoundBox = None
                for strandSetDict in selectionDict.values():
                    for strand, value in strandSetDict.items():
                        # XXX The following line is a work around for broken
                        # path selection in model, remove when fixed
                        if not strand in self.cnToMaya:
                            continue
                        helixNode = self.cnToMaya[strand]
                        boundBox = cmds.exactWorldBoundingBox(helixNode[1])
                        # might be better to get the rise this way...
                        #n = OpenMaya.MFnDependencyNode(helixNode)
                        #risePlug = n.findPlug("rise")
                        #rise = risePlug.asDouble()
                        # but this works too
                        idxL, idxH = strand.idxs()
                        rise = (boundBox[5] - boundBox[2]) / (idxH - idxL + 1)
                        if frontEp == 0:
                            boundBox[5] = boundBox[2] + rise
                        elif backEp == 0:
                            boundBox[2] = boundBox[5] - rise
                        if epBoundBox == None:
                            epBoundBox = boundBox
                        else:
                            # union the boxes
                            epBoundBox[0] = min(epBoundBox[0], boundBox[0])
                            epBoundBox[1] = min(epBoundBox[1], boundBox[1])
                            epBoundBox[2] = min(epBoundBox[2], boundBox[2])
                            epBoundBox[3] = max(epBoundBox[3], boundBox[3])
                            epBoundBox[4] = max(epBoundBox[4], boundBox[4])
                            epBoundBox[5] = max(epBoundBox[5], boundBox[5])

                # XXX The following line is a work around for broken
                # path selection in model, remove when fixed
                if not epBoundBox == None:

                    cmds.showHidden(self.epSelectionBox)
                    cmds.setAttr(
                            self.epSelectionBox + ".scale",
                            epBoundBox[3] - epBoundBox[0],
                            epBoundBox[4] - epBoundBox[1],
                            epBoundBox[5] - epBoundBox[2],
                            type="double3")
                    cmds.setAttr(
                            self.epSelectionBox + ".translate",
                            (epBoundBox[0] + epBoundBox[3]) / 2,
                            (epBoundBox[1] + epBoundBox[4]) / 2,
                            (epBoundBox[2] + epBoundBox[5]) / 2,
                            type="double3")

            else:
                cmds.hide(self.epSelectionBox)

        else:
            cmds.hide(self.selectionBox)
            cmds.hide(self.epSelectionBox)
