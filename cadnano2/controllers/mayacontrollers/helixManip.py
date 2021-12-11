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
helixManip.py
Created by Alex Tessier on 2011-08
A Maya manip for controlling Helix Shape similar to the selectTool
"""

import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
from cadnano2.cadnano import app

# for controlling the nodes
from cadnano2.model.enum import StrandType
from controllers.mayacontrollers.mayaObjectManager import Mom


helixManipId = OpenMaya.MTypeId(0x00117702)
contextCmdName = "spHelixManipCtxCmd"
nodeName = "spHelixManip"


def project(a, b):
    c = OpenMaya.MVector()
    bn = b.normal()
    c.x = a.x * bn.x
    c.y = a.y * bn.y
    c.z = a.z * bn.z
    return c


class helixManip(OpenMayaMPx.MPxManipContainer):

    class helix():
        id = None
        helixName = ""
        helixNode = OpenMaya.MObject()
        helixTransform = OpenMaya.MObject()

        def __str__(self):
            return self.helixName

    startBaseFloatAttr = OpenMaya.MObject()
    endBaseFloatAttr = OpenMaya.MObject()

    frontDir = OpenMaya.MVector()
    backDir = OpenMaya.MVector()
    manipHandleOffset = 1
    fDistanceFrontManip = OpenMaya.MDagPath()
    fDistanceBackManip = OpenMaya.MDagPath()
    sp = OpenMaya.MPoint()
    cp = OpenMaya.MPoint()
    ep = OpenMaya.MPoint()
    ecp = OpenMaya.MPoint()

    isMouseDown = False

    deltaFront = 0
    deltaBack = 0
    # min/max range of delta (for different length strands)
    maxDelta = 0
    minDelta = 0

    helices = {}
    helicesNames = []
    ffpIdxMap = {}
    epIdxMap = {}

    frontDistance = 0
    backDistance = 0

    firstHelix = 0

    #static
    helixDragMarker = None
    dragMarkerName = "HelixManipDragMarker"
    transformName = dragMarkerName + "Transform"
    meshName = dragMarkerName + "Mesh"

    def createHelixDragMarker(self):

        if not helixManip.helixDragMarker == None:
            return helixManip.helixDragMarker

        try:
            cmds.createNode(
                        "transform",
                        name=helixManip.transformName,
                        skipSelect=True)
            cmds.setAttr("%s.rotateX" % helixManip.transformName, 90)

            cmds.createNode(
                        "mesh",
                        name=helixManip.meshName,
                        parent=helixManip.transformName,
                        skipSelect=True)
            cmds.createNode(
                        "polyPlane",
                        name=helixManip.dragMarkerName,
                        skipSelect=True)
            #cmds.setAttr("%s.width" % dragMarkerName, 1)
            #cmds.setAttr("%s.height" % dragMarkerName, 1)
            cmds.setAttr(
                    "%s.subdivisionsWidth" % helixManip.dragMarkerName, 1)
            cmds.setAttr(
                    "%s.subdivisionsHeight" % helixManip.dragMarkerName, 1)

            cmds.connectAttr("%s.output" % helixManip.dragMarkerName,
                             "%s.inMesh" % helixManip.meshName)

            helixManip.helixDragMarker = helixManip.transformName

        except:
            sys.stderr.write(
                        "helixManip: Error createHelixDragMarker\n")
            sys.stderr.write(sys.exc_info()[0])
            raise

        return helixManip.helixDragMarker

    def moveHelixDragMarkerTo(self, translation):
        cmds.setAttr(
            helixManip.transformName + ".translate",
            translation[0],
            translation[1],
            translation[2],
            type="double3")

    def __init__(self):
        OpenMayaMPx.MPxManipContainer.__init__(self)

    def addHelix(self, HNumber):

        m = Mom()

        h = self.helix()
        h.id = HNumber
        h.helixTransform = m.getNodeFromName(
                                    "%s%s" % (m.helixTransformName, HNumber))
        h.helixNode = m.getNodeFromName("%s%s" % (m.helixNodeName, HNumber))
        nodeFn = OpenMaya.MFnDependencyNode(h.helixNode)
        h.helixName = nodeFn.name()
        self.helices[h.id] = h

        self.helicesNames.append(h.helixName)

        # we only connect the first node, so that the update events trigger
        # the delta value will be the same for all the helices
        if(len(self.helices) == 1):
            self.firstHelix = h.id
            self.connectToDependNode(h)

    def finishedAddingHelices(self):
        self.finishAddingManips()
        #for (id, helix) in self.helices.iteritems():
        OpenMayaMPx.MPxManipContainer.connectToDependNode(
                                self, self.helices[self.firstHelix].helixNode)

    def createChildren(self):
        self.helices = {}
        self.helicesNames = []

        #print "helixManip: createChildren being called..."
        # startPoint should correspond to the end of the helix
        # read the attribute to get the offset from the starting position
        self.fDistanceFrontManip = self.addDistanceManip(
                                                "distanceManip", "distance")
        distanceManipFn = OpenMayaUI.MFnDistanceManip(self.fDistanceFrontManip)
        startPoint = OpenMaya.MPoint(0.0, 0.0, 0.0)
        self.frontDir = OpenMaya.MVector(0.0, 0.0, 1.0)
        distanceManipFn.setStartPoint(startPoint)
        distanceManipFn.setDirection(self.frontDir)

        self.fDistanceBackManip = self.addDistanceManip(
                                                "distancgeteManip", "distance")
        distanceManipFn = OpenMayaUI.MFnDistanceManip(self.fDistanceBackManip)
        startPoint = OpenMaya.MPoint(0.0, 0.0, 0.0)
        self.backDir = OpenMaya.MVector(0.0, 0.0, -1.0)
        distanceManipFn.setStartPoint(startPoint)
        distanceManipFn.setDirection(self.backDir)

    def draw(self, view, path, style, status):
        OpenMayaMPx.MPxManipContainer.draw(self, view, path, style, status)

        if not self.isMouseDown:
            return

        u = OpenMaya.MPoint()
        v = OpenMaya.MPoint()
        drawText = ""
        am = self.activeManip()
        m = self.getTransformMtxFromNode(
                                self.helices[self.firstHelix].helixTransform)
        if am is self.fDistanceFrontManip:
            drawText = str(self.deltaFront)
            if self.deltaFront > 0:
                drawText = "+" + drawText
            c = self.canMove(self.deltaFront)
            if c[0]:
                drawText = "<  " + drawText
            if c[1]:
                drawText = drawText + "  >"
            u = self.sp * m
            v = u + self.frontDir * self.frontDistance
        elif am is self.fDistanceBackManip:
            drawText = str(self.deltaBack)
            if self.deltaBack > 0:
                drawText = "+" + drawText
            c = self.canMove(self.deltaBack)
            if c[0]:
                drawText = "<  " + drawText
            if c[1]:
                drawText = drawText + "  >"
            u = self.ep * m
            v = u + self.backDir * self.backDistance

        w = OpenMaya.MPoint((u.x + v.x) / 2, (u.y + v.y) / 2, (u.z + v.z) / 2)

        view.beginGL()
        view.setDrawColor(OpenMaya.MColor(0.9, 0, 0))
        view.drawText(drawText, w, OpenMayaUI.M3dView.kCenter)
        view.endGL()

    def connectToDependNode(self, helix):
        #print "connectToDependNode called"
        nodeFn = OpenMaya.MFnDependencyNode(helix.helixNode)

        try:
            frontPlug = nodeFn.findPlug("startBaseFloat")
            backPlug = nodeFn.findPlug("endBaseFloat")

            frontManip = OpenMayaUI.MFnDistanceManip(self.fDistanceFrontManip)
            frontManip.connectToDistancePlug(frontPlug)

            backManip = OpenMayaUI.MFnDistanceManip(self.fDistanceBackManip)
            backManip.connectToDistancePlug(backPlug)

            # hookup the converter functions
            self.addPlugToManipConversion(frontManip.startPointIndex())
            self.addPlugToManipConversion(frontManip.currentPointIndex())
            self.addPlugToManipConversion(backManip.startPointIndex())
            self.addPlugToManipConversion(backManip.currentPointIndex())

            idx = self.addManipToPlugConversion(frontPlug)
            self.ffpIdxMap[idx] = helix
            idx = self.addManipToPlugConversion(backPlug)
            self.epIdxMap[idx] = helix

            # initially, current points and start/end points match
            startPos = nodeFn.findPlug("startPos")
            startPoint = self.getFloat3PlugValue(startPos)
            self.sp = startPoint
            self.cp = startPoint + self.frontDir * self.manipHandleOffset

            endPos = nodeFn.findPlug("endPos")
            endPoint = self.getFloat3PlugValue(endPos)
            self.ep = endPoint
            self.ecp = endPoint + self.backDir * self.manipHandleOffset

        except:
            sys.stderr.write(
                        "helixManip: Error finding and connecting plugs\n")
            sys.stderr.write(sys.exc_info()[0])
            raise

    def computeDistance(self, helix, sp, cp, dirv):
        # sp - start point, cp - current point
        u = OpenMaya.MVector(sp)
        v = OpenMaya.MVector(cp)
        w = u - v
        m = self.getTransformMtxFromNode(helix.helixTransform)
        wm = w * m
        if(wm.normal() * dirv.normal() > 0):  # dotproduct
            dir = -1
        else:
            dir = 1
        distance = w.length() * dir
        return distance

    def activeManip(self):

        try:
            activeManip = OpenMaya.MObject()
            self.isManipActive(OpenMaya.MFn.kDistanceManip, activeManip)

            m = Mom()
            if activeManip == self.fDistanceFrontManip.node():
                return self.fDistanceFrontManip
            elif activeManip == self.fDistanceBackManip.node():
                return self.fDistanceBackManip
        except:
            sys.stderr.write("ERROR: helixManip.activeManip\n")
            raise

        return None

    def calculateDeltaBounds(self):
        try:

            self.minDelta = float('-inf')
            self.maxDelta = float('inf')

            am = self.activeManip()
            for (id, helix) in self.helices.items():
                strand = self.getStrand(helix)
                lowIdx, highIdx = strand.idxs()

                minVal = 0
                maxVal = 0
                if am is self.fDistanceFrontManip:
                    lbound, ubound = strand.getResizeBounds(lowIdx)
                    minVal = lbound - lowIdx
                    maxVal = ubound - lowIdx
                elif am is self.fDistanceBackManip:
                    lbound, ubound = strand.getResizeBounds(highIdx)
                    minVal = lbound - highIdx
                    maxVal = ubound - highIdx
                    
                self.minDelta = max(minVal, self.minDelta)
                self.maxDelta = min(maxVal, self.maxDelta)

        except:
            print("calculateDeltaBounds failed!")
            raise

    def snapToXover(self, delta):

        am = self.activeManip()
        newDelta = delta

        try:
            for (id, helix) in self.helices.items():
                strand = self.getStrand(helix)
                idxL, idxH = strand.idxs()
                # idxL = idxL+delta if value[0] else idxL
                # idxH = idxH+delta if value[1] else idxH
                if am is self.fDistanceFrontManip and strand.connectionLow():
                    part = strand.virtualHelix().part()
                    newDelta = part.xoverSnapTo(strand, idxL, delta) - idxL
                elif am is self.fDistanceBackManip and strand.connectionHigh():
                    part = strand.virtualHelix().part()
                    newDelta = part.xoverSnapTo(strand, idxH, delta) - idxH
        except:
            sys.stderr.write("ERROR: helixManip.snapToXover\n")
            raise

        return newDelta

    def canMove(self, delta):

        dirLeft = False
        dirRight = False

        if self.snapToXover(delta) > self.snapToXover(self.minDelta):
            dirLeft = True
        if self.snapToXover(delta) < self.snapToXover(self.maxDelta):
            dirRight = True

        return (dirLeft, dirRight)

    def doPress(self):

        # print "PRESS"
        self.isMouseDown = True

        am = self.activeManip()

        m = Mom()
        m.strandsSelected(
                        self.helicesNames,
                        (am is self.fDistanceFrontManip,
                        am is self.fDistanceBackManip)
                        )

        self.createHelixDragMarker()
        selectedItems = cmds.ls(Mom().helixTransformName + "*", selection=True)
        bbox = cmds.exactWorldBoundingBox(selectedItems)

        cmds.setAttr(
                helixManip.transformName + ".scale",
                bbox[3] - bbox[0],
                0,
                bbox[4] - bbox[1],
                type="double3")

        z = 0
        if am is self.fDistanceFrontManip:
            z = bbox[5]
        elif am is self.fDistanceBackManip:
            z = bbox[2]

        self.moveHelixDragMarkerTo((
                                (bbox[0] + bbox[3]) / 2,
                                (bbox[1] + bbox[4]) / 2,
                                z
                                ))
        cmds.showHidden(helixManip.transformName)

        self.calculateDeltaBounds()

        return OpenMaya.kUnknownParameter

    def doRelease(self):
        # print "RELEASED"

        self.isMouseDown = False

        if(self.deltaFront != 0):
            app().activeDocument.document().resizeSelection(self.deltaFront)

        if(self.deltaBack != 0):
            app().activeDocument.document().resizeSelection(self.deltaBack)

        m = Mom()
        m.strandsSelected(self.helicesNames, (True, True))

        cmds.hide(helixManip.transformName)

        self.frontDistance = 0
        self.backDistance = 0

        return OpenMaya.kUnknownParameter

    def doDrag(self):
        #print "DRAGGING"

        am = self.activeManip()
        selectedItems = cmds.ls(Mom().helixTransformName + "*", selection=True)
        bbox = cmds.exactWorldBoundingBox(selectedItems)
        z = 0
        if am is self.fDistanceFrontManip:
            self.moveHelixDragMarkerTo((
                                (bbox[0] + bbox[3]) / 2,
                                (bbox[1] + bbox[4]) / 2,
                                bbox[5] + self.frontDistance
                                ))
        elif am is self.fDistanceBackManip:
            self.moveHelixDragMarkerTo((
                                (bbox[0] + bbox[3]) / 2,
                                (bbox[1] + bbox[4]) / 2,
                                bbox[2] - self.backDistance
                                ))

        return OpenMaya.kUnknownParameter

    def plugToManipConversion(self, manipIndex):

        #print "plugToManipCalled"

        manipData = OpenMayaUI.MManipData()
        try:

            frontManip = OpenMayaUI.MFnDistanceManip(self.fDistanceFrontManip)
            backManip = OpenMayaUI.MFnDistanceManip(self.fDistanceBackManip)

            boundBoxCenter = OpenMaya.MVector()
            boundBoxScale = OpenMaya.MVector()

            selectedItems = cmds.ls(
                                Mom().helixTransformName + "*", selection=True)
            bbox = cmds.exactWorldBoundingBox(selectedItems)
            boundBoxCenter.x = float((bbox[0] + bbox[3]) / 2)
            boundBoxCenter.y = float((bbox[1] + bbox[4]) / 2)
            boundBoxCenter.z = float((bbox[2] + bbox[5]) / 2)
            boundBoxScale.x = float(bbox[3] - bbox[0])
            boundBoxScale.y = float(bbox[4] - bbox[1])
            boundBoxScale.z = float(bbox[5] - bbox[2])

            if(manipIndex == frontManip.currentPointIndex()):

                ws = boundBoxCenter + project(boundBoxScale / 2, self.frontDir)
                ws += self.frontDir * \
                                (self.manipHandleOffset + self.frontDistance)

                numData = OpenMaya.MFnNumericData()
                numDataObj = numData.create(OpenMaya.MFnNumericData.k3Double)
                numData.setData3Double(ws.x, ws.y, ws.z)
                manipData = OpenMayaUI.MManipData(numDataObj)

            elif(manipIndex == backManip.currentPointIndex()):

                ws = boundBoxCenter + project(boundBoxScale / 2, self.backDir)
                ws += self.backDir * \
                                (self.manipHandleOffset + self.backDistance)

                numData = OpenMaya.MFnNumericData()
                numDataObj = numData.create(OpenMaya.MFnNumericData.k3Double)
                numData.setData3Double(ws.x, ws.y, ws.z)
                manipData = OpenMayaUI.MManipData(numDataObj)

            elif(manipIndex == frontManip.startPointIndex()):

                ws = boundBoxCenter + project(boundBoxScale / 2, self.frontDir)

                numData = OpenMaya.MFnNumericData()
                numDataObj = numData.create(OpenMaya.MFnNumericData.k3Float)
                numData.setData3Float(ws.x, ws.y, ws.z)
                manipData = OpenMayaUI.MManipData(numDataObj)

            elif(manipIndex == backManip.startPointIndex()):

                ws = boundBoxCenter + project(boundBoxScale / 2, self.backDir)

                numData = OpenMaya.MFnNumericData()
                numDataObj = numData.create(OpenMaya.MFnNumericData.k3Float)
                numData.setData3Float(ws.x, ws.y, ws.z)
                manipData = OpenMayaUI.MManipData(numDataObj)
        except:
            sys.stderr.write("ERROR: helixManip.plugToManipConversion\n")
            raise

        return manipData

    def manipToPlugConversion(self, plugIndex):
        #print "manipToPlugConversion", plugIndex

        try:

            if plugIndex in self.ffpIdxMap:  # front float plug
                helix = self.ffpIdxMap[plugIndex]
                numData = OpenMaya.MFnNumericData()
                numDataObj = numData.create(OpenMaya.MFnNumericData.k3Double)

                sp = OpenMaya.MPoint()
                cp = OpenMaya.MPoint()

                frontManip = OpenMayaUI.MFnDistanceManip(
                                                    self.fDistanceFrontManip)

                self.getConverterManipValue(frontManip.startPointIndex(), sp)
                self.getConverterManipValue(frontManip.currentPointIndex(), cp)

                m2 = self.getTransformMtxFromNode(helix.helixTransform)
                m = m2.inverse()

                self.sp = sp * m
                self.cp = cp * m

                # distance is...
                distance = self.computeDistance(
                                        helix, self.sp, self.cp, self.frontDir
                                                ) - self.manipHandleOffset

                self.frontDistance = distance

                delta = self.distanceToBase(helix, distance)
                self.resizeCNHelixFront(helix, delta)

                numData.setData3Double(cp.x, cp.y, cp.z)
                returnData = OpenMayaUI.MManipData(numDataObj)

            elif plugIndex in self.epIdxMap:
                helix = self.epIdxMap[plugIndex]
                numData = OpenMaya.MFnNumericData()
                numDataObj = numData.create(OpenMaya.MFnNumericData.k3Double)

                ep = OpenMaya.MPoint()
                ecp = OpenMaya.MPoint()

                backManip = OpenMayaUI.MFnDistanceManip(
                                                    self.fDistanceBackManip)

                self.getConverterManipValue(backManip.startPointIndex(), ep)
                self.getConverterManipValue(backManip.currentPointIndex(), ecp)

                m2 = self.getTransformMtxFromNode(helix.helixTransform)
                m = m2.inverse()

                self.ep = ep * m
                self.ecp = ecp * m

                # distance is...
                distance = self.computeDistance(
                                        helix, self.ep, self.ecp, self.backDir
                                                ) - self.manipHandleOffset

                self.backDistance = distance

                delta = self.distanceToBase(helix, distance)
                self.resizeCNHelixBack(helix, delta)

                numData.setData3Double(ecp.x, ecp.y, ecp.z)
                returnData = OpenMayaUI.MManipData(numDataObj)
        except:
            sys.stderr.write("ERROR: helixManip.manipToPlugConversion\n")
            raise

        return returnData

    def getTransformFromNode(self, trnsNode):
        try:
            dagFn = OpenMaya.MFnDagNode(trnsNode)
            path = OpenMaya.MDagPath()
            dagFn.getPath(path)
            transformFn = OpenMaya.MFnTransform(path)
            return transformFn
        except:
            print("getTransformFromNode -- unable to get transform from node")
            print(trnsNode)
            raise

    def getTransformMtxFromNode(self, trnsNode):
        mtx = OpenMaya.MMatrix()
        try:
            transformFn = self.getTransformFromNode(trnsNode)
            mm = transformFn.transformation()
            mtx = mm.asMatrix()
        except:
            print("Unable to get transformation matrix for node:")
            print(trnsNode)

        return mtx

    # Getting values out of references is a little crazy in the 1.0
    # Maya Python API....
    def getFloat3PlugValue(self, plug):
        # Retrieve the value as an MObject
        object = plug.asMObject()

        # TODO type checking that our plug is a float3 plug!
        # Convert the MObject to a float3
        numDataFn = OpenMaya.MFnNumericData(object)

        xParam = OpenMaya.MScriptUtil()
        xParam.createFromDouble(0.0)
        xPtr = xParam.asFloatPtr()

        yParam = OpenMaya.MScriptUtil()
        yParam.createFromDouble(0.0)
        yPtr = yParam.asFloatPtr()

        zParam = OpenMaya.MScriptUtil()
        zParam.createFromDouble(0.0)
        zPtr = zParam.asFloatPtr()

        numDataFn.getData3Float(xPtr, yPtr, zPtr)

        return OpenMaya.MPoint(OpenMaya.MScriptUtil.getFloat(xPtr),
                                OpenMaya.MScriptUtil.getFloat(yPtr),
                                OpenMaya.MScriptUtil.getFloat(zPtr))

    def getStrand(self, helix):
        m = Mom()
        return m.mayaToCn[helix.helixName]

    def getRise(self, helix):
        try:
            n = OpenMaya.MFnDependencyNode(helix.helixNode)
            risePlug = n.findPlug("rise")
            rise = risePlug.asDouble()
            return rise
        except:
            print("Failed to retrieve rise from helix %s" % helix.helixName)

    def distanceToBase(self, helix, distance):
        try:
            ## given a distance from the origin of the strand,
            ## compute the change in bases

            rise = self.getRise(helix)
            delta = int(distance / rise)

            return delta
        except:
            print("distanceToBase failed!")

    def baseToDistance(self, helix, base):
        try:
            ## given a distance from the origin of the strand,
            ## compute the change in bases

            rise = self.getRise(helix)
            distance = base * rise

            return distance
        except:
            print("baseToDistance failed!")

    def resizeCNHelixFront(self, helix, delta):
        #print "resizeCNHelixFront"
        try:
            strand = self.getStrand(helix)
            lowIdx, highIdx = strand.idxs()
            newLow = lowIdx - delta
            newLow = min(newLow, highIdx - 1)
            newLow = max(newLow, strand.part().minBaseIdx())

            self.deltaFront = newLow - lowIdx
            self.deltaFront = max(self.minDelta, self.deltaFront)
            self.deltaFront = min(self.maxDelta, self.deltaFront)

            self.deltaFront = self.snapToXover(self.deltaFront)

            self.frontDistance = -self.baseToDistance(helix, self.deltaFront)
        except:
            print("resizeCNHelixFront failed!")
            raise

    def resizeCNHelixBack(self, helix, delta):
        #print "resizeCNHelixBack"
        try:
            strand = self.getStrand(helix)
            lowIdx, highIdx = strand.idxs()
            newHigh = highIdx + delta
            newHigh = min(newHigh, strand.part().maxBaseIdx())
            newHigh = max(newHigh, lowIdx + 1)

            self.deltaBack = newHigh - highIdx
            self.deltaBack = max(self.minDelta, self.deltaBack)
            self.deltaBack = min(self.maxDelta, self.deltaBack)

            self.deltaBack = self.snapToXover(self.deltaBack)

            self.backDistance = self.baseToDistance(helix, self.deltaBack)
        except:
            print("resizeCNHelixBack failed!")
            raise


def helixManipCreator():
    #print "helixManip: helixManipCreator called"
    return OpenMayaMPx.asMPxPtr(helixManip())


def helixManipInitialize():
        #print "helixManip: helixManipInitialize called"
        OpenMayaMPx.MPxManipContainer.initialize()
        typedAttr = OpenMaya.MFnTypedAttribute()
        nAttr = OpenMaya.MFnNumericAttribute()

        helixManip.startBaseFloatAttr = \
            nAttr.create('helixManipStartPos',
            'hmsp',
            OpenMaya.MFnNumericData.kFloat,
            0.0)

        nAttr.setWritable(True)
        nAttr.setStorable(False)
        helixManip.endBaseFloatAttr = \
            nAttr.create('helixManipEndPos',
            'hmep',
            OpenMaya.MFnNumericData.kFloat,
            0.0)

        nAttr.setWritable(True)
        nAttr.setStorable(False)

        helixManip.addAttribute(helixManip.startBaseFloatAttr)
        helixManip.addAttribute(helixManip.endBaseFloatAttr)


# initialize the script plug-in
def initializePlugin(mobject):
    #print "helixManip: initializePlugin for helixManip called"
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerNode(nodeName, helixManipId, helixManipCreator,
                    helixManipInitialize, OpenMayaMPx.MPxNode.kManipContainer)
    except:
        print("helixManip: Failed to register node: %s" % nodeName)
        raise


# uninitialize the script plug-in
def uninitializePlugin(mobject):
    #print "helixManip uninitializePlugin for helixManip called"
    mplugin = OpenMayaMPx.MFnPlugin(mobject)

    try:
        mplugin.deregisterNode(helixManipId)
    except:
        print("helixManip: Failed to deregister node: %s" % nodeName)
        raise
