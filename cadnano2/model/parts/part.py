#!/usr/bin/env python
# encoding: utf-8

from heapq import heapify, heappush, heappop
from itertools import product
from collections import defaultdict
import random

from cadnano2.model.enum import StrandType
from cadnano2.model.virtualhelix import VirtualHelix
from cadnano2.model.strand import Strand
from cadnano2.model.oligo import Oligo
from cadnano2.model.strandset import StrandSet
from cadnano2.views import styles

import cadnano2.util as util

util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject'])
util.qtWrapImport('QtGui', globals(), ['QUndoCommand'])


class Part(QObject):
    """
    A Part is a group of VirtualHelix items that are on the same lattice.
    Parts are the model component that most directly corresponds to a
    DNA origami design.

    Parts are always parented to the document.
    Parts know about their oligos, and the internal geometry of a part
    Copying a part recursively copies all elements in a part:
        VirtualHelices, Strands, etc

    PartInstances are parented to either the document or an assembly
    PartInstances know global position of the part
    Copying a PartInstance only creates a new PartInstance with the same
    Part(), with a mutable parent and position field.
    """

    _step = 21  # this is the period (in bases) of the part lattice
    _radius = 1.125  # nanometers
    _turnsPerStep = 2
    _helicalPitch = _step / _turnsPerStep
    _twistPerBase = 360 / _helicalPitch  # degrees

    def __init__(self, *args, **kwargs):
        """
        Sets the parent document, sets bounds for part dimensions, and sets up
        bookkeeping for partInstances, Oligos, VirtualHelix's, and helix ID
        number assignment.
        """
        if self.__class__ == Part:
            e = "This class is abstract. Perhaps you want HoneycombPart."
            raise NotImplementedError(e)
        self._document = kwargs.get('document', None)
        super(Part, self).__init__(parent=self._document)
        # Data structure
        self._insertions = defaultdict(dict)  # dict of insertions per virtualhelix
        self._oligos = set()
        self._coordToVirtualHelix = {}
        self._numberToVirtualHelix = {}
        # Dimensions
        self._maxRow = 50  # subclass overrides based on prefs
        self._maxCol = 50
        self._minBase = 0
        self._maxBase = int(2 * self._step - 1)
        # ID assignment
        self.oddRecycleBin, self.evenRecycleBin = [], []
        self.reserveBin = set()
        self._highestUsedOdd = -1  # Used in _reserveHelixIDNumber
        self._highestUsedEven = -2  # same
        self._importedVHelixOrder = None
        # Runtime state
        self._activeBaseIndex = self._step
        self._activeVirtualHelix = None
        self._activeVirtualHelixIdx = None

    # end def

    def __repr__(self):
        clsName = self.__class__.__name__
        return "<%s %s>" % (clsName, str(id(self))[-4:])

    ### SIGNALS ###
    partActiveSliceIndexSignal = pyqtSignal(QObject, int)  # self, index
    partActiveSliceResizeSignal = pyqtSignal(QObject)      # self
    partDimensionsChangedSignal = pyqtSignal(QObject)      # self
    partInstanceAddedSignal = pyqtSignal(QObject)          # self
    partParentChangedSignal = pyqtSignal(QObject)          # self
    partPreDecoratorSelectedSignal = pyqtSignal(object, int, int, int)  # row,col,idx
    partRemovedSignal = pyqtSignal(QObject)                # self
    partStrandChangedSignal = pyqtSignal(object, QObject)          # self, virtualHelix
    partVirtualHelixAddedSignal = pyqtSignal(object, QObject)      # self, virtualhelix
    partVirtualHelixRenumberedSignal = pyqtSignal(object, tuple)   # self, coord
    partVirtualHelixResizedSignal = pyqtSignal(object, tuple)      # self, coord
    partVirtualHelicesReorderedSignal = pyqtSignal(object, list)   # self, list of coords
    partHideSignal = pyqtSignal(QObject)
    partActiveVirtualHelixChangedSignal = pyqtSignal(QObject, QObject)

    ### SLOTS ###

    ### ACCESSORS ###
    def document(self):
        return self._document
    # end def

    def oligos(self):
        return self._oligos
    # end def

    def setDocument(self, document):
        self._document = document
    # end def

    def stepSize(self):
        return self._step
    # end def

    def subStepSize(self):
        """Note: _subStepSize is defined in subclasses."""
        return self._subStepSize
    # end def

    def undoStack(self):
        return self._document.undoStack()
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def virtualHelix(self, vhref, returnNoneIfAbsent=True):
        # vhrefs are the shiny new way to talk to part about its constituent
        # virtualhelices. Wherever you see f(...,vhref,...) you can
        # f(...,27,...)         use the virtualhelix's id number
        # f(...,vh,...)         use an actual virtualhelix
        # f(...,(1,42),...)     use the coordinate representation of its position
        """A vhref is the number of a virtual helix, the (row, col) of a virtual helix,
        or the virtual helix itself. For conveniece, CRUD should now work with any of them."""
        vh = None
        if type(vhref) in (int, int):
            vh = self._numberToVirtualHelix.get(vhref, None)
        elif type(vhref) in (tuple, list):
            vh = self._coordToVirtualHelix.get(vhref, None)
        else:
            vh = vhref
        if not isinstance(vh, VirtualHelix):
            if returnNoneIfAbsent:
                return None
            else:
                err = "Couldn't find the virtual helix in part %s "+\
                      "referenced by index %s" % (self, vhref)
                raise IndexError(err)
        return vh

    def activeBaseIndex(self):
        return self._activeBaseIndex
    # end def

    def activeVirtualHelix(self):
        return self._activeVirtualHelix
     # end def

    def activeVirtualHelixIdx(self):
        return self._activeVirtualHelixIdx
     # end def

    def dimensions(self):
        """Returns a tuple of the max X and maxY coordinates of the lattice."""
        return self.latticeCoordToPositionXY(self._maxRow, self._maxCol)
    # end def

    def getStapleSequences(self):
        """getStapleSequences"""
        s = "Start,End,Sequence,Length,Color\n"
        for oligo in self._oligos:
            if oligo.strand5p().strandSet().isStaple():
                s = s + oligo.sequenceExport()
        return s

    def getVirtualHelices(self):
        """yield an iterator to the virtualHelix references in the part"""
        return list(self._coordToVirtualHelix.values())
    # end def

    def indexOfRightmostNonemptyBase(self):
        """
        During reduction of the number of bases in a part, the first click
        removes empty bases from the right hand side of the part (red
        left-facing arrow). This method returns the new numBases that will
        effect that reduction.
        """
        ret = self._step - 1
        for vh in self.getVirtualHelices():
            ret = max(ret, vh.indexOfRightmostNonemptyBase())
        return ret
    # end def

    def insertions(self):
        """Return dictionary of insertions."""
        return self._insertions
    # end def

    def isEvenParity(self, row, column):
        """Should be overridden when subclassing."""
        raise NotImplementedError
    # end def

    def getStapleLoopOligos(self):
        """
        Returns staple oligos with no 5'/3' ends. Used by
        actionExportStaplesSlot in documentcontroller to validate before
        exporting staple sequences.
        """
        stapLoopOlgs = []
        for o in list(self.oligos()):
            if o.isStaple() and o.isLoop():
                stapLoopOlgs.append(o)
        return stapLoopOlgs

    def hasVirtualHelixAtCoord(self, coord):
        return coord in self._coordToVirtualHelix
    # end def

    def maxBaseIdx(self):
        return self._maxBase
    # end def

    def minBaseIdx(self):
        return self._minBase
    # end def

    def numberOfVirtualHelices(self):
        return len(self._coordToVirtualHelix)
    # end def

    def radius(self):
        return self._radius
    # end def

    def helicalPitch(self):
        return self._helicalPitch
    # end def

    def twistPerBase(self):
        return self._twistPerBase
    # end def

    def virtualHelixAtCoord(self, coord):
        """
        Looks for a virtualHelix at the coordinate, coord = (row, colum)
        if it exists it is returned, else None is returned
        """
        try:
            return self._coordToVirtualHelix[coord]
        except:
            return None
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def autoStaple(part):
        """Autostaple does the following:
        1. Clear existing staple strands by iterating over each strand
        and calling RemoveStrandCommand on each. The next strand to remove
        is always at index 0.
        2. Create temporary strands that span regions where scaffold is present.
        3. Determine where actual strands will go based on strand overlap with
        prexovers.
        4. Delete temporary strands and create new strands.
        """
        epDict = {}  # keyed on StrandSet
        cmds = []

        # clear existing staple strands
        # part.verifyOligos()

        for o in list(part.oligos()):
            if not o.isStaple():
                continue
            c = Oligo.RemoveOligoCommand(o)
            cmds.append(c)
        # end for
        util.execCommandList(part, cmds, desc="Clear staples")
        cmds = []

        # create strands that span all bases where scaffold is present
        for vh in part.getVirtualHelices():
            segments = []
            scafSS = vh.scaffoldStrandSet()
            for strand in scafSS:
                lo, hi = strand.idxs()
                if len(segments) == 0:
                    segments.append([lo, hi])  # insert 1st strand
                elif segments[-1][1] == lo - 1:
                    segments[-1][1] = hi  # extend
                else:
                    segments.append([lo, hi])  # insert another strand
            stapSS = vh.stapleStrandSet()
            epDict[stapSS] = []
            for i in range(len(segments)):
                lo, hi = segments[i]
                epDict[stapSS].extend(segments[i])
                c = StrandSet.CreateStrandCommand(stapSS, lo, hi, i)
                cmds.append(c)
        util.execCommandList(part, cmds, desc="Add tmp strands", useUndoStack=False)
        cmds = []

        # determine where xovers should be installed
        for vh in part.getVirtualHelices():
            stapSS = vh.stapleStrandSet()
            scafSS = vh.scaffoldStrandSet()
            is5to3 = stapSS.isDrawn5to3()
            potentialXovers = part.potentialCrossoverList(vh)
            for neighborVh, idx, strandType, isLowIdx in potentialXovers:
                if strandType != StrandType.Staple:
                    continue
                if isLowIdx and is5to3:
                    strand = stapSS.getStrand(idx)
                    neighborSS = neighborVh.stapleStrandSet()
                    nStrand = neighborSS.getStrand(idx)
                    if strand == None or nStrand == None:
                        continue
                    # check for bases on both strands at [idx-1:idx+3]
                    if not (strand.lowIdx() < idx and strand.highIdx() > idx + 1):
                        continue
                    if not (nStrand.lowIdx() < idx and nStrand.highIdx() > idx + 1):
                        continue

                    # check for nearby scaffold xovers
                    scafStrandL = scafSS.getStrand(idx-4)
                    scafStrandH = scafSS.getStrand(idx+5)
                    if scafStrandL:
                        if scafStrandL.hasXoverAt(idx-4):
                            continue
                    if scafStrandH:
                        if scafStrandH.hasXoverAt(idx+5):
                            continue

                    # disable edge xovers
                    scafStrandL1 = scafSS.getStrand(idx-1)
                    scafStrandM = scafSS.getStrand(idx)
                    scafStrandH1 = scafSS.getStrand(idx+1)
                    if scafStrandL1:
                        if scafStrandL1.hasXoverAt(idx-1) and not vh.hasStrandAtIdx(idx-2):
                            continue
                        if scafStrandL1.hasXoverAt(idx-2) and not vh.hasStrandAtIdx(idx-3):
                            continue
                    if scafStrandM:
                        if scafStrandM.hasXoverAt(idx-1) and not vh.hasStrandAtIdx(idx-2):
                            continue
                        if scafStrandM.hasXoverAt(idx+1) and not vh.hasStrandAtIdx(idx+2):
                            continue
                    if scafStrandH1:
                        if scafStrandH1.hasXoverAt(idx+1) and not vh.hasStrandAtIdx(idx+2):
                            continue
                        if scafStrandH1.hasXoverAt(idx+2) and not vh.hasStrandAtIdx(idx+3):
                            continue

                    # Finally, add the xovers to install
                    epDict[stapSS].extend([idx, idx+1])
                    epDict[neighborSS].extend([idx, idx+1])

        # clear temporary staple strands
        for vh in part.getVirtualHelices():
            stapSS = vh.stapleStrandSet()
            for strand in stapSS:
                c = StrandSet.RemoveStrandCommand(stapSS, strand, 0)
                cmds.append(c)
        util.execCommandList(part, cmds, desc="Rm tmp strands", useUndoStack=False)
        cmds = []

        util.beginSuperMacro(part, desc="Auto-Staple")

        for stapSS, epList in epDict.items():
            assert (len(epList) % 2 == 0)
            epList = sorted(epList)
            ssIdx = 0
            for i in range(0, len(epList),2):
                lo, hi = epList[i:i+2]
                c = StrandSet.CreateStrandCommand(stapSS, lo, hi, ssIdx)
                cmds.append(c)
                ssIdx += 1
        util.execCommandList(part, cmds, desc="Create strands")
        cmds = []

        # create crossovers wherever possible (from strand5p only)
        for vh in part.getVirtualHelices():
            stapSS = vh.stapleStrandSet()
            is5to3 = stapSS.isDrawn5to3()
            potentialXovers = part.potentialCrossoverList(vh)
            for neighborVh, idx, strandType, isLowIdx in potentialXovers:
                if strandType != StrandType.Staple:
                    continue
                if (isLowIdx and is5to3) or (not isLowIdx and not is5to3):
                    strand = stapSS.getStrand(idx)
                    neighborSS = neighborVh.stapleStrandSet()
                    nStrand = neighborSS.getStrand(idx)
                    if strand == None or nStrand == None:
                        continue
                    if idx in strand.idxs() and idx in nStrand.idxs():
                        # only install xovers on pre-split strands
                        part.createXover(strand, idx, nStrand, idx, updateOligo=False)

        c = Part.RefreshOligosCommand(part)
        cmds.append(c)
        util.execCommandList(part, cmds, desc="Assign oligos")

        cmds = []
        util.endSuperMacro(part)

    # end def

    def verifyOligoStrandCounts(self):
        total_stap_strands = 0
        stapOligos = set()
        total_stap_oligos = 0

        for vh in self.getVirtualHelices():
            stapSS = vh.stapleStrandSet()
            total_stap_strands += len(stapSS._strandList)
            for strand in stapSS:
                stapOligos.add(strand.oligo())
        # print "# stap oligos:", len(stapOligos), "# stap strands:", total_stap_strands


    def verifyOligos(self):
        total_errors = 0
        total_passed = 0

        for o in list(self.oligos()):
            oL = o.length()
            a = 0
            gen = o.strand5p().generator3pStrand()

            for s in gen:
                a += s.totalLength()
            # end for
            if oL != a:
                total_errors += 1
                # print "wtf", total_errors, "oligoL", oL, "strandsL", a, "isStaple?", o.isStaple()
                o.applyColor('#ff0000')
            else:
                total_passed += 1
        # end for
        # print "Total Passed: ", total_passed, "/", total_passed+total_errors
    # end def

    def removeVirtualHelices(self, useUndoStack=True):
        vhs = [vh for vh in self._coordToVirtualHelix.values()]
        for vh in vhs:
            vh.remove(useUndoStack)
        # end for
    # end def

    # def remove(self, useUndoStack=True):
    #     """
    #     This method uses the slow method of removing each element one at a time
    #     while maintaining state while the command is executed
    #     """
    #     self.partHideSignal.emit(self)
    #     self._activeVirtualHelix = None
    #     if useUndoStack:
    #         self.undoStack().beginMacro("Delete Part")
    #     self.removeVirtualHelices(useUndoStack)
    #     c = Part.RemovePartCommand(self)
    #     if useUndoStack:
    #         self.undoStack().push(c)
    #         self.undoStack().endMacro()
    #     else:
    #         c.redo()
    # # end def

    def remove(self, useUndoStack=True):
        """
        This method assumes all strands are and all VirtualHelices are
        going away, so it does not maintain a valid model state while
        the command is being executed.
        Everything just gets pushed onto the undostack more or less as is.
        Except that strandSets are actually cleared then restored, but this
        is neglible performance wise.  Also, decorators/insertions are assumed
        to be parented to strands in the view so their removal Signal is
        not emitted.  This causes problems with undo and redo down the road
        but works as of now.
        """
        self.partHideSignal.emit(self)
        self._activeVirtualHelix = None
        if useUndoStack:
            self.undoStack().beginMacro("Delete Part")
        # remove strands and oligos
        self.removeAllOligos(useUndoStack)
        # remove VHs
        vhs = list(self._coordToVirtualHelix.values())
        for vh in vhs:
            d = VirtualHelix.RemoveVirtualHelixCommand(self, vh)
            if useUndoStack:
                self.undoStack().push(d)
            else:
                d.redo()
        # end for
        # remove the part
        e = Part.RemovePartCommand(self)
        if useUndoStack:
            self.undoStack().push(e)
            self.undoStack().endMacro()
        else:
            e.redo()
    # end def
    
    def removeAllOligos(self, useUndoStack=True):
        # clear existing oligos
        cmds = []
        for o in list(self.oligos()):
            cmds.append(Oligo.RemoveOligoCommand(o))
        # end for
        util.execCommandList(self, cmds, desc="Clear oligos", useUndoStack=useUndoStack)
    # end def

    def addOligo(self, oligo):
        self._oligos.add(oligo)

    # end def

    def createVirtualHelix(self, row, col, useUndoStack=True):
        c = Part.CreateVirtualHelixCommand(self, row, col)
        util.execCommandList(self, [c], desc="Add VirtualHelix", \
                                                useUndoStack=useUndoStack)
    # end def

    def createXover(self, strand5p, idx5p, strand3p, idx3p, updateOligo=True, useUndoStack=True):
        # prexoveritem needs to store left or right, and determine
        # locally whether it is from or to
        # pass that info in here in and then do the breaks
        ss5p = strand5p.strandSet()
        ss3p = strand3p.strandSet()
        if ss5p.strandType() != ss3p.strandType():
            return
        if useUndoStack:
            self.undoStack().beginMacro("Create Xover")
        if ss5p.isScaffold() and useUndoStack:  # ignore on import
            strand5p.oligo().applySequence(None)
            strand3p.oligo().applySequence(None)
        if strand5p == strand3p:
            """
            This is a complicated case basically we need a truth table.
            1 strand becomes 1, 2 or 3 strands depending on where the xover is
            to.  1 and 2 strands happen when the xover is to 1 or more existing
            endpoints.  Since SplitCommand depends on a StrandSet index, we need
            to adjust this strandset index depending which direction the crossover is
            going in.

            Below describes the 3 strand process
            1) Lookup the strands strandset index (ssIdx)
            1) Split attempted on the 3 prime strand, AKA 5prime endpoint of
            one of the new strands.  We have now created 2 strands, and the ssIdx
            is either the same as the first lookup, or one more than it depending
            on which way the the strand is drawn (isDrawn5to3).  If a split occured
            the 5prime strand is definitely part of the 3prime strand created in this step
            2) Split is attempted on the resulting 2 strands.  There is
            now 3 strands, and the final 3 prime strand may be one of the two new strands
            created in this step. Check it.
            3) Create the Xover
            """
            c = None
            # lookup the initial strandset index
            found, overlap, ssIdx3p = ss3p._findIndexOfRangeFor(strand3p)
            if strand3p.idx5Prime() == idx3p:  # yes, idx already matches
                temp5 = xoStrand3 = strand3p
            else:
                offset3p = -1 if ss3p.isDrawn5to3() else 1
                if ss3p.strandCanBeSplit(strand3p, idx3p + offset3p):
                    c = ss3p.SplitCommand(strand3p, idx3p + offset3p, ssIdx3p)
                    # cmds.append(c)
                    xoStrand3 = c._strandHigh if ss3p.isDrawn5to3() else c._strandLow
                    # adjust the target 5prime strand, always necessary if a split happens here
                    if idx5p > idx3p and ss3p.isDrawn5to3():
                        temp5 = xoStrand3
                    elif idx5p < idx3p and not ss3p.isDrawn5to3():
                        temp5 = xoStrand3
                    else:
                        temp5 = c._strandLow if ss3p.isDrawn5to3() else c._strandHigh
                    if useUndoStack:
                        self.undoStack().push(c)
                    else:
                        c.redo()
                else:
                    if useUndoStack:
                        self.undoStack().endMacro()
                        # unclear the applied sequence
                        if self.undoStack().canUndo() and ss5p.isScaffold():
                            self.undoStack().undo()
                    return
                # end if
            if xoStrand3.idx3Prime() == idx5p:
                xoStrand5 = temp5
            else:
                ssIdx5p = ssIdx3p
                # if the strand was split for the strand3p, then we need to adjust the strandset index
                if c:
                    # the insertion index into the set is increases
                    if ss3p.isDrawn5to3():
                        ssIdx5p = ssIdx3p + 1 if idx5p > idx3p else ssIdx3p
                    else:
                        ssIdx5p = ssIdx3p + 1 if idx5p > idx3p else ssIdx3p
                if ss5p.strandCanBeSplit(temp5, idx5p):
                    d = ss5p.SplitCommand(temp5, idx5p, ssIdx5p)
                    # cmds.append(d)
                    xoStrand5 = d._strandLow if ss5p.isDrawn5to3() else d._strandHigh
                    if useUndoStack:
                        self.undoStack().push(d)
                    else:
                        d.redo()
                    # adjust the target 3prime strand, IF necessary
                    if idx5p > idx3p and ss3p.isDrawn5to3():
                        xoStrand3 = xoStrand5
                    elif idx5p < idx3p and not ss3p.isDrawn5to3():
                        xoStrand3 = xoStrand5
                else:
                    if useUndoStack:
                        self.undoStack().endMacro()
                        # unclear the applied sequence
                        if self.undoStack().canUndo() and ss5p.isScaffold():
                            self.undoStack().undo()
                    return
        # end if
        else:  # Do the following if it is in fact a different strand
            # is the 5' end ready for xover installation?
            if strand3p.idx5Prime() == idx3p:  # yes, idx already matches
                xoStrand3 = strand3p
            else:  # no, let's try to split
                offset3p = -1 if ss3p.isDrawn5to3() else 1
                if ss3p.strandCanBeSplit(strand3p, idx3p + offset3p):
                    found, overlap, ssIdx = ss3p._findIndexOfRangeFor(strand3p)
                    if found:
                        c = ss3p.SplitCommand(strand3p, idx3p + offset3p, ssIdx)
                        # cmds.append(c)
                        xoStrand3 = c._strandHigh if ss3p.isDrawn5to3() else c._strandLow
                        if useUndoStack:
                            self.undoStack().push(c)
                        else:
                            c.redo()
                else:  # can't split... abort
                    if useUndoStack:
                        self.undoStack().endMacro()
                        # unclear the applied sequence
                        if self.undoStack().canUndo() and ss5p.isScaffold():
                            self.undoStack().undo()
                    return

            # is the 3' end ready for xover installation?
            if strand5p.idx3Prime() == idx5p:  # yes, idx already matches
                xoStrand5 = strand5p
            else:
                if ss5p.strandCanBeSplit(strand5p, idx5p):
                    found, overlap, ssIdx = ss5p._findIndexOfRangeFor(strand5p)
                    if found:
                        d = ss5p.SplitCommand(strand5p, idx5p, ssIdx)
                        # cmds.append(d)
                        xoStrand5 = d._strandLow if ss5p.isDrawn5to3() else d._strandHigh
                        if useUndoStack:
                            self.undoStack().push(d)
                        else:
                            d.redo()
                else:  # can't split... abort
                    if useUndoStack:
                        self.undoStack().endMacro()
                        # unclear the applied sequence
                        if self.undoStack().canUndo() and ss5p.isScaffold():
                            self.undoStack().undo()
                    return
        # end else

        e = Part.CreateXoverCommand(self, xoStrand5, idx5p, xoStrand3, idx3p, updateOligo=updateOligo)
        if useUndoStack:
            self.undoStack().push(e)
            self.undoStack().endMacro()
        else:
            e.redo()

    # end def

    def removeXover(self, strand5p, strand3p, useUndoStack=True):
        cmds = []
        if strand5p.connection3p() == strand3p:
            c = Part.RemoveXoverCommand(self, strand5p, strand3p)
            cmds.append(c)
            util.execCommandList(self, cmds, desc="Remove Xover", \
                                                    useUndoStack=useUndoStack)
    # end def

    def destroy(self):
        self.setParent(None)
        self.deleteLater()  # QObject also emits a destroyed() Signal
    # end def

    def generatorFullLattice(self):
        """
        Returns a generator that yields the row, column lattice points to draw
        relative to the part origin.
        """
        return product(list(range(self._maxRow)), list(range(self._maxCol)))
    # end def

    def generatorSpatialLattice(self, scaleFactor=1.0):
        """
        Returns a generator that yields the XY spatial lattice points to draw
        relative to the part origin.
        """
        # nested for loop in one line
        latticeCoordToPositionXY = self.latticeCoordToPositionXY
        for latticeCoord in product(list(range(self._maxRow)), list(range(self._maxCol))):
            row, col = latticeCoord
            x, y = latticeCoordToPositionXY(row, col, scaleFactor)
            yield x, y, row, col
    # end def

    def getPreXoversHigh(self, strandType, neighborType, minIdx=0, maxIdx=None):
        """
        Returns all prexover positions for neighborType that are below
        maxIdx. Used in emptyhelixitem.py.
        """
        preXO = self._scafH if strandType == StrandType.Scaffold else self._stapH
        if maxIdx == None:
            maxIdx = self._maxBase
        steps = (self._maxBase // self._step) + 1
        ret = [i * self._step + j for i in range(steps) for j in preXO[neighborType]]
        return [x for x in ret if x >= minIdx and x <= maxIdx]

    def getPreXoversLow(self, strandType, neighborType, minIdx=0, maxIdx=None):
        """
        Returns all prexover positions for neighborType that are above
        minIdx. Used in emptyhelixitem.py.
        """
        preXO = self._scafL if strandType == StrandType.Scaffold \
                                else self._stapL
        if maxIdx == None:
            maxIdx = self._maxBase
        steps = (self._maxBase // self._step) + 1
        ret = [i * self._step + j for i in range(steps) for j in preXO[neighborType]]
        return [x for x in ret if x >= minIdx and x <= maxIdx]

    def latticeCoordToPositionXY(self, row, col, scaleFactor=1.0):
        """
        Returns a tuple of the (x,y) position for a given lattice row and
        column.

        Note: The x,y position is the upperLeftCorner for the given
        coordinate, and relative to the part instance.
        """
        raise NotImplementedError  # To be implemented by Part subclass
    # end def

    def positionToCoord(self, x, y, scaleFactor=1.0):
        """
        Returns a tuple (row, column) lattice coordinate for a given
        x and y position that is within +/- 0.5 of a true valid lattice
        position.

        Note: mapping should account for int-to-float rounding errors.
        x,y is relative to the Part Instance Position.
        """
        raise NotImplementedError  # To be implemented by Part subclass
    # end def

    def newPart(self):
        return Part(self._document)
    # end def

    def removeOligo(self, oligo):
        # Not a designated method
        # (there exist methods that also directly
        # remove parts from self._oligos)
        try:
            self._oligos.remove(oligo)
        except KeyError:
            print(util.trace(5))
            # print "error removing oligo", oligo
    # end def

    def renumber(self, coordList, useUndoStack=True):
        if useUndoStack:
            self.undoStack().beginMacro("Renumber VirtualHelices")
        c = Part.RenumberVirtualHelicesCommand(self, coordList)
        if useUndoStack:
            self.undoStack().push(c)
            self.undoStack().endMacro()
        else:
            c.redo()
    # end def
    
    class RenumberVirtualHelicesCommand(QUndoCommand):
        """
        """
        def __init__(self, part, coordList):
            super(Part.RenumberVirtualHelicesCommand, self).__init__()
            self._part = part
            self._vhs = [part.virtualHelixAtCoord(coord) for coord in coordList]
            self._oldNumbers = [vh.number() for vh in self._vhs]
        # end def
            
        def redo(self):
            even = 0
            odd = 1
            for vh in self._vhs:
                if vh.isEvenParity():
                    vh.setNumber(even)
                    even += 2
                else:
                    vh.setNumber(odd)
                    odd += 2
            # end for
            part = self._part
            aVH =  part.activeVirtualHelix()
            if aVH:
                part.partStrandChangedSignal.emit(part, aVH)
            for oligo in part._oligos:
                for strand in oligo.strand5p().generator3pStrand():
                    strand.strandUpdateSignal.emit(strand)
        # end def
            
        def undo(self):
            for vh, num in zip(self._vhs, self._oldNumbers):
                vh.setNumber(num)
            # end for
            part = self._part
            aVH =  part.activeVirtualHelix()
            if aVH:
                part.partStrandChangedSignal.emit(part, aVH)
            for oligo in part._oligos:
                for strand in oligo.strand5p().generator3pStrand():
                    strand.strandUpdateSignal.emit(strand)
        # end def
    # end def

    def resizeLattice(self):
        """docstring for resizeLattice"""
        pass
    # end def

    def resizeVirtualHelices(self, minDelta, maxDelta, useUndoStack=True):
        """docstring for resizeVirtualHelices"""
        c = Part.ResizePartCommand(self, minDelta, maxDelta)
        util.execCommandList(self, [c], desc="Resize part", \
                                                    useUndoStack=useUndoStack)
    # end def

    def setActiveBaseIndex(self, idx):
        self._activeBaseIndex = idx
        self.partActiveSliceIndexSignal.emit(self, idx)
    # end def

    def setActiveVirtualHelix(self, virtualHelix, idx=None):
        self._activeVirtualHelix = virtualHelix
        self._activeVirtualHelixIdx = idx
        self.partStrandChangedSignal.emit(self, virtualHelix)
    # end def

    def selectPreDecorator(self, selectionList):
        """
        Handles view notifications that a predecorator has been selected.
        """
        if (len(selectionList) == 0):
            return
            # print "all PreDecorators were unselected"
            # partPreDecoratorUnSelectedSignal.emit()
        sel = selectionList[0]
        (row, col, baseIdx) = (sel[0], sel[1], sel[2])
        self.partPreDecoratorSelectedSignal.emit(self, row, col, baseIdx)

    def xoverSnapTo(self, strand, idx, delta):
        """
        Returns the nearest xover position to allow snap-to behavior in
        resizing strands via dragging selected xovers.
        """
        strandType = strand.strandType()
        if delta > 0:
            minIdx, maxIdx = idx - delta, idx + delta
        else:
            minIdx, maxIdx = idx + delta, idx - delta

        # determine neighbor strand and bind the appropriate prexover method
        lo, hi = strand.idxs()
        if idx == lo:
            connectedStrand = strand.connectionLow()
            preXovers = self.getPreXoversHigh
        else:
            connectedStrand = strand.connectionHigh()
            preXovers = self.getPreXoversLow
        connectedVh = connectedStrand.virtualHelix()

        # determine neighbor position, if any
        neighbors = self.getVirtualHelixNeighbors(strand.virtualHelix())
        if connectedVh in neighbors:
            neighborIdx = neighbors.index(connectedVh)
            try:
                newIdx = util.nearest(idx + delta,
                                    preXovers(strandType,
                                                neighborIdx,
                                                minIdx=minIdx,
                                                maxIdx=maxIdx)
                                    )
                return newIdx
            except ValueError:
                return None  # nearest not found in the expanded list
        else:  # no neighbor (forced xover?)... don't snap, just return
            return idx + delta

    ### PRIVATE SUPPORT METHODS ###
    def _addVirtualHelix(self, virtualHelix):
        """
        private method for adding a virtualHelix to the Parts data structure
        of virtualHelix references
        """
        self._coordToVirtualHelix[virtualHelix.coord()] = virtualHelix
    # end def

    def _removeVirtualHelix(self, virtualHelix):
        """
        private method for adding a virtualHelix to the Parts data structure
        of virtualHelix references
        """
        del self._coordToVirtualHelix[virtualHelix.coord()]
    # end def

    def _reserveHelixIDNumber(self, parityEven=True, requestedIDnum=None):
        """
        Reserves and returns a unique numerical label appropriate for a
        virtualhelix of a given parity. If a specific index is preferable
        (say, for undo/redo) it can be requested in num.
        """
        num = requestedIDnum
        if num != None:  # We are handling a request for a particular number
            assert num >= 0, int(num) == num
            # assert not num in self._numberToVirtualHelix
            if num in self.oddRecycleBin:
                self.oddRecycleBin.remove(num)
                heapify(self.oddRecycleBin)
                return num
            if num in self.evenRecycleBin:
                self.evenRecycleBin.remove(num)
                heapify(self.evenRecycleBin)
                return num
            self.reserveBin.add(num)
            return num
        # end if
        else:
            # Just find any valid index (subject to parity constraints)
            if parityEven:
                if len(self.evenRecycleBin):
                    return heappop(self.evenRecycleBin)
                else:
                    while self._highestUsedEven + 2 in self.reserveBin:
                        self._highestUsedEven += 2
                    self._highestUsedEven += 2
                    return self._highestUsedEven
            else:
                if len(self.oddRecycleBin):
                    return heappop(self.oddRecycleBin)
                else:
                    # use self._highestUsedOdd iff the recycle bin is empty
                    # and highestUsedOdd+2 is not in the reserve bin
                    while self._highestUsedOdd + 2 in self.reserveBin:
                        self._highestUsedOdd += 2
                    self._highestUsedOdd += 2
                    return self._highestUsedOdd
        # end else
    # end def

    def _recycleHelixIDNumber(self, n):
        """
        The caller's contract is to ensure that n is not used in *any* helix
        at the time of the calling of this function (or afterwards, unless
        reserveLabelForHelix returns the label again).
        """
        if n % 2 == 0:
            heappush(self.evenRecycleBin, n)
        else:
            heappush(self.oddRecycleBin, n)
    # end def

    def _splitBeforeAutoXovers(self, vh5p, vh3p, idx, useUndoStack=True):
        # prexoveritem needs to store left or right, and determine
        # locally whether it is from or to
        # pass that info in here in and then do the breaks
        ss5p = strand5p.strandSet()
        ss3p = strand3p.strandSet()
        cmds = []

        # is the 5' end ready for xover installation?
        if strand3p.idx5Prime() == idx5p:  # yes, idx already matches
            xoStrand3 = strand3p
        else:  # no, let's try to split
            offset3p = -1 if ss3p.isDrawn5to3() else 1
            if ss3p.strandCanBeSplit(strand3p, idx3p + offset3p):
                found, overlap, ssIdx = ss3p._findIndexOfRangeFor(strand3p)
                if found:
                    c = ss3p.SplitCommand(strand3p, idx3p + offset3p, ssIdx)
                    cmds.append(c)
                    xoStrand3 = c._strandHigh if ss3p.isDrawn5to3() else c._strandLow
            else:  # can't split... abort
                return

        # is the 3' end ready for xover installation?
        if strand5p.idx3Prime() == idx5p:  # yes, idx already matches
            xoStrand5 = strand5p
        else:
            if ss5p.strandCanBeSplit(strand5p, idx5p):
                found, overlap, ssIdx = ss5p._findIndexOfRangeFor(strand5p)
                if found:
                    d = ss5p.SplitCommand(strand5p, idx5p, ssIdx)
                    cmds.append(d)
                    xoStrand5 = d._strandLow if ss5p.isDrawn5to3() \
                                                else d._strandHigh
            else:  # can't split... abort
                return
        c = Part.CreateXoverCommand(self, xoStrand5, idx5p, xoStrand3, idx3p)
        cmds.append(c)
        util.execCommandList(self, cmds, desc="Create Xover", \
                                                useUndoStack=useUndoStack)
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def shallowCopy(self):
        part = self.newPart()
        part._virtualHelices = dict(self._virtualHelices)
        part._oligos = set(self._oligos)
        part._maxBase = self._maxBase
        return part
    # end def

    def deepCopy(self):
        """
        1) Create a new part
        2) copy the VirtualHelices
        3) Now you need to map the ORIGINALs Oligos onto the COPY's Oligos
        To do this you can for each Oligo in the ORIGINAL
            a) get the strand5p() of the ORIGINAL
            b) get the corresponding strand5p() in the COPY based on
                i) lookup the hash idNum of the ORIGINAL strand5p() VirtualHelix
                ii) get the StrandSet() that you created in Step 2 for the
                StrandType of the original using the hash idNum
        """
        # 1) new part
        part = self.newPart()
        for key, vhelix in self._virtualHelices:
            # 2) Copy VirtualHelix
            part._virtualHelices[key] = vhelix.deepCopy(part)
        # end for
        # 3) Copy oligos
        for oligo, val in self._oligos:
            strandGenerator = oligo.strand5p().generator3pStrand()
            strandType = oligo.strand5p().strandType()
            newOligo = oligo.deepCopy(part)
            lastStrand = None
            for strand in strandGenerator:
                idNum = strand.virtualHelix().number()
                newVHelix = part._virtualHelices[idNum]
                newStrandSet = newVHelix().getStrandSetByType(strandType)
                newStrand = strand.deepCopy(newStrandSet, newOligo)
                if lastStrand:
                    lastStrand.setConnection3p(newStrand)
                else:
                    # set the first condition
                    newOligo.setStrand5p(newStrand)
                newStrand.setConnection5p(lastStrand)
                newStrandSet.addStrand(newStrand)
                lastStrand = newStrand
            # end for
            # check loop condition
            if oligo.isLoop():
                s5p = newOligo.strand5p()
                lastStrand.set3pconnection(s5p)
                s5p.set5pconnection(lastStrand)
            # add to part
            oligo.add()
        # end for
        return part
    # end def

    def areSameOrNeighbors(self, virtualHelixA, virtualHelixB):
        """
        returns True or False
        """
        return virtualHelixB in self.getVirtualHelixNeighbors(virtualHelixA) or \
            virtualHelixA == virtualHelixB
    # end def

    def potentialCrossoverList(self, virtualHelix, idx=None):
        """
        Returns a list of tuples
            (neighborVirtualHelix, index, strandType, isLowIdx)

        where:

        neighborVirtualHelix is a virtualHelix neighbor of the arg virtualHelix
        index is the index where a potential Xover might occur
        strandType is from the enum (StrandType.Scaffold, StrandType.Staple)
        isLowIdx is whether or not it's the at the low index (left in the Path
        view) of a potential Xover site
        """
        vh = virtualHelix
        ret = []  # LUT = Look Up Table
        part = self
        # these are the list of crossover points simplified
        # they depend on whether the strandType is scaffold or staple
        # create a list of crossover points for each neighbor of the form
        # [(_scafL[i], _scafH[i], _stapL[i], _stapH[i]), ...]
        lutsNeighbor = list(
                            zip(
                                part._scafL,
                                part._scafH,
                                part._stapL,
                                part._stapH
                                )
                            )

        sTs = (StrandType.Scaffold, StrandType.Staple)
        numBases = part.maxBaseIdx()

        # create a range for the helical length dimension of the Part,
        # incrementing by the lattice step size.
        baseRange = list(range(0, numBases, part._step))

        if idx != None:
            baseRange = [x for x in baseRange if x >= idx - 3 * part._step and \
                                        x <= idx + 2 * part._step]

        if vh is None:
            return

        fromStrandSets = vh.getStrandSets()
        neighbors = self.getVirtualHelixNeighbors(vh)

        # print neighbors, lutsNeighbor
        for neighbor, lut in zip(neighbors, lutsNeighbor):
            if not neighbor:
                continue

            # now arrange again for iteration
            # (_scafL[i], _scafH[i]), (_stapL[i], _stapH[i]) )
            # so we can pair by StrandType
            lutScaf = lut[0:2]
            lutStap = lut[2:4]
            lut = (lutScaf, lutStap)

            toStrandSets = neighbor.getStrandSets()
            for fromSS, toSS, pts, st in zip(fromStrandSets, toStrandSets, lut, sTs):
                # test each period of each lattice for each StrandType
                for pt, isLowIdx in zip(pts, (True, False)):
                    for i, j in product(baseRange, pt):
                        index = i + j
                        if index < numBases:
                            if fromSS.hasNoStrandAtOrNoXover(index) and \
                                    toSS.hasNoStrandAtOrNoXover(index):
                                ret.append((neighbor, index, st, isLowIdx))
                            # end if
                        # end if
                    # end for
                # end for
            # end for
        # end for
        return ret
    # end def

    def possibleXoverAt(self, fromVirtualHelix, toVirtualHelix, strandType, idx):
        fromSS = fromVirtualHelix.getStrandSetByType(strandType)
        toSS = toVirtualHelix.getStrandSetByType(strandType)
        return fromSS.hasStrandAtAndNoXover(idx) and \
                toSS.hasStrandAtAndNoXover(idx)
    # end def

    def setImportedVHelixOrder(self, orderedCoordList):
        """Used on file import to store the order of the virtual helices."""
        self._importedVHelixOrder = orderedCoordList
        self.partVirtualHelicesReorderedSignal.emit(self, orderedCoordList)

    ### COMMANDS ###
    class CreateVirtualHelixCommand(QUndoCommand):
        def __init__(self, part, row, col):
            super(Part.CreateVirtualHelixCommand, self).__init__()
            self._part = part
            self._parityEven = part.isEvenParity(row, col)
            idNum = part._reserveHelixIDNumber(self._parityEven,
                                                requestedIDnum=None)
            self._vhelix = VirtualHelix(part, row, col, idNum)
            self._idNum = idNum
        # end def

        def redo(self):
            vh = self._vhelix
            part = self._part
            idNum = self._idNum
            vh.setPart(part)
            part._addVirtualHelix(vh)
            vh.setNumber(idNum)
            if not vh.number():
                part._reserveHelixIDNumber(self._parityEven,
                                            requestedIDnum=idNum)
            # end if
            part.partVirtualHelixAddedSignal.emit(part, vh)
            part.partActiveSliceResizeSignal.emit(part)
        # end def

        def undo(self):
            vh = self._vhelix
            part = self._part
            idNum = self._idNum
            part._removeVirtualHelix(vh)
            part._recycleHelixIDNumber(idNum)
            # clear out part references
            vh.setNumber(None)  # must come before setPart(None)
            vh.setPart(None)
            vh.virtualHelixRemovedSignal.emit(vh)
            part.partActiveSliceResizeSignal.emit(part)
        # end def
    # end class

    class CreateXoverCommand(QUndoCommand):
        """
        Creates a Xover from the 3' end of strand5p to the 5' end of strand3p
        this needs to
        1. preserve the old oligo of strand3p
        2. install the crossover
        3. apply the strand5p oligo to the strand3p
        """
        def __init__(self, part, strand5p, strand5pIdx, strand3p, strand3pIdx, updateOligo=True):
            super(Part.CreateXoverCommand, self).__init__()
            self._part = part
            self._strand5p = strand5p
            self._strand5pIdx = strand5pIdx
            self._strand3p = strand3p
            self._strand3pIdx = strand3pIdx
            self._oldOligo3p = strand3p.oligo()
            self._updateOligo = updateOligo
        # end def

        def redo(self):
            part = self._part
            strand5p = self._strand5p
            strand5pIdx = self._strand5pIdx
            strand3p = self._strand3p
            strand3pIdx = self._strand3pIdx
            olg5p = strand5p.oligo()
            oldOlg3p = self._oldOligo3p

            # 0. Deselect the involved strands
            doc = strand5p.document()
            doc.removeStrandFromSelection(strand5p)
            doc.removeStrandFromSelection(strand3p)

            if self._updateOligo:
                # Test for Loopiness
                if olg5p == strand3p.oligo():
                    olg5p.setLoop(True)
                else:
                    # 1. update preserved oligo length
                    olg5p.incrementLength(oldOlg3p.length())
                    # 2. Remove the old oligo and apply the 5' oligo to the 3' strand
                    oldOlg3p.removeFromPart()
                    for strand in strand3p.generator3pStrand():
                        # emits strandHasNewOligoSignal
                        Strand.setOligo(strand, olg5p)

            # 3. install the Xover
            strand5p.setConnection3p(strand3p)
            strand3p.setConnection5p(strand5p)

            ss5 = strand5p.strandSet()
            vh5p = ss5.virtualHelix()
            st5p = ss5.strandType()
            ss3 = strand3p.strandSet()
            vh3p = ss3.virtualHelix()
            st3p = ss3.strandType()

            part.partActiveVirtualHelixChangedSignal.emit(part, vh5p)
            # strand5p.strandXover5pChangedSignal.emit(strand5p, strand3p)
            if self._updateOligo:
                strand5p.strandUpdateSignal.emit(strand5p)
                strand3p.strandUpdateSignal.emit(strand3p)
        # end def

        def undo(self):
            part = self._part
            strand5p = self._strand5p
            strand5pIdx = self._strand5pIdx
            strand3p = self._strand3p
            strand3pIdx = self._strand3pIdx
            oldOlg3p = self._oldOligo3p
            olg5p = strand5p.oligo()

            # 0. Deselect the involved strands
            doc = strand5p.document()
            doc.removeStrandFromSelection(strand5p)
            doc.removeStrandFromSelection(strand3p)

            # 1. uninstall the Xover
            strand5p.setConnection3p(None)
            strand3p.setConnection5p(None)

            if self._updateOligo:
                # Test Loopiness
                if oldOlg3p.isLoop():
                    oldOlg3p.setLoop(False)
                else:
                    # 2. restore the modified oligo length
                    olg5p.decrementLength(oldOlg3p.length())
                    # 3. apply the old oligo to strand3p
                    oldOlg3p.addToPart(part)
                    for strand in strand3p.generator3pStrand():
                        # emits strandHasNewOligoSignal
                        Strand.setOligo(strand, oldOlg3p)

            ss5 = strand5p.strandSet()
            vh5p = ss5.virtualHelix()
            st5p = ss5.strandType()
            ss3 = strand3p.strandSet()
            vh3p = ss3.virtualHelix()
            st3p = ss3.strandType()

            part.partActiveVirtualHelixChangedSignal.emit(part, vh5p)
            # strand5p.strandXover5pChangedSignal.emit(strand5p, strand3p)
            if self._updateOligo:
                strand5p.strandUpdateSignal.emit(strand5p)
                strand3p.strandUpdateSignal.emit(strand3p)
        # end def
    # end class

    class RefreshOligosCommand(QUndoCommand):
        """
        RefreshOligosCommand is a post-processing step for AutoStaple.

        Normally when an xover is created, all strands in the 3' direction are
        assigned the oligo of the 5' strand. This becomes very expensive
        during autoStaple, because the Nth xover requires updating up to N-1
        strands.

        Hence, we disable oligo assignment during the xover creation step,
        and then do it all in one pass at the end with this command.
        """
        def __init__(self, part):
            super(Part.RefreshOligosCommand, self).__init__()
            self._part = part
        # end def

        def redo(self):
            visited = {}
            for vh in self._part.getVirtualHelices():
                stapSS = vh.stapleStrandSet()
                for strand in stapSS:
                    visited[strand] = False

            for strand in list(visited.keys()):
                if visited[strand]:
                    continue
                visited[strand] = True
                startOligo = strand.oligo()
                strand5gen = strand.generator5pStrand()
                # this gets the oligo and burns a strand in the generator
                strand5 = next(strand5gen)
                for strand5 in strand5gen:
                    oligo5 = strand5.oligo()
                    if oligo5 != startOligo:
                        oligo5.removeFromPart()
                        Strand.setOligo(strand5, startOligo)  # emits strandHasNewOligoSignal
                    visited[strand5] = True
                # end for
                startOligo.setStrand5p(strand5)
                # is it a loop?
                if strand.connection3p() == strand5:
                    startOligo.setLoop(True)
                else:
                    strand3gen = strand.generator3pStrand()
                    strand3 = next(strand3gen)   # burn one
                    for strand3 in strand3gen:
                        oligo3 = strand3.oligo()
                        if oligo3 != startOligo:
                            oligo3.removeFromPart()
                            Strand.setOligo(strand3, startOligo)  # emits strandHasNewOligoSignal
                        visited[strand3] = True
                    # end for
                startOligo.refreshLength()
            # end for

            oligoSet = set()
            for strand in list(visited.keys()):
                oligoSet.add(strand.oligo())
                strand.strandUpdateSignal.emit(strand)
        # end def

        def undo(self):
            """Doesn't reassign """
            pass
        # end def
    # end class

    class RemoveXoverCommand(QUndoCommand):
        """
        Removes a Xover from the 3' end of strand5p to the 5' end of strand3p
        this needs to
        1. preserve the old oligo of strand3p
        2. install the crossover
        3. update the oligo length
        4. apply the new strand3p oligo to the strand3p
        """
        def __init__(self, part, strand5p, strand3p):
            super(Part.RemoveXoverCommand, self).__init__()
            self._part = part
            self._strand5p = strand5p
            self._strand5pIdx = strand5p.idx3Prime()
            self._strand3p = strand3p
            self._strand3pIdx = strand3p.idx5Prime()
            nO3p = self._newOligo3p = strand3p.oligo().shallowCopy()
            colorList = styles.stapColors if strand5p.strandSet().isStaple() \
                                            else styles.scafColors
            nO3p.setColor(random.choice(colorList).name())
            nO3p.setLength(0)
            for strand in strand3p.generator3pStrand():
                nO3p.incrementLength(strand.totalLength())
            # end def
            nO3p.setStrand5p(strand3p)
            
            self._isLoop = strand3p.oligo().isLoop()
        # end def

        def redo(self):
            part = self._part
            strand5p = self._strand5p
            strand5pIdx = self._strand5pIdx
            strand3p = self._strand3p
            strand3pIdx = self._strand3pIdx
            newOlg3p = self._newOligo3p
            olg5p = self._strand5p.oligo()

            # 0. Deselect the involved strands
            doc = strand5p.document()
            doc.removeStrandFromSelection(strand5p)
            doc.removeStrandFromSelection(strand3p)

            # 1. uninstall the Xover
            strand5p.setConnection3p(None)
            strand3p.setConnection5p(None)

            if self._isLoop:
                olg5p.setLoop(False)
                olg5p.setStrand5p(strand3p)
            else:
                # 2. restore the modified oligo length
                olg5p.decrementLength(newOlg3p.length())
                # 3. apply the old oligo to strand3p
                newOlg3p.addToPart(part)
                for strand in strand3p.generator3pStrand():
                    # emits strandHasNewOligoSignal
                    Strand.setOligo(strand, newOlg3p)

            ss5 = strand5p.strandSet()
            vh5p = ss5.virtualHelix()
            st5p = ss5.strandType()
            ss3 = strand3p.strandSet()
            vh3p = ss3.virtualHelix()
            st3p = ss3.strandType()

            part.partActiveVirtualHelixChangedSignal.emit(part, vh5p)
            # strand5p.strandXover5pChangedSignal.emit(strand5p, strand3p)
            strand5p.strandUpdateSignal.emit(strand5p)
            strand3p.strandUpdateSignal.emit(strand3p)
        # end def

        def undo(self):
            part = self._part
            strand5p = self._strand5p
            strand5pIdx = self._strand5pIdx
            strand3p = self._strand3p
            strand3pIdx = self._strand3pIdx
            olg5p = strand5p.oligo()
            newOlg3p = self._newOligo3p

            # 0. Deselect the involved strands
            doc = strand5p.document()
            doc.removeStrandFromSelection(strand5p)
            doc.removeStrandFromSelection(strand3p)

            if self._isLoop:
                olg5p.setLoop(True)
                # No need to restore whatever the old Oligo._strand5p was
            else:
                # 1. update preserved oligo length
                olg5p.incrementLength(newOlg3p.length())
                # 2. Remove the old oligo and apply the 5' oligo to the 3' strand
                newOlg3p.removeFromPart()
                for strand in strand3p.generator3pStrand():
                    # emits strandHasNewOligoSignal
                    Strand.setOligo(strand, olg5p)
            # end else

            # 3. install the Xover
            strand5p.setConnection3p(strand3p)
            strand3p.setConnection5p(strand5p)

            ss5 = strand5p.strandSet()
            vh5p = ss5.virtualHelix()
            st5p = ss5.strandType()
            ss3 = strand3p.strandSet()
            vh3p = ss3.virtualHelix()
            st3p = ss3.strandType()

            part.partActiveVirtualHelixChangedSignal.emit(part, vh5p)
            # strand5p.strandXover5pChangedSignal.emit(strand5p, strand3p)
            strand5p.strandUpdateSignal.emit(strand5p)
            strand3p.strandUpdateSignal.emit(strand3p)
        # end def
    # end class

    class RemovePartCommand(QUndoCommand):
        """
        RemovePartCommand deletes a part. Emits partRemovedSignal.
        """
        def __init__(self, part):
            super(Part.RemovePartCommand, self).__init__()
            self._part = part
            self._doc = part.document()
        # end def

        def redo(self):
            # Remove the strand
            part = self._part
            doc = self._doc
            doc.removePart(part)
            part.setDocument(None)
            part.partRemovedSignal.emit(part)
        # end def

        def undo(self):
            part = self._part
            doc = self._doc
            doc._addPart(part)
            part.setDocument(doc)
            doc.documentPartAddedSignal.emit(doc, part)
        # end def
    # end class

    class RemoveAllStrandsCommand(QUndoCommand):
        """
        1. Remove all strands. Emits strandRemovedSignal for each.
        2. Remove all oligos. 
        """
        def __init__(self, part):
            super(Part.RemoveAllStrandsCommand, self).__init__()
            self._part = part
            self._vhs = vhs = part.getVirtualHelices()
            self._strandSets = []
            for vh in self._vhs:
                x = vh.getStrandSets()
                self._strandSets.append(x[0])
                self._strandSets.append(x[1])
            self._strandSetListCopies = \
                        [[y for y in x._strandList] for x in self._strandSets]
            self._oligos = set(part.oligos())
        # end def

        def redo(self):
            part = self._part
            # Remove the strand
            for sSet in self._strandSets:
                sList = sSet._strandList
                for strand in sList:
                    sSet.removeStrand(strand)
                # end for
                sSet._strandList = []
            #end for
            for vh in self._vhs:
                # for updating the Slice View displayed helices
                part.partStrandChangedSignal.emit(part, vh)
            # end for
            self._oligos.clear()
        # end def

        def undo(self):
            part = self._part
            # Remove the strand
            sListCopyIterator = iter(self._strandSetListCopies)
            for sSet in self._strandSets:
                sList = next(sListCopyIterator)
                for strand in sList:
                    sSet.strandsetStrandAddedSignal.emit(sSet, strand)
                # end for
                sSet._strandList = sList
            #end for
            for vh in self._vhs:
                # for updating the Slice View displayed helices
                part.partStrandChangedSignal.emit(part, vh)
            # end for
            for olg in self._oligos:
                part.addOligo(olg)
        # end def
    # end class

    class ResizePartCommand(QUndoCommand):
        """
        set the maximum and mininum base index in the helical direction

        need to adjust all subelements in the event of a change in the
        minimum index
        """
        def __init__(self, part, minHelixDelta, maxHelixDelta):
            super(Part.ResizePartCommand, self).__init__()
            self._part = part
            self._minDelta = minHelixDelta
            self._maxDelta = maxHelixDelta
            self._oldActiveIdx = part.activeBaseIndex()
        # end def

        def redo(self):
            part = self._part
            part._minBase += self._minDelta
            part._maxBase += self._maxDelta
            if self._minDelta != 0:
                self.deltaMinDimension(part, self._minDelta)
            for vh in part._coordToVirtualHelix.values():
                part.partVirtualHelixResizedSignal.emit(part, vh.coord())
            if self._oldActiveIdx > part._maxBase:
                part.setActiveBaseIndex(part._maxBase)
            part.partDimensionsChangedSignal.emit(part)
        # end def

        def undo(self):
            part = self._part
            part._minBase -= self._minDelta
            part._maxBase -= self._maxDelta
            if self._minDelta != 0:
                self.deltaMinDimension(part, self._minDelta)
            for vh in part._coordToVirtualHelix.values():
                part.partVirtualHelixResizedSignal.emit(part, vh.coord())
            if self._oldActiveIdx != part.activeBaseIndex():
                part.setActiveBaseIndex(self._oldActiveIdx)
            part.partDimensionsChangedSignal.emit(part)
        # end def

        def deltaMinDimension(self, part, minDimensionDelta):
            """
            Need to update:
            strands
            insertions
            """
            for vhDict in part._insertions.values():
                for insertion in vhDict:
                    insertion.updateIdx(minDimensionDelta)
                # end for
            # end for
            for vh in part._coordToVirtualHelix.values():
                for strand in vh.scaffoldStrand().generatorStrand():
                    strand.updateIdxs(minDimensionDelta)
                for strand in vh.stapleStrand().generatorStrand():
                    strand.updateIdxs(minDimensionDelta)
            # end for
        # end def
    # end class
# end class
