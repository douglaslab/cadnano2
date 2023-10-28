import random
from operator import itemgetter
from itertools import repeat

from .strand import Strand
from .oligo import Oligo
from .enum import StrandType
from cadnano2.views import styles

import cadnano2.util as util
# import cadnano2.util as util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QUndoStack', 'QUndoCommand'])


class StrandSet(QObject):
    """
    StrandSet is a container class for Strands, and provides the several
    publicly accessible methods for editing strands, including operations
    for creation, destruction, resizing, splitting, and merging strands.

    Views may also query StrandSet for information that is useful in
    determining if edits can be made, such as the bounds of empty space in
    which a strand can be created or resized.
    """
    def __init__(self, strandType, virtualHelix):
        super(StrandSet, self).__init__(virtualHelix)
        self._virtualHelix = virtualHelix
        self._doc = virtualHelix.document()
        self._strandList = []
        self._undoStack = None
        self._lastStrandSetIndex = None
        self._strandType = strandType
    # end def

    def __iter__(self):
        """Iterate over each strand in the strands list."""
        return self._strandList.__iter__()
    # end def

    def __repr__(self):
        if self._strandType == 0:
            type = 'scaf'
        else:
            type = 'stap'
        num = self._virtualHelix.number()
        return "<%s_StrandSet(%d)>" % (type, num)
    # end def

    ### SIGNALS ###
    strandsetStrandAddedSignal = pyqtSignal(QObject, QObject)  # strandset, strand

    ### SLOTS ###

    ### ACCESSORS ###
    def part(self):
        return self._virtualHelix.part()
    # end def

    def document(self):
        return self._doc
    # end def

    def generatorStrand(self):
        """Return a generator that yields the strands in self._strandList."""
        return iter(self._strandList)
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def isDrawn5to3(self):
        return self._virtualHelix.isDrawn5to3(self)
    # end def

    def isStaple(self):
        return self._strandType == StrandType.Staple
    # end def

    def isScaffold(self):
        return self._strandType == StrandType.Scaffold
    # end def

    def getNeighbors(self, strand):
        isInSet, overlap, strandSetIdx = self._findIndexOfRangeFor(strand)
        sList = self._strandList
        if isInSet:
            if strandSetIdx > 0:
                lowStrand = sList[strandSetIdx - 1]
            else:
                lowStrand = None
            if strandSetIdx < len(sList) - 1:
                highStrand = sList[strandSetIdx + 1]
            else:
                highStrand = None
            return lowStrand, highStrand
        else:
            raise IndexError
    # end def

    def complementStrandSet(self):
        """
        Returns the complementary strandset. Used for insertions and
        sequence application.
        """
        vh = self.virtualHelix()
        if self.isStaple():
            return vh.scaffoldStrandSet()
        else:
            return vh.stapleStrandSet()
    # end def

    def getBoundsOfEmptyRegionContaining(self, baseIdx):
        """
        Returns the (tight) bounds of the contiguous stretch of unpopulated
        bases that includes the baseIdx.
        """
        lowIdx, highIdx = 0, self.partMaxBaseIdx()  # init the return values
        lenStrands = len(self._strandList)

        # not sure how to set this up this to help in caching
        # lastIdx = self._lastStrandSetIndex

        if lenStrands == 0:  # empty strandset, just return the part bounds
            return (lowIdx, highIdx)

        low = 0              # index of the first (left-most) strand
        high = lenStrands    # index of the last (right-most) strand
        while low < high:    # perform binary search to find empty region
            mid = (low + high) // 2
            midStrand = self._strandList[mid]
            mLow, mHigh = midStrand.idxs()
            if baseIdx < mLow:  # baseIdx is to the left of crntStrand
                high = mid   # continue binary search to the left
                highIdx = mLow - 1  # set highIdx to left of crntStrand
            elif baseIdx > mHigh:   # baseIdx is to the right of crntStrand
                low = mid + 1    # continue binary search to the right
                lowIdx = mHigh + 1  # set lowIdx to the right of crntStrand
            else:
                return (None, None)  # baseIdx was not empty
        self._lastStrandSetIndex = (low + high) // 2  # set cache
        return (lowIdx, highIdx)
    # end def

    def indexOfRightmostNonemptyBase(self):
        """Returns the high baseIdx of the last strand, or 0."""
        if len(self._strandList) > 0:
            return self._strandList[-1].highIdx()
        else:
            return 0

    def partMaxBaseIdx(self):
        """Return the bounds of the StrandSet as defined in the part."""
        return self._virtualHelix.part().maxBaseIdx()
    # end def

    def strandCount(self):
        return len(self._strandList)
    # end def

    def strandType(self):
        return self._strandType
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def createStrand(self, baseIdxLow, baseIdxHigh, useUndoStack=True):
        """
        Assumes a strand is being created at a valid set of indices.
        """
        boundsLow, boundsHigh = \
                            self.getBoundsOfEmptyRegionContaining(baseIdxLow)
        canInsert, strandSetIdx = \
                                self.getIndexToInsert(baseIdxLow, baseIdxHigh)
        if canInsert:
            c = StrandSet.CreateStrandCommand(self,
                                        baseIdxLow, baseIdxHigh, strandSetIdx)
            row, col = self._virtualHelix.coord()
            # d = "(%d,%d).%d + [%d,%d]" % \
            #             (row, col, self._strandType, baseIdxLow, baseIdxHigh)
            d = "(%d,%d).%d^%d" % (row, col, self._strandType, strandSetIdx)
            util.execCommandList(self, [c], desc=d, useUndoStack=useUndoStack)
            return strandSetIdx
        else:
            return -1
    # end def

    def createDeserializedStrand(self, baseIdxLow, baseIdxHigh, useUndoStack=False):
        """
        Passes a strand to AddStrandCommand that was read in from file input.
        Omits the step of checking _couldStrandInsertAtLastIndex, since
        we assume that deserialized strands will not cause collisions.
        """
        boundsLow, boundsHigh = self.getBoundsOfEmptyRegionContaining(baseIdxLow)
        assert(baseIdxLow < baseIdxHigh)
        assert(boundsLow <= baseIdxLow)
        assert(baseIdxHigh <= boundsHigh)
        canInsert, strandSetIdx = self.getIndexToInsert(baseIdxLow, baseIdxHigh)
        if canInsert:
            c = StrandSet.CreateStrandCommand(self, baseIdxLow, baseIdxHigh, strandSetIdx)
            util.execCommandList(self, [c], desc=None, useUndoStack=useUndoStack)
            return strandSetIdx
        else:
            return -1
    # end def

    def removeStrand(self, strand, strandSetIdx=None, useUndoStack=True, solo=True):
        """
        solo is an argument to enable limiting signals emiting from
        the command in the case the command is instantiated part of a larger
        command
        """
        cmds = []
        if strandSetIdx == None:
            isInSet, overlap, strandSetIdx = self._findIndexOfRangeFor(strand)
            if not isInSet:
                raise IndexError
        if self.isScaffold() and strand.sequence() != None:
            cmds.append(strand.oligo().applySequenceCMD(None))
        cmds += strand.clearDecoratorCommands()
        cmds.append(StrandSet.RemoveStrandCommand(self, strand, strandSetIdx, solo))
        util.execCommandList(self, cmds, desc="Remove strand", useUndoStack=useUndoStack)
        return strandSetIdx
    # end def

    def removeAllStrands(self, useUndoStack=True):
        # copy the list because we are going to shrink it and that's
        # a no no with iterators
        #temp = [x for x in self._strandList]
        for strand in list(self._strandList):#temp:
            self.removeStrand(strand, 0, useUndoStack, solo=False)
        # end def

    def mergeStrands(self, priorityStrand, otherStrand, useUndoStack=True):
        """
        Merge the priorityStrand and otherStrand into a single new strand.
        The oligo of priority should be propagated to the other and all of
        its connections.
        """
        lowAndHighStrands = self.strandsCanBeMerged(priorityStrand, otherStrand)
        if lowAndHighStrands:
            strandLow, strandHigh = lowAndHighStrands
            isInSet, overlap, lowStrandSetIdx = self._findIndexOfRangeFor(strandLow)
            if isInSet:
                c = StrandSet.MergeCommand(strandLow, strandHigh, \
                                            lowStrandSetIdx, priorityStrand)
                util.execCommandList(self, [c], desc="Merge", useUndoStack=useUndoStack)
    # end def

    def strandsCanBeMerged(self, strandA, strandB):
        """
        returns None if the strands can't be merged, otherwise
        if the strands can be merge it returns the strand with the lower index

        only checks that the strands are of the same StrandSet and that the
        end points differ by 1.  DOES NOT check if the Strands overlap, that
        should be handled by addStrand
        """
        if strandA.strandSet() != strandB.strandSet():
            return None
        if abs(strandA.lowIdx() - strandB.highIdx()) == 1 or \
            abs(strandB.lowIdx() - strandA.highIdx()) == 1:
            if strandA.lowIdx() < strandB.lowIdx():
                if not strandA.connectionHigh() and not strandB.connectionLow():
                    return strandA, strandB
            else:
                if not strandB.connectionHigh() and not strandA.connectionLow():
                    return strandB, strandA
        else:
            return None
    # end def

    def splitStrand(self, strand, baseIdx, updateSequence=True, useUndoStack=True):
        """
        Break strand into two strands. Reapply sequence by default (disabled
        during autostaple).
        """
        if self.strandCanBeSplit(strand, baseIdx):
            isInSet, overlap, strandSetIdx = self._findIndexOfRangeFor(strand)
            if isInSet:
                c = StrandSet.SplitCommand(strand, baseIdx, strandSetIdx, updateSequence)
                util.execCommandList(self, [c], desc="Split", useUndoStack=useUndoStack)
                return True
            else:
                return False
        else:
            return False
    # end def

    def strandCanBeSplit(self, strand, baseIdx):
        """
        Make sure the base index is within the strand
        Don't split right next to a 3Prime end
        Don't split on endpoint (AKA a crossover)
        """
        # no endpoints
        if baseIdx == strand.lowIdx() or baseIdx == strand.highIdx():
            return False
        # make sure the base index within the strand
        elif strand.lowIdx() > baseIdx or baseIdx > strand.highIdx():
            return False
        elif abs(baseIdx - strand.idx3Prime()) > 1:
            return True
    # end def

    def destroy(self):
        self.setParent(None)
        self.deleteLater()  # QObject will emit a destroyed() Signal
    # end def

    def remove(self, useUndoStack=True):
        """
        Removes a VirtualHelix from the model. Accepts a reference to the
        VirtualHelix, or a (row,col) lattice coordinate to perform a lookup.
        """
        if useUndoStack:
            self.undoStack().beginMacro("Delete StrandSet")
        self.removeAllStrands(useUndoStack)
        if useUndoStack:
            self.undoStack().endMacro()
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def undoStack(self):
        if self._undoStack == None:
            self._undoStack = self._virtualHelix.undoStack()
        return self._undoStack

    def virtualHelix(self):
        return self._virtualHelix

    def strandFilter(self):
        return "scaffold" if self._strandType == StrandType.Scaffold else "staple"

    def hasStrandAt(self, idxLow, idxHigh):
        """
        """
        dummyStrand = Strand(self, idxLow, idxHigh)
        strandList = [s for s in self._findOverlappingRanges(dummyStrand)]
        dummyStrand._strandSet = None
        dummyStrand.setParent(None)
        dummyStrand.deleteLater()
        dummyStrand = None
        return len(strandList) > 0
    # end def

    def getOverlappingStrands(self, idxLow, idxHigh):
        dummyStrand = Strand(self, idxLow, idxHigh)
        strandList = [s for s in self._findOverlappingRanges(dummyStrand)]
        dummyStrand._strandSet = None
        dummyStrand.setParent(None)
        dummyStrand.deleteLater()
        dummyStrand = None
        return strandList
    # end def

    def hasStrandAtAndNoXover(self, idx):
        dummyStrand = Strand(self, idx, idx)
        strandList = [s for s in self._findOverlappingRanges(dummyStrand)]
        dummyStrand._strandSet = None
        dummyStrand.setParent(None)
        dummyStrand.deleteLater()
        dummyStrand = None
        if len(strandList) > 0:
            return False if strandList[0].hasXoverAt(idx) else True
        else:
            return False
    # end def

    def hasNoStrandAtOrNoXover(self, idx):
        dummyStrand = Strand(self, idx, idx)
        strandList = [s for s in self._findOverlappingRanges(dummyStrand)]
        dummyStrand._strandSet = None
        dummyStrand.setParent(None)
        dummyStrand.deleteLater()
        dummyStrand = None
        if len(strandList) > 0:
            return False if strandList[0].hasXoverAt(idx) else True
        else:
            return True
    # end def

    def getIndexToInsert(self, idxLow, idxHigh):
        """
        """
        canInsert = True
        dummyStrand = Strand(self, idxLow, idxHigh)
        if self._couldStrandInsertAtLastIndex(dummyStrand):
            return canInsert, self._lastStrandSetIndex
        isInSet, overlap, idx = self._findIndexOfRangeFor(dummyStrand)
        dummyStrand._strandSet = None
        dummyStrand.setParent(None)
        dummyStrand.deleteLater()
        dummyStrand = None
        if overlap:
            canInsert = False
        return canInsert, idx
    # end def

    def getStrand(self, baseIdx):
        """Returns the strand that overlaps with baseIdx."""
        dummyStrand = Strand(self, baseIdx, baseIdx)
        strandList = [s for s in self._findOverlappingRanges(dummyStrand)]
        dummyStrand._strandSet = None
        dummyStrand.setParent(None)
        dummyStrand.deleteLater()
        dummyStrand = None
        return strandList[0] if len(strandList) > 0 else None
    # end def

    def getLegacyArray(self):
        """docstring for getLegacyArray"""
        num = self._virtualHelix.number()
        ret = [[-1, -1, -1, -1] for i in range(self.part().maxBaseIdx() + 1)]
        if self.isDrawn5to3():
            for strand in self._strandList:
                lo, hi = strand.idxs()
                assert strand.idx5Prime() == lo and strand.idx3Prime() == hi
                # map the first base (5' xover if necessary)
                s5p = strand.connection5p()
                if s5p != None:
                    ret[lo][0] = s5p.virtualHelix().number()
                    ret[lo][1] = s5p.idx3Prime()
                ret[lo][2] = num
                ret[lo][3] = lo + 1
                # map the internal bases
                for idx in range(lo + 1, hi):
                    ret[idx][0] = num
                    ret[idx][1] = idx - 1
                    ret[idx][2] = num
                    ret[idx][3] = idx + 1
                # map the last base (3' xover if necessary)
                ret[hi][0] = num
                ret[hi][1] = hi - 1
                s3p = strand.connection3p()
                if s3p != None:
                    ret[hi][2] = s3p.virtualHelix().number()
                    ret[hi][3] = s3p.idx5Prime()
                # end if
            # end for
        # end if
        else:
            for strand in self._strandList:
                lo, hi = strand.idxs()
                assert strand.idx3Prime() == lo and strand.idx5Prime() == hi
                # map the first base (3' xover if necessary)
                ret[lo][0] = num
                ret[lo][1] = lo + 1
                s3p = strand.connection3p()
                if s3p != None:
                    ret[lo][2] = s3p.virtualHelix().number()
                    ret[lo][3] = s3p.idx5Prime()
                # map the internal bases
                for idx in range(lo + 1, hi):
                    ret[idx][0] = num
                    ret[idx][1] = idx + 1
                    ret[idx][2] = num
                    ret[idx][3] = idx - 1
                # map the last base (5' xover if necessary)
                ret[hi][2] = num
                ret[hi][3] = hi - 1
                s5p = strand.connection5p()
                if s5p != None:
                    ret[hi][0] = s5p.virtualHelix().number()
                    ret[hi][1] = s5p.idx3Prime()
                # end if
            # end for
        return ret
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _addToStrandList(self, strand, idx):
        """Inserts strand into the _strandList at idx."""
        self._strandList.insert(idx, strand)

    def _removeFromStrandList(self, strand):
        """Remove strand from _strandList."""
        self._doc.removeStrandFromSelection(strand)  # make sure the strand is no longer selected
        self._strandList.remove(strand)

    def _couldStrandInsertAtLastIndex(self, strand):
        """Verification of insertability based on cached last index."""
        lastInd = self._lastStrandSetIndex
        strandList = self._strandList
        if lastInd == None or lastInd > (len(strandList) - 1):
            self._lastStrandSetIndex = None
            return False
        else:
            sTestHigh = strandList[lastInd].lowIdx() if lastInd < len(strandList) else self.partMaxBaseIdx()
            sTestLow = strandList[lastInd - 1].highIdx() if lastInd > 0 else - 1
            sLow, sHigh = strand.idxs()
            if sTestLow < sLow and sHigh < sTestHigh:
                return True
            else:
                return False

    def _findOverlappingRanges(self, qstrand, useCache=False):
        """
        a binary search for the strands in self._strandList overlapping with
        a query strands, or qstrands, indices.

        Useful for operations on complementary strands such as applying a
        sequence

        This is an generator for now

        Strategy:
        1.
            search the _strandList for a strand the first strand that has a
            highIndex >= lowIndex of the query strand.
            save that strandSet index as sSetIndexLow.
            if No strand satisfies this condition, return an empty list

            Unless it matches the query strand's lowIndex exactly,
            Step 1 is O(log N) where N in length of self._strandList to the max,
            that is it needs to exhaust the search

            conversely you could search for first strand that has a
            lowIndex LESS than or equal to the lowIndex of the query strand.

        2.
            starting at self._strandList[sSetIndexLow] test each strand to see if
            it's indexLow is LESS than or equal to qstrand.indexHigh.  If it is
            yield/return that strand.  If it's GREATER than the indexHigh, or
            you run out of strands to check, the generator terminates
        """
        strandList = self._strandList
        lenStrands = len(strandList)
        if lenStrands == 0:
            return
        # end if

        low = 0
        high = lenStrands
        qLow, qHigh = qstrand.idxs()

        # Step 1: get rangeIndexLow with a binary search
        if useCache:  # or self.doesLastSetIndexMatch(qstrand, strandList):
            # cache match!
            sSetIndexLow = self._lastStrandSetIndex
        else:
            sSetIndexLow = -1
            while low < high:
                mid = (low + high) // 2
                midStrand = strandList[mid]

                # pre get indices from the currently tested strand
                mLow, mHigh = midStrand.idxs()

                if mHigh == qLow:
                    # match, break out of while loop
                    sSetIndexLow = mid
                    break
                elif mHigh > qLow:
                    # store the candidate index
                    sSetIndexLow = mid
                    # adjust the high index to find a better candidate if
                    # it exists
                    high = mid
                # end elif
                else:  # mHigh < qLow
                    # If a strand exists it must be a higher rangeIndex
                    # leave the high the same
                    low = mid + 1
                #end elif
            # end while
        # end else

        # Step 2: create a generator on matches
        # match on whether the tempStrand's lowIndex is
        # within the range of the qStrand
        if sSetIndexLow > -1:
            tempStrands = iter(strandList[sSetIndexLow:])
            tempStrand = next(tempStrands)
            qHigh += 1  # bump it up for a more efficient comparison
            i = 0   # use this to
            while tempStrand and tempStrand.lowIdx() < qHigh:
                yield tempStrand
                # use a next and a default to cause a break condition
                tempStrand = next(tempStrands, None)
                i += 1
            # end while

            # cache the last index we left of at
            i = sSetIndexLow + i
            """
            if
            1. we ran out of strands to test adjust
                OR
            2. the end condition tempStrands highIndex is still inside the
            qstrand but not equal to the end point
                adjust i down 1
            otherwise
            """
            if not tempStrand or tempStrand.highIdx() < qHigh - 1:
                i -= 1
            # assign cache but double check it's a valid index
            self._lastStrandSetIndex = i if -1 < i < lenStrands else None
            return
        else:
            # no strand was found
            # go ahead and clear the cache
            self._lastStrandSetIndex = None if len(self._strandList) > 0 else 0
            return
    # end def

    def getStrandIndex(self, strand):
        try:
            ind = self._strandList.index(strand)
            return (True, ind)
        except ValueError:
            return (False, 0)
    # end def

    def _findIndexOfRangeFor(self, strand):
        """
        Performs a binary search for strand in self._strandList.

        If the strand is found, we want to return its index and we don't care
        about whether it overlaps with anything.

        If the strand is not found, we want to return whether it would
        overlap with any existing strands, and if not, the index where it
        would go.

        Returns a tuple (found, overlap, idx)
            found is True if strand in self._strandList
            overlap is True if strand is not found, and would overlap with
            existing strands in self._strandList
            idx is the index where the strand was found if found is True
            idx is the index where the strand could be inserted if found
            is False and overlap is False.
        """
        # setup
        strandList = self._strandList
        lastIdx = self._lastStrandSetIndex
        lenStrands = len(strandList)
        # base case: empty list, can insert at 0
        if lenStrands == 0:
            return (False, False, 0)
        # check cache
        if lastIdx:
            if lastIdx < lenStrands and strandList[lastIdx] == strand:
                return (True, False, lastIdx)
        # init search bounds
        low, high = 0, lenStrands
        sLow, sHigh = strand.idxs()
        # perform binary search
        while low < high:
            mid = (low + high) // 2
            midStrand = strandList[mid]
            mLow, mHigh = midStrand.idxs()
            if midStrand == strand:
                self._lastStrandSetIndex = mid
                return (True, False, mid)
            elif mHigh < sLow:
                #  strand                [sLow----)
                # mStrand  (----mHigh]
                low = mid + 1  # search higher
            elif mLow > sHigh:
                #  strand  (----sHigh]
                # mStrand                [mLow----)
                high = mid  # search lower
            else:
                if mLow <= sLow <= mHigh:
                    # overlap: right side of mStrand
                    #  strand         [sLow---------------)
                    # mStrand  [mLow----------mHigh]
                    self._lastStrandSetIndex = None
                    return (False, True, None)
                elif mLow <= sHigh <= mHigh:
                    # overlap: left side of mStrand
                    #  strand  (--------------sHigh]
                    # mStrand         [mLow-----------mHigh]
                    self._lastStrandSetIndex = None
                    return (False, True, None)
                elif sLow <= mLow and mHigh <= sHigh:
                    # overlap: strand encompases existing
                    #  strand  [sLow-------------------sHigh]
                    # mStrand         [mLow----mHigh]
                    # note: inverse case is already covered above
                    self._lastStrandSetIndex = None
                    return (False, True, None)
                else:
                    # strand not in set, here's where you'd insert it
                    self._lastStrandSetIndex = mid
                    return (False, False, mid)
            # end else
        self._lastStrandSetIndex = low
        return (False, False, low)
    # end def

    def _doesLastSetIndexMatch(self, qstrand, strandList):
        """
        strandList is passed to save a lookup
        """
        lSI = self._lastStrandSetIndex
        if lSI:
            qLow, qHigh = qstrand.idxs()
            tempStrand = strandList[lSI]
            tLow, tHigh = tempStrand.idxs()
            if not (qLow <= tLow <= qHigh or qLow <= tHigh <= qHigh):
                return False
            else:  # get a difference
                dif = abs(qLow - tLow)
                # check neighboring strandList just in case
                difLow = dif + 1
                if lSI > 0:
                    tLow, tHigh = strand[lSI - 1].idxs()
                    if qLow <= tLow <= qHigh or qLow <= tHigh <= qHigh:
                        difLow = abs(qLow - tLow)
                difHigh = dif + 1
                if lSI < len(strand) - 1:
                    tLow, tHigh = strand[lSI + 1].idxs()
                    if qLow <= tLow <= qHigh or qLow <= tHigh <= qHigh:
                        difHigh = abs(qLow - tLow)
                # check that the cached strand is in fact the right guy
                if dif < difLow and dif < difHigh:
                    return True
                else:
                    False
            # end else
        # end if
        else:
            return False
        # end else
    # end def

    ### COMMANDS ###
    class CreateStrandCommand(QUndoCommand):
        """
        Create a new Strand based with bounds (baseIdxLow, baseIdxHigh),
        and insert it into the strandSet at position strandSetIdx. Also,
        create a new Oligo, add it to the Part, and point the new Strand
        at the oligo.
        """
        def __init__(self, strandSet, baseIdxLow, baseIdxHigh, strandSetIdx):
            super(StrandSet.CreateStrandCommand, self).__init__()
            self._strandSet = strandSet
            self._sSetIdx = strandSetIdx
            self._strand = Strand(strandSet, baseIdxLow, baseIdxHigh)
            colorList = styles.stapColors if strandSet.isStaple() else [styles.scafColors[0]] # default to classic 0066cc
            color = random.choice(colorList).name()
            self._newOligo = Oligo(None, color)  # redo will set part
            self._newOligo.setLength(self._strand.totalLength())
        # end def

        def redo(self):
            # Add the new strand to the StrandSet strandList
            strand = self._strand
            strandSet = self._strandSet
            strandSet._strandList.insert(self._sSetIdx, strand)
            # Set up the new oligo
            oligo = self._newOligo
            oligo.setStrand5p(strand)
            oligo.addToPart(strandSet.part())
            strand.setOligo(oligo)

            if strandSet.isStaple():
                strand.reapplySequence()
            # Emit a signal to notify on completion
            strandSet.strandsetStrandAddedSignal.emit(strandSet, strand)
            # for updating the Slice View displayed helices
            strandSet.part().partStrandChangedSignal.emit(strandSet.part(), strandSet.virtualHelix())
        # end def

        def undo(self):
            # Remove the strand from StrandSet strandList and selectionList
            strand = self._strand
            strandSet = self._strandSet
            strandSet._doc.removeStrandFromSelection(strand)
            strandSet._strandList.pop(self._sSetIdx)
            # Get rid of the new oligo
            oligo = self._newOligo
            oligo.setStrand5p(None)
            oligo.removeFromPart()
            # Emit a signal to notify on completion
            strand.strandRemovedSignal.emit(strand)
            strand.setOligo(None)
            # for updating the Slice View displayed helices
            strandSet.part().partStrandChangedSignal.emit(strandSet.part(), strandSet.virtualHelix())
        # end def
    # end class

    class RemoveStrandCommand(QUndoCommand):
        """
        RemoveStrandCommand deletes a strand. It should only be called on
        strands with no connections to other strands.
        """
        def __init__(self, strandSet, strand, strandSetIdx, solo=True):
            super(StrandSet.RemoveStrandCommand, self).__init__()
            self._strandSet = strandSet
            self._strand = strand
            self._sSetIdx = strandSetIdx
            self._solo = solo
            self._oldStrand5p = strand.connection5p()
            self._oldStrand3p = strand.connection3p()
            self._oligo = olg = strand.oligo()
            # only create a new 5p oligo if there is a 3' connection
            self._newOligo5p = olg.shallowCopy() if self._oldStrand5p else None
            if olg.isLoop() or self._oldStrand3p == None:
                self._newOligo3p = olg3p = None
                if self._newOligo5p:
                    self._newOligo5p.setLoop(False)
            else:
                self._newOligo3p = olg3p = olg.shallowCopy()
                olg3p.setStrand5p(self._oldStrand3p)
                colorList = styles.stapColors if strandSet.isStaple() else [styles.scafColors[0]]
                color = random.choice(colorList).name()
                olg3p.setColor(color)
                olg3p.refreshLength()
        # end def

        def redo(self):
            # Remove the strand
            strand = self._strand
            strandSet = self._strandSet
            # strandSet._removeFromStrandList(strand)
            strandSet._doc.removeStrandFromSelection(strand)
            strandSet._strandList.pop(self._sSetIdx)
            strand5p = self._oldStrand5p
            strand3p = self._oldStrand3p
            oligo = self._oligo
            olg5p = self._newOligo5p
            olg3p = self._newOligo3p

            #oligo.incrementLength(-strand.totalLength())
            
            oligo.removeFromPart()

            if strand5p != None:
                strand5p.setConnection3p(None)
            if strand3p != None:
                strand3p.setConnection5p(None)

            # Clear connections and update oligos
            if strand5p != None:
                for s5p in oligo.strand5p().generator3pStrand():
                    Strand.setOligo(s5p, olg5p)
                olg5p.refreshLength()
                olg5p.addToPart(strandSet.part())
                if self._solo:
                    part = strandSet.part()
                    vh = strandSet.virtualHelix()
                    part.partActiveVirtualHelixChangedSignal.emit(part, vh)
                    #strand5p.strandXover5pChangedSignal.emit(strand5p, strand)
                strand5p.strandUpdateSignal.emit(strand5p)
            # end if
            if strand3p != None:
                if not oligo.isLoop():
                    # apply 2nd oligo copy to all 3' downstream strands
                    for s3p in strand3p.generator3pStrand():
                        Strand.setOligo(s3p, olg3p)
                    olg3p.addToPart(strandSet.part())
                if self._solo:
                    part = strandSet.part()
                    vh = strandSet.virtualHelix()
                    part.partActiveVirtualHelixChangedSignal.emit(part, vh)
                    # strand.strandXover5pChangedSignal.emit(strand, strand3p)
                strand3p.strandUpdateSignal.emit(strand3p)
            # end if
            # Emit a signal to notify on completion
            strand.strandRemovedSignal.emit(strand)
            # for updating the Slice View displayed helices
            strandSet.part().partStrandChangedSignal.emit(strandSet.part(), strandSet.virtualHelix())
        # end def

        def undo(self):
            # Restore the strand
            strand = self._strand
            strandSet = self._strandSet
            # Add the newStrand to the sSet
            strandSet._addToStrandList(strand, self._sSetIdx)
            # strandSet._strandList.insert(self._sSetIdx, strand)
            strand5p = self._oldStrand5p
            strand3p = self._oldStrand3p
            oligo = self._oligo
            olg5p = self._newOligo5p
            olg3p = self._newOligo3p

            # Restore connections to this strand
            if strand5p != None:
                strand5p.setConnection3p(strand)

            if strand3p != None:
                strand3p.setConnection5p(strand)

            # oligo.decrementLength(strand.totalLength())
            
            # Restore the oligo
            oligo.addToPart(strandSet.part())
            if olg5p:
                olg5p.removeFromPart()
            if olg3p:
                olg3p.removeFromPart()
            for s5p in oligo.strand5p().generator3pStrand():
                Strand.setOligo(s5p, oligo)
            # end for

            # Emit a signal to notify on completion
            strandSet.strandsetStrandAddedSignal.emit(strandSet, strand)
            # for updating the Slice View displayed helices
            strandSet.part().partStrandChangedSignal.emit(strandSet.part(), strandSet.virtualHelix())

            # Restore connections to this strand
            if strand5p != None:
                if self._solo:
                    part = strandSet.part()
                    vh = strandSet.virtualHelix()
                    part.partActiveVirtualHelixChangedSignal.emit(part, vh)
                    # strand5p.strandXover5pChangedSignal.emit(
                    #                                        strand5p, strand)
                strand5p.strandUpdateSignal.emit(strand5p)
                strand.strandUpdateSignal.emit(strand)

            if strand3p != None:
                if self._solo:
                    part = strandSet.part()
                    vh = strandSet.virtualHelix()
                    part.partActiveVirtualHelixChangedSignal.emit(part, vh)
                    # strand.strandXover5pChangedSignal.emit(strand, strand3p)
                strand3p.strandUpdateSignal.emit(strand3p)
                strand.strandUpdateSignal.emit(strand)
        # end def
    # end class

    class MergeCommand(QUndoCommand):
        """
        This class takes two Strands and merges them.  This Class should be
        private to StrandSet as knowledge of a strandSetIndex outside of this
        of the StrandSet class implies knowledge of the StrandSet
        implementation

        Must pass this two different strands, and nominally one of the strands
        again which is the priorityStrand.  The resulting "merged" strand has
        the properties of the priorityStrand's oligo.  Decorators are preserved

        the strandLow and strandHigh must be presorted such that strandLow
        has a lower range than strandHigh

        lowStrandSetIdx should be known ahead of time as a result of selection
        """
        def __init__(self, strandLow, strandHigh, lowStrandSetIdx, priorityStrand):
            super(StrandSet.MergeCommand, self).__init__()
            # Store strands
            self._strandLow = strandLow
            self._strandHigh = strandHigh
            pS = priorityStrand
            self._sSet = sSet = pS.strandSet()
            # Store oligos
            self._newOligo = pS.oligo().shallowCopy()
            self._sLowOligo = sLOlg = strandLow.oligo()
            self._sHighOligo = sHOlg = strandHigh.oligo()

            self._sSetIdx = lowStrandSetIdx

            # update the new oligo length if it's not a loop
            if sLOlg != sHOlg:
                self._newOligo.setLength(sLOlg.length() + sHOlg.length())

            # Create the newStrand by copying the priority strand to
            # preserve its properties
            newIdxs = strandLow.lowIdx(), strandHigh.highIdx()
            newStrand = strandLow.shallowCopy()
            newStrand.setIdxs(newIdxs)
            newStrand.setConnectionHigh(strandHigh.connectionHigh())
            # Merging any decorators
            newStrand.addDecorators(strandHigh.decorators())
            self._newStrand = newStrand
            # Update the oligo for things like its 5prime end and isLoop
            self._newOligo.strandMergeUpdate(strandLow, strandHigh, newStrand)
            
            # set the new sequence by concatenating the sequence properly
            if strandLow._sequence or strandHigh._sequence:
                tL = strandLow.totalLength()
                tH = strandHigh.totalLength()
                seqL = strandLow._sequence if strandLow._sequence else "".join([" " for i in range(tL)])
                seqH = strandHigh._sequence if strandHigh._sequence else "".join([" " for i in range(tH)])    
                if newStrand.isDrawn5to3():
                    newStrand._sequence = seqL + seqH
                else:
                    newStrand._sequence = seqH + seqL
        # end def

        def redo(self):
            sS = self._sSet
            sL = self._strandLow
            sH = self._strandHigh
            nS = self._newStrand
            idx = self._sSetIdx
            olg = self._newOligo
            lOlg = sL.oligo()
            hOlg = sH.oligo()

            # Remove old strands from the sSet (reusing idx, so order matters)
            sS._removeFromStrandList(sL)
            sS._removeFromStrandList(sH)
            # Add the newStrand to the sSet
            sS._addToStrandList(nS, idx)

            # update connectivity of strands
            nScL = nS.connectionLow()
            if nScL:
                if (nS.isDrawn5to3() and nScL.isDrawn5to3()) or \
                    (not nS.isDrawn5to3() and not nScL.isDrawn5to3()):
                    nScL.setConnectionHigh(nS)
                else:
                    nScL.setConnectionLow(nS)
            nScH = nS.connectionHigh()
            if nScH:
                if (nS.isDrawn5to3() and nScH.isDrawn5to3()) or \
                    (not nS.isDrawn5to3() and not nScH.isDrawn5to3()):
                    nScH.setConnectionLow(nS)
                else:
                    nScH.setConnectionHigh(nS)

            # Traverse the strands via 3'conns to assign the new oligo
            for strand in olg.strand5p().generator3pStrand():
                Strand.setOligo(strand, olg)  # emits strandHasNewOligoSignal

            # Add new oligo and remove old oligos
            olg.addToPart(sS.part())
            lOlg.removeFromPart()
            if hOlg != lOlg:  # check if a loop was created
                hOlg.removeFromPart()

            # Emit Signals related to destruction and addition
            sL.strandRemovedSignal.emit(sL)
            sH.strandRemovedSignal.emit(sH)
            sS.strandsetStrandAddedSignal.emit(sS, nS)
        # end def

        def undo(self):
            sS = self._sSet
            sL = self._strandLow
            sH = self._strandHigh
            nS = self._newStrand
            idx = self._sSetIdx
            olg = self._newOligo
            lOlg = self._sLowOligo
            hOlg = self._sHighOligo
            # Remove the newStrand from the sSet
            sS._removeFromStrandList(nS)
            # Add old strands to the sSet (reusing idx, so order matters)
            sS._addToStrandList(sH, idx)
            sS._addToStrandList(sL, idx)

            # update connectivity of strands
            sLcL = sL.connectionLow()
            if sLcL:
                if (sL.isDrawn5to3() and sLcL.isDrawn5to3()) or \
                    (not sL.isDrawn5to3() and not sLcL.isDrawn5to3()):
                    sLcL.setConnectionHigh(sL)
                else:
                    sLcL.setConnectionLow(sL)
            sHcH = sH.connectionHigh()
            if sHcH:
                if (sH.isDrawn5to3() and sHcH.isDrawn5to3()) or \
                    (not sH.isDrawn5to3() and not sHcH.isDrawn5to3()):
                    sHcH.setConnectionLow(sH)
                else:
                    sHcH.setConnectionHigh(sH)

            # Traverse the strands via 3'conns to assign the old oligo
            for strand in lOlg.strand5p().generator3pStrand():
                Strand.setOligo(strand, lOlg)  # emits strandHasNewOligoSignal
            for strand in hOlg.strand5p().generator3pStrand():
                Strand.setOligo(strand, hOlg)  # emits strandHasNewOligoSignal

            # Remove new oligo and add old oligos
            olg.removeFromPart()
            lOlg.addToPart(sL.part())
            if hOlg != lOlg:
                hOlg.addToPart(sH.part())

            # Emit Signals related to destruction and addition
            nS.strandRemovedSignal.emit(nS)
            sS.strandsetStrandAddedSignal.emit(sS, sL)
            sS.strandsetStrandAddedSignal.emit(sS, sH)
        # end def
    # end class

    class SplitCommand(QUndoCommand):
        """
        The SplitCommand takes as input a strand and "splits" the strand in
        two, such that one new strand 3' end is at baseIdx, and the other
        new strand 5' end is at baseIdx +/- 1 (depending on the direction
        of the strands).

        Under the hood:
        On redo, this command actually is creates two new copies of the
        original strand, resizes each and modifies their connections.
        On undo, the new copies are removed and the original is restored.
        """
        def __init__(self, strand, baseIdx, strandSetIdx, updateSequence=True):
            super(StrandSet.SplitCommand, self).__init__()
            # Store inputs
            self._oldStrand = strand
            oldSequence  = strand._sequence
            is5to3 = strand.isDrawn5to3()
            
            self._sSetIdx = strandSetIdx
            self._sSet = sSet = strand.strandSet()
            self._oldOligo = oligo = strand.oligo()
            # Create copies
            self._strandLow = strandLow = strand.shallowCopy()
            self._strandHigh = strandHigh = strand.shallowCopy()

            if oligo.isLoop():
                self._lOligo = self._hOligo = lOligo = hOligo = oligo.shallowCopy()
            else:
                self._lOligo = lOligo = oligo.shallowCopy()
                self._hOligo = hOligo = oligo.shallowCopy()
            colorList = styles.stapColors if sSet.isStaple() \
                                            else styles.scafColors
            # end

            # Determine oligo retention based on strand priority
            if is5to3:  # strandLow has priority
                iNewLow = baseIdx
                colorLow = oligo.color()
                colorHigh = random.choice(colorList).name()
                olg5p, olg3p = lOligo, hOligo
                std5p, std3p = strandLow, strandHigh
            else:  # strandHigh has priority
                iNewLow = baseIdx - 1
                colorLow = random.choice(colorList).name()
                colorHigh = oligo.color()
                olg5p, olg3p = hOligo, lOligo
                std5p, std3p = strandHigh, strandLow
            # this is for updating a connected xover view object
            # there is only ever one xover a strand is in charge of
            self._strand3p = std3p
            self._strand5p = std5p

            # Update strand connectivity
            strandLow.setConnectionHigh(None)
            strandHigh.setConnectionLow(None)

            # Resize strands and update decorators
            strandLow.setIdxs((strand.lowIdx(), iNewLow))
            strandHigh.setIdxs((iNewLow + 1, strand.highIdx()))

            # Update the oligo for things like its 5prime end and isLoop
            olg5p.strandSplitUpdate(std5p, std3p, olg3p, strand)

            if not oligo.isLoop():
                # Update the oligo color if necessary
                lOligo.setColor(colorLow)
                hOligo.setColor(colorHigh)
                # settle the oligo length
                length = 0
                for strand in std3p.generator3pStrand():
                    length += strand.totalLength()
                # end for
                olg5p.setLength(olg5p.length() - length)
                olg3p.setLength(length)
            # end if

            if updateSequence and oldSequence:
                if is5to3:  # strandLow has priority
                    tL = strandLow.totalLength()
                    strandLow._sequence = oldSequence[0:tL]
                    strandHigh._sequence = oldSequence[tL:]
                    # print "lenght match 5 to 3", strandHigh.totalLength()+tL == len(oldSequence)
                    # assert (strandHigh.totalLength()+tL == len(oldSequence))
                else:
                    tH = strandHigh.totalLength()
                    strandHigh._sequence = oldSequence[0:tH]
                    strandLow._sequence = oldSequence[tH:]
                    # print "lenght match 3 to 5", strandLow.totalLength()+tH == len(oldSequence)
                    # assert (strandLow.totalLength()+tH == len(oldSequence))

        # end def

        def redo(self):
            sS = self._sSet
            sL = self._strandLow
            sH = self._strandHigh
            oS = self._oldStrand
            idx = self._sSetIdx
            olg = self._oldOligo
            lOlg = self._lOligo
            hOlg = self._hOligo
            wasNotLoop = lOlg != hOlg

            # Remove old Strand from the sSet
            sS._removeFromStrandList(oS)

            # Add new strands to the sSet (reusing idx, so order matters)
            sS._addToStrandList(sH, idx)
            sS._addToStrandList(sL, idx)

            # update connectivity of strands
            sLcL = sL.connectionLow()
            if sLcL:
                if (oS.isDrawn5to3() and sLcL.isDrawn5to3()) or \
                    (not oS.isDrawn5to3() and not sLcL.isDrawn5to3()):
                    sLcL.setConnectionHigh(sL)
                else:
                    sLcL.setConnectionLow(sL)
            sHcH = sH.connectionHigh()
            if sHcH:
                if (oS.isDrawn5to3() and sHcH.isDrawn5to3()) or \
                    (not oS.isDrawn5to3() and not sHcH.isDrawn5to3()):
                    sHcH.setConnectionLow(sH)
                else:
                    sHcH.setConnectionHigh(sH)

            # Traverse the strands via 3'conns to assign the new oligos
            for strand in lOlg.strand5p().generator3pStrand():
                Strand.setOligo(strand, lOlg)  # emits strandHasNewOligoSignal
            if wasNotLoop:  # do the second oligo which is different
                for strand in hOlg.strand5p().generator3pStrand():
                    # emits strandHasNewOligoSignal
                    Strand.setOligo(strand, hOlg)

            # Add new oligo and remove old oligos from the part
            olg.removeFromPart()
            lOlg.addToPart(sL.part())
            if wasNotLoop:
                hOlg.addToPart(sH.part())

            # Emit Signals related to destruction and addition
            oS.strandRemovedSignal.emit(oS)
            sS.strandsetStrandAddedSignal.emit(sS, sH)
            sS.strandsetStrandAddedSignal.emit(sS, sL)
        # end def

        def undo(self):
            sS = self._sSet
            sL = self._strandLow
            sH = self._strandHigh
            oS = self._oldStrand
            idx = self._sSetIdx
            olg = self._oldOligo
            lOlg = self._lOligo
            hOlg = self._hOligo
            wasNotLoop = lOlg != hOlg

            # Remove new strands from the sSet (reusing idx, so order matters)
            sS._removeFromStrandList(sL)
            sS._removeFromStrandList(sH)
            # Add the old strand to the sSet
            sS._addToStrandList(oS, idx)

            # update connectivity of strands
            oScL = oS.connectionLow()
            if oScL:
                if (oS.isDrawn5to3() and oScL.isDrawn5to3()) or \
                    (not oS.isDrawn5to3() and not oScL.isDrawn5to3()):
                    oScL.setConnectionHigh(oS)
                else:
                    oScL.setConnectionLow(oS)
            oScH = oS.connectionHigh()
            if oScH:
                if (oS.isDrawn5to3() and oScH.isDrawn5to3()) or \
                    (not oS.isDrawn5to3() and not oScH.isDrawn5to3()):
                    oScH.setConnectionLow(oS)
                else:
                    oScH.setConnectionHigh(oS)

            # Traverse the strands via 3'conns to assign the old oligo
            for strand in olg.strand5p().generator3pStrand():
                Strand.setOligo(strand, olg)
            # Add old oligo and remove new oligos from the part
            olg.addToPart(sS.part())
            lOlg.removeFromPart()
            if wasNotLoop:
                hOlg.removeFromPart()

            # Emit Signals related to destruction and addition
            sL.strandRemovedSignal.emit(sL)
            sH.strandRemovedSignal.emit(sH)
            sS.strandsetStrandAddedSignal.emit(sS, oS)
        # end def
    # end class

    def deepCopy(self, virtualHelix):
        """docstring for deepCopy"""
        pass
    # end def
# end class
