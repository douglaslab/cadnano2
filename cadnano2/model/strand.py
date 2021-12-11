#!/usr/bin/env python
# encoding: utf-8

from operator import attrgetter
import cadnano2.util as util
from array import array
from .decorators.insertion import Insertion

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject'])
util.qtWrapImport('QtGui', globals(), ['QUndoStack', 'QUndoCommand'])


ARRAY_TYPE = 'B'


def sixb(x): return x.encode('utf-8')


def tostring(x): return x.tobytes().decode('utf-8')


class Strand(QObject):
    """
    A Strand is a continuous stretch of bases that are all in the same
    StrandSet (recall: a VirtualHelix is made up of two StrandSets).

    Every Strand has two endpoints. The naming convention for keeping track
    of these endpoints is based on the relative numeric value of those
    endpoints (low and high). Thus, Strand has a '_baseIdxLow', which is its
    index with the lower numeric value (typically positioned on the left),
    and a '_baseIdxHigh' which is the higher-value index (typically positioned
    on the right)

    Strands can be linked to other strands by "connections". References to
    connected strands are named "_strand5p" and "_strand3p", which correspond
    to the 5' and 3' phosphate linkages in the physical DNA strand,
    respectively. Since Strands can point 5'-to-3' in either the low-to-high
    or high-to-low directions, connection accessor methods (connectionLow and
    connectionHigh) are bound during the init for convenience.
    """

    def __init__(self, strandSet, baseIdxLow, baseIdxHigh, oligo=None):
        super(Strand, self).__init__(strandSet)
        self._strandSet = strandSet
        self._doc = strandSet.document()

        self._baseIdxLow = baseIdxLow  # base index of the strand's left bound
        self._baseIdxHigh = baseIdxHigh  # base index of the right bound
        self._oligo = oligo
        self._strand5p = None  # 5' connection to another strand
        self._strand3p = None  # 3' connection to another strand
        self._sequence = None

        self._decorators = {}
        self._modifiers = {}

        # dynamic methods for mapping high/low connection /indices
        # to corresponding 3Prime 5Prime
        isDrawn5to3 = strandSet.isDrawn5to3()
        if isDrawn5to3:
            self.idx5Prime = self.lowIdx
            self.idx3Prime = self.highIdx
            self.connectionLow = self.connection5p
            self.connectionHigh = self.connection3p
            self.setConnectionLow = self.setConnection5p
            self.setConnectionHigh = self.setConnection3p
        else:
            self.idx5Prime = self.highIdx
            self.idx3Prime = self.lowIdx
            self.connectionLow = self.connection3p
            self.connectionHigh = self.connection5p
            self.setConnectionLow = self.setConnection3p
            self.setConnectionHigh = self.setConnection5p
        self._isDrawn5to3 = isDrawn5to3
    # end def

    def __repr__(self):
        clsName = self.__class__.__name__
        s = "%s.<%s(%s, %s)>" % (self._strandSet.__repr__(),
                                clsName,
                                self._baseIdxLow,
                                self._baseIdxHigh)
        return s

    def generator5pStrand(self):
        """
        Iterate from self to the final _strand5p == None
        3prime to 5prime
        Includes originalCount to check for circular linked list
        """
        originalCount = 0
        node0 = node = self
        f = attrgetter('_strand5p')
        # while node and originalCount == 0:
        #     yield node  # equivalent to: node = node._strand5p
        #     node = f(node)
        #     if node0 == self:
        #         originalCount += 1
        while node:
            yield node  # equivalent to: node = node._strand5p
            node = f(node)
            if node0 == node:
                break

    # end def

    def generator3pStrand(self):
        """
        Iterate from self to the final _strand3p == None
        5prime to 3prime
        Includes originalCount to check for circular linked list
        """
        originalCount = 0
        node0 = node = self
        f = attrgetter('_strand3p')
        while node:
            yield node  # equivalent to: node = node._strand5p
            node = f(node)
            if node0 == node:
                break
    # end def

    def strandFilter(self):
        return self._strandSet.strandFilter()

    ### SIGNALS ###
    strandHasNewOligoSignal = pyqtSignal(QObject)  # strand
    strandRemovedSignal = pyqtSignal(QObject)  # strand
    strandResizedSignal = pyqtSignal(QObject, tuple)

    # Parameters: (strand3p, strand5p)
    strandXover5pChangedSignal = pyqtSignal(QObject, QObject)
    strandXover5pRemovedSignal = pyqtSignal(QObject, QObject)

    # Parameters: (strand)
    strandUpdateSignal = pyqtSignal(QObject)

    # Parameters: (strand, insertion object)
    strandInsertionAddedSignal = pyqtSignal(QObject, object)
    strandInsertionChangedSignal = pyqtSignal(QObject, object)
    # Parameters: (strand, insertion index)
    strandInsertionRemovedSignal = pyqtSignal(QObject, int)

    # Parameters: (strand, decorator object)
    strandDecoratorAddedSignal = pyqtSignal(QObject, object)
    strandDecoratorChangedSignal = pyqtSignal(QObject, object)
    # Parameters: (strand, decorator index)
    strandDecoratorRemovedSignal = pyqtSignal(QObject, int)

    # Parameters: (strand, modifier object)
    strandModifierAddedSignal = pyqtSignal(QObject, object)
    strandModifierChangedSignal = pyqtSignal(QObject, object)
    # Parameters: (strand, modifier index)
    strandModifierRemovedSignal = pyqtSignal(QObject, int)

    # Parameters: (strand, value)
    selectedChangedSignal = pyqtSignal(QObject, tuple)

    ### SLOTS ###
    ### ACCESSORS ###
    def undoStack(self):
        return self._strandSet.undoStack()

    def decorators(self):
        return self._decorators
    # end def

    def isStaple(self):
        return self._strandSet.isStaple()

    def isScaffold(self):
        return self._strandSet.isScaffold()

    def part(self):
        return self._strandSet.part()
    # end def

    def document(self):
        return self._doc
    # end def

    def oligo(self):
        return self._oligo
    # end def

    def sequence(self, forExport=False):
        seq = self._sequence
        if seq:
            return util.markwhite(seq) if forExport else seq
        elif forExport:
            return ''.join(['?' for x in range(self.totalLength())])
        return ''
    # end def

    def strandSet(self):
        return self._strandSet
    # end def

    def strandType(self):
        return self._strandSet.strandType()

    def virtualHelix(self):
        return self._strandSet.virtualHelix()
    # end def

    def setSequence(self, sequenceString):
        """
        Applies sequence string from 5' to 3'
        return the tuple (used, unused) portion of the sequenceString
        """
        if sequenceString == None:
            self._sequence = None
            return None, None
        length = self.totalLength()
        if len(sequenceString) < length:
            bonus = length - len(sequenceString)
            sequenceString += ''.join([' ' for x in range(bonus)])
        temp = sequenceString[0:length]
        self._sequence = temp
        return temp, sequenceString[length:]
    # end def

    def reapplySequence(self):
        """
        """
        compSS = self.strandSet().complementStrandSet()

        # the strand sequence will need to be regenerated from scratch
        # as there are no guarantees about the entirety of the strand moving
        # i.e. both endpoints thanks to multiple selections so just redo the 
        # whole thing
        self._sequence = None

        for compStrand in compSS._findOverlappingRanges(self):
            compSeq = compStrand.sequence()
            usedSeq = util.comp(compSeq) if compSeq else None
            usedSeq = self.setComplementSequence(
                                        usedSeq, compStrand)
        # end for
    # end def

    def getComplementStrands(self):
        """
        return the list of complement strands that overlap with this strand
        """
        compSS = self.strandSet().complementStrandSet()
        return [compStrand for compStrand in compSS._findOverlappingRanges(self)]
    # end def

    def getPreDecoratorIdxList(self):
        """
        Return positions where predecorators should be displayed. This is
        just a very simple check for the presence of xovers on the strand.

        Will refine later by checking for lattice neighbors in 3D.
        """
        return list(range(self._baseIdxLow, self._baseIdxHigh + 1))
    # end def

    # def getPreDecoratorIdxList(self):
    #     """Return positions where predecorators should be displayed."""
    #     part = self._strandSet.part()
    #     validIdxs = sorted([idx[0] for idx in part._stapL + part._stapH])
    #     lo, hi = self._baseIdxLow, self._baseIdxHigh
    #     start = lo if self.connectionLow() == None else lo+1
    #     end = hi if self.connectionHigh() == None else hi-1
    #     ret = []
    #     for i in range(start, end+1):
    #         if i % part.stepSize() in validIdxs:
    #             ret.append(i)
    #     return ret
    # # end def

    def setComplementSequence(self, sequenceString, strand):
        """
        This version takes anothers strand and only sets the indices that
        align with the given complimentary strand

        return the used portion of the sequenceString

        As it depends which direction this is going, and strings are stored in
        memory left to right, we need to test for isDrawn5to3 to map the
        reverse compliment appropriately, as we traverse overlapping strands.

        We reverse the sequence ahead of time if we are applying it 5' to 3',
        otherwise we reverse the sequence post parsing if it's 3' to 5'

        Again, sequences are stored as strings in memory 5' to 3' so we need
        to jump through these hoops to iterate 5' to 3' through them correctly

        Perhaps it's wiser to merely store them left to right and reverse them
        at draw time, or export time
        """
        sLowIdx, sHighIdx = self._baseIdxLow, self._baseIdxHigh
        cLowIdx, cHighIdx = strand.idxs()

        # get the ovelap
        lowIdx, highIdx = util.overlap(sLowIdx, sHighIdx, cLowIdx, cHighIdx)

        # only get the characters we're using, while we're at it, make it the
        # reverse compliment

        totalLength = self.totalLength()

        # see if we are applying
        if sequenceString is None:
            # clear out string for in case of not total overlap
            useSeq = ''.join([' ' for x in range(totalLength)])
        else:  # use the string as is
            useSeq = sequenceString[::-1] if self._isDrawn5to3 \
                                            else sequenceString

        temp = array(ARRAY_TYPE, sixb(useSeq))
        if self._sequence is None:
            tempSelf = array(ARRAY_TYPE, sixb(''.join([' ' for x in range(totalLength)])))
        else:
            tempSelf = array(ARRAY_TYPE, sixb(self._sequence) if self._isDrawn5to3 \
                                                    else sixb(self._sequence[::-1]))

        # generate the index into the compliment string
        a = self.insertionLengthBetweenIdxs(sLowIdx, lowIdx - 1)
        b = self.insertionLengthBetweenIdxs(lowIdx, highIdx)
        c = strand.insertionLengthBetweenIdxs(cLowIdx, lowIdx - 1)
        start = lowIdx - cLowIdx + c
        end = start + b + highIdx - lowIdx + 1
        tempSelf[lowIdx - sLowIdx + a:highIdx - sLowIdx + 1 + a + b] = temp[start:end]
        # print "old sequence", self._sequence
        self._sequence = tostring(tempSelf)

        # if we need to reverse it do it now
        if not self._isDrawn5to3:
            self._sequence = self._sequence[::-1]

        # test to see if the string is empty(), annoyingly expensive
        if len(self._sequence.strip()) == 0:
            self._sequence = None

        # print "new sequence", self._sequence
        return self._sequence
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def connection3p(self):
        return self._strand3p
    # end def

    def connection5p(self):
        return self._strand5p
    # end def

    def idxs(self):
        return (self._baseIdxLow, self._baseIdxHigh)
    # end def

    def lowIdx(self):
        return self._baseIdxLow
    # end def

    def highIdx(self):
        return self._baseIdxHigh
    # end def

    def idx3Prime(self):
        """Returns the absolute baseIdx of the 3' end of the strand."""
        return self.idx3Prime

    def idx5Prime(self):
        """Returns the absolute baseIdx of the 5' end of the strand."""
        return self.idx5Prime

    def isDrawn5to3(self):
        return self._strandSet.isDrawn5to3()
    # end def

    def getSequenceList(self):
        """
        return the list of sequences strings comprising the sequence and the
        inserts as a tuple with the index of the insertion
        [(idx, (strandItemString, insertionItemString), ...]

        This takes advantage of the fact the python iterates a dictionary
        by keys in order so if keys are indices, the insertions will iterate
        out from low index to high index
        """
        seqList = []
        isDrawn5to3 = self._isDrawn5to3
        seq = self._sequence if isDrawn5to3 else self._sequence[::-1]
        # assumes a sequence has been applied correctly and is up to date
        tL = self.totalLength()

        offsetLast = 0
        lengthSoFar = 0
        iLength = 0
        lI, hI = self.idxs()

        for insertion in self.insertionsOnStrand():
            iLength = insertion.length()
            index = insertion.idx()
            offset = index + 1 - lI + lengthSoFar
            if iLength < 0:
                offset -= 1
            # end if
            lengthSoFar += iLength
            seqItem = seq[offsetLast:offset]  # the stranditem seq

            # Because skips literally skip displaying a character at a base
            # position, this needs to be accounted for seperately
            if iLength < 0:
                seqItem += ' '
                offsetLast = offset
            else:
                offsetLast = offset + iLength
            seqInsertion = seq[offset:offsetLast]  # the insertions sequence
            seqList.append((index, (seqItem, seqInsertion)))
        # end for
        # append the last bit of the strand
        seqList.append((lI + tL, (seq[offsetLast:tL], '')))
        if not isDrawn5to3:
            # reverse it again so all sub sequences are from 5' to 3'
            for i in range(len(seqList)):
                index, temp = seqList[i]
                seqList[i] = (index, (temp[0][::-1], temp[1][::-1]))
        return seqList
    # end def

    def canResizeTo(self, newLow, newHigh):
        """
        Checks to see if a resize is allowed. Similar to getResizeBounds
        but works for two bounds at once.
        """
        lowNeighbor, highNeighbor = self._strandSet.getNeighbors(self)
        lowBound = lowNeighbor.highIdx() if lowNeighbor \
                                            else self.part().minBaseIdx()
        highBound = highNeighbor.lowIdx() if highNeighbor \
                                            else self.part().maxBaseIdx()

        if newLow > lowBound and newHigh < highBound:
            return True
        return False

    def getResizeBounds(self, idx):
        """
        Determines (inclusive) low and high drag boundaries resizing
        from an endpoint located at idx.

        When resizing from _baseIdxLow:
            low bound is determined by checking for lower neighbor strands.
            high bound is the index of this strand's high cap, minus 1.

        When resizing from _baseIdxHigh:
            low bound is the index of this strand's low cap, plus 1.
            high bound is determined by checking for higher neighbor strands.

        When a neighbor is not present, just use the Part boundary.
        """
        neighbors = self._strandSet.getNeighbors(self)
        if idx == self._baseIdxLow:
            if neighbors[0]:
                low = neighbors[0].highIdx() + 1
            else:
                low = self.part().minBaseIdx()
            return low, self._baseIdxHigh - 1
        else:  # self._baseIdxHigh
            if neighbors[1]:
                high = neighbors[1].lowIdx() - 1
            else:
                high = self.part().maxBaseIdx()
            return self._baseIdxLow + 1, high
    # end def

    def hasXoverAt(self, idx):
        """
        An xover is necessarily at an enpoint of a strand
        """
        if idx == self.highIdx():
            return True if self.connectionHigh() != None else False
        elif idx == self.lowIdx():
            return True if self.connectionLow() != None else False
        else:
            return False
    # end def

    def canInstallXoverAt(self, idx, fromStrand, fromIdx):
        """
        Assumes idx is:
        self.lowIdx() <= idx <= self.highIdx()
        """

        if self.hasXoverAt(idx):
            return False
        sS = self.strandSet()
        isSameStrand = fromStrand == self
        isStrandTypeMatch = \
                fromStrand.strandSet().strandType() == sS.strandType() \
                                                if fromStrand else True
        if not isStrandTypeMatch:
            return False
        isDrawn5to3 = sS.isDrawn5to3()
        indexDiffH = self.highIdx() - idx
        indexDiffL = idx - self.lowIdx()
        index3Lim = self.idx3Prime() - 1 if isDrawn5to3 \
                                            else self.idx3Prime() + 1
        if isSameStrand:
            indexDiffStrands = fromIdx - idx
            if idx == self.idx5Prime() or idx == index3Lim:
                return True
            elif indexDiffStrands > -3 and indexDiffStrands < 3:
                return False
        # end if for same Strand
        if idx == self.idx5Prime() or idx == index3Lim:
            return True
        elif indexDiffH > 2 and indexDiffL > 1:
            return True
        else:
            return False
    #end def

    def insertionLengthBetweenIdxs(self, idxL, idxH):
        """
        includes the length of insertions in addition to the bases
        """
        tL = 0
        insertions = self.insertionsOnStrand(idxL, idxH)
        for insertion in insertions:
            tL += insertion.length()
        return tL
    # end def

    def insertionsOnStrand(self, idxL=None, idxH=None):
        """
        if passed indices it will use those as a bounds
        """
        insertions = []
        coord = self.virtualHelix().coord()
        insertionsDict = self.part().insertions()[coord]
        sortedIndices = sorted(insertionsDict.keys())
        if idxL == None:
            idxL, idxH = self.idxs()
        for index in sortedIndices:
            insertion = insertionsDict[index]
            if idxL <= insertion.idx() <= idxH:
                insertions.append(insertion)
            # end if
        # end for
        return insertions
    # end def

    def length(self):
        return self._baseIdxHigh - self._baseIdxLow + 1
    # end def

    def totalLength(self):
        """
        includes the length of insertions in addition to the bases
        """
        tL = 0
        insertions = self.insertionsOnStrand()

        for insertion in insertions:
            tL += insertion.length()
        return tL + self.length()
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def addDecorators(self, additionalDecorators):
        """Used to add decorators during a merge operation."""
        self._decorators.update(additionalDecorators)
    # end def

    def addInsertion(self, idx, length, useUndoStack=True):
        """
        Adds an insertion or skip at idx.
        length should be
            >0 for an insertion
            -1 for a skip
        """
        cmds = []
        idxLow, idxHigh = self.idxs()
        if idxLow <= idx <= idxHigh:
            if not self.hasInsertionAt(idx):
                # make sure length is -1 if a skip
                if length < 0:
                    length = -1
                if useUndoStack:
                    cmds.append(self.oligo().applySequenceCMD(None, useUndoStack=useUndoStack))
                    for strand in self.getComplementStrands():
                        cmds.append(strand.oligo().applySequenceCMD(None, useUndoStack=useUndoStack))
                cmds.append(Strand.AddInsertionCommand(self, idx, length))
                util.execCommandList(self, cmds, desc="Add Insertion",
                                     useUndoStack=useUndoStack)
            # end if
        # end if
    # end def

    def changeInsertion(self, idx, length, useUndoStack=True):
        cmds = []
        idxLow, idxHigh = self.idxs()
        if idxLow <= idx <= idxHigh:
            if self.hasInsertionAt(idx):
                if length == 0:
                    self.removeInsertion(idx)
                else:
                    # make sure length is -1 if a skip
                    if length < 0:
                        length = -1
                    cmds.append(self.oligo().applySequenceCMD(None, useUndoStack=useUndoStack))
                    for strand in self.getComplementStrands():
                        cmds.append(strand.oligo().applySequenceCMD(None, useUndoStack=useUndoStack))
                    cmds.append(
                            Strand.ChangeInsertionCommand(self, idx, length))
                    util.execCommandList(
                                        self, cmds, desc="Change Insertion",
                                        useUndoStack=useUndoStack)
            # end if
        # end if
    # end def
    
    def removeInsertion(self,  idx, useUndoStack=True):
        cmds = []
        idxLow, idxHigh = self.idxs()
        if idxLow <= idx <= idxHigh:
            if self.hasInsertionAt(idx):
                cmds.append(self.oligo().applySequenceCMD(None, useUndoStack=useUndoStack))
                for strand in self.getComplementStrands():
                    cmds.append(strand.oligo().applySequenceCMD(None, useUndoStack=useUndoStack))
                cmds.append(Strand.RemoveInsertionCommand(self, idx))
                util.execCommandList(
                                    self, cmds, desc="Remove Insertion",
                                    useUndoStack=useUndoStack)
            # end if
        # end if
    # end def

    def destroy(self):
        self.setParent(None)
        self.deleteLater()  # QObject also emits a destroyed() Signal
    # end def

    def merge(self, idx):
        """Check for neighbor, then merge if possible."""
        lowNeighbor, highNeighbor = self._strandSet.getNeighbors(self)
        # determine where to check for neighboring endpoint
        if idx == self._baseIdxLow:
            if lowNeighbor:
                if lowNeighbor.highIdx() == idx - 1:
                    self._strandSet.mergeStrands(self, lowNeighbor)
        elif idx == self._baseIdxHigh:
            if highNeighbor:
                if highNeighbor.lowIdx() == idx + 1:
                    self._strandSet.mergeStrands(self, highNeighbor)
        else:
            raise IndexError
    # end def

    def resize(self, newIdxs, useUndoStack=True):
        cmds = []
        if self.strandSet().isScaffold():
            cmds.append(self.oligo().applySequenceCMD(None))
        cmds += self.getRemoveInsertionCommands(newIdxs)
        cmds.append(Strand.ResizeCommand(self, newIdxs))
        util.execCommandList(
                            self, cmds, desc="Resize strand",
                            useUndoStack=useUndoStack)
    # end def

    def setConnection3p(self, strand):
        self._strand3p = strand
    # end def

    def setConnection5p(self, strand):
        self._strand5p = strand
    # end def

    def setIdxs(self, idxs):
        self._baseIdxLow = idxs[0]
        self._baseIdxHigh = idxs[1]
    # end def

    def setOligo(self, newOligo, emitSignal=True):
        self._oligo = newOligo
        if emitSignal:
            self.strandHasNewOligoSignal.emit(self)
    # end def

    def setStrandSet(self, strandSet):
        self._strandSet = strandSet
    # end def

    def split(self, idx, updateSequence=True):
        """Called by view items to split this strand at idx."""
        self._strandSet.splitStrand(self, idx, updateSequence)

    def updateIdxs(self, delta):
        self._baseIdxLow += delta
        self._baseIdxHigh += delta
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def getRemoveInsertionCommands(self, newIdxs):
        """
        Removes Insertions, Decorators, and Modifiers that have fallen out of
        range of newIdxs.

        For insertions, it finds the ones that have neither Staple nor Scaffold
        strands at the insertion idx as a result of the change of this
        strand to newIdxs

        """
        decs = self._decorators
        mods = self._modifiers
        cIdxL, cIdxH = self.idxs()
        nIdxL, nIdxH = newIdxs

        lowOut, highOut = False, False
        insertions = []
        if cIdxL < nIdxL < cIdxH:
            idxL, idxH = cIdxL, nIdxL - 1
            insertions += self.insertionsOnStrand(idxL, idxH)
        else:
            lowOut = True
        if cIdxL < nIdxH < cIdxH:
            idxL, idxH = nIdxH + 1, cIdxH
            insertions += self.insertionsOnStrand(idxL, idxH)
        else:
            highOut = True
        # this only called if both the above aren't true
        # if lowOut and highOut:
        # if we move the whole strand, just clear the insertions out
        if nIdxL > cIdxH or nIdxH < cIdxL:
            idxL, idxH = cIdxL, cIdxH
            insertions += self.insertionsOnStrand(idxL, idxH)
            # we stretched in this direction

        return self.clearInsertionsCommands(insertions, cIdxL, cIdxH)
    # end def

    def clearInsertionsCommands(self, insertions, idxL, idxH):
        """
        clear out insertions in this range
        """
        commands = []
        compSS = self.strandSet().complementStrandSet()

        overlappingStrandList = compSS.getOverlappingStrands(idxL, idxH)
        for insertion in insertions:
            idx = insertion.idx()
            removeMe = True
            for strand in overlappingStrandList:
                overLapIdxL, overLapIdxH = strand.idxs()
                if overLapIdxL <= idx <= overLapIdxH:
                    removeMe = False
                # end if
            # end for
            if removeMe:
                commands.append(Strand.RemoveInsertionCommand(self, idx))
            else:
                pass
                # print "keeping %s insertion at %d" % (self, key)
        # end for

        ### ADD CODE HERE TO HANDLE DECORATORS AND MODIFIERS
        return commands
    # end def

    def clearDecoratorCommands(self):
        insertions = self.insertionsOnStrand()
        return self.clearInsertionsCommands(insertions, *self.idxs())
    # end def

    def hasDecoratorAt(self, idx):
        return idx in self._decorators
    # end def

    def hasInsertion(self):
        """
        Iterate through dict of insertions for this strand's virtualhelix
        and return True of any of the indices overlap with the strand.
        """
        coord = self.virtualHelix().coord()
        insts = self.part().insertions()[coord]
        for i in range(self._baseIdxLow, self._baseIdxHigh+1):
            if i in insts:
                return True
        return False
    # end def

    def hasInsertionAt(self, idx):
        coord = self.virtualHelix().coord()
        insts = self.part().insertions()[coord]
        return idx in insts
    # end def

    def hasModifierAt(self, idx):
        return idx in self._modifiers
    # end def

    def shallowCopy(self):
        """
        can't use python module 'copy' as the dictionary _decorators
        needs to be shallow copied as well, but wouldn't be if copy.copy()
        is used, and copy.deepcopy is undesired
        """
        nS = Strand(self._strandSet, *self.idxs())
        nS._oligo = self._oligo
        nS._strand5p = self._strand5p
        nS._strand3p = self._strand3p
        # required to shallow copy the dictionary
        nS._decorators = dict(list(self._decorators.items()))
        nS._sequence = None  # self._sequence
        return nS
    # end def

    def deepCopy(self, strandSet, oligo):
        """
        can't use python module 'copy' as the dictionary _decorators
        needs to be shallow copied as well, but wouldn't be if copy.copy()
        is used, and copy.deepcopy is undesired
        """
        nS = Strand(strandSet, *self.idxs())
        nS._oligo = oligo
        decs = nS._decorators
        for key, decOrig in self._decorators:
            decs[key] = decOrig.deepCopy()
        # end fo
        nS._sequence = self._sequence
        return nS
    # end def

    ### COMMANDS ###
    class ResizeCommand(QUndoCommand):
        def __init__(self, strand, newIdxs):
            super(Strand.ResizeCommand, self).__init__()
            self.strand = strand
            self.oldIndices = oI = strand.idxs()
            self.newIdxs = newIdxs
            # an increase in length leads to positive delta
            self.delta = (newIdxs[1] - newIdxs[0]) - (oI[1] - oI[0])
            # now handle insertion deltas
            oldInsertions = strand.insertionsOnStrand(*oI)
            newInsertions = strand.insertionsOnStrand(*newIdxs)
            oL = 0
            for i in oldInsertions:
                oL += i.length()
            nL = 0
            for i in newInsertions:
                nL += i.length()
            self.delta += (nL-oL)

            # the strand sequence will need to be regenerated from scratch
            # as there are no guarantees about the entirety of the strand moving
            # thanks to multiple selections
        # end def

        def redo(self):
            std = self.strand
            nI = self.newIdxs
            strandSet = self.strand.strandSet()
            part = strandSet.part()

            std.oligo().incrementLength(self.delta)
            std.setIdxs(nI)
            if strandSet.isStaple():
                
                std.reapplySequence()
            std.strandResizedSignal.emit(std, nI)
            # for updating the Slice View displayed helices
            part.partStrandChangedSignal.emit(part, strandSet.virtualHelix())
            std5p = std.connection5p()
            if std5p:
                std5p.strandResizedSignal.emit(std5p, std5p.idxs())
        # end def

        def undo(self):
            std = self.strand
            oI = self.oldIndices
            strandSet = self.strand.strandSet()
            part = strandSet.part()

            std.oligo().decrementLength(self.delta)
            std.setIdxs(oI)
            if strandSet.isStaple():
                std.reapplySequence()
            std.strandResizedSignal.emit(std, oI)
            # for updating the Slice View displayed helices
            part.partStrandChangedSignal.emit(part, strandSet.virtualHelix())
            std5p = std.connection5p()
            if std5p:
                std5p.strandResizedSignal.emit(std5p, std5p.idxs())
        # end def
    # end class

    class AddInsertionCommand(QUndoCommand):
        def __init__(self, strand, idx, length):
            super(Strand.AddInsertionCommand, self).__init__()
            self._strand = strand
            coord = strand.virtualHelix().coord()
            self._insertions = strand.part().insertions()[coord]
            self._idx = idx
            self._length = length
            self._insertion = Insertion(idx, length)
            self._compStrand = \
                        strand.strandSet().complementStrandSet().getStrand(idx)
        # end def

        def redo(self):
            strand = self._strand
            cStrand = self._compStrand
            inst = self._insertion
            self._insertions[self._idx] = inst
            strand.oligo().incrementLength(inst.length())
            strand.strandInsertionAddedSignal.emit(strand, inst)
            if cStrand:
                cStrand.oligo().incrementLength(inst.length())
                cStrand.strandInsertionAddedSignal.emit(cStrand, inst)
        # end def

        def undo(self):
            strand = self._strand
            cStrand = self._compStrand
            inst = self._insertion
            strand.oligo().decrementLength(inst.length())
            if cStrand:
                cStrand.oligo().decrementLength(inst.length())
            idx = self._idx
            del self._insertions[idx]
            strand.strandInsertionRemovedSignal.emit(strand, idx)
            if cStrand:
                cStrand.strandInsertionRemovedSignal.emit(cStrand, idx)
        # end def
    # end class

    class RemoveInsertionCommand(QUndoCommand):
        def __init__(self, strand, idx):
            super(Strand.RemoveInsertionCommand, self).__init__()
            self._strand = strand
            self._idx = idx
            coord = strand.virtualHelix().coord()
            self._insertions = strand.part().insertions()[coord]
            self._insertion = self._insertions[idx]
            self._compStrand = \
                        strand.strandSet().complementStrandSet().getStrand(idx)
        # end def

        def redo(self):
            strand = self._strand
            cStrand = self._compStrand
            inst = self._insertion
            strand.oligo().decrementLength(inst.length())
            if cStrand:
                cStrand.oligo().decrementLength(inst.length())
            idx = self._idx
            del self._insertions[idx]
            strand.strandInsertionRemovedSignal.emit(strand, idx)
            if cStrand:
                cStrand.strandInsertionRemovedSignal.emit(cStrand, idx)
        # end def

        def undo(self):
            strand = self._strand
            cStrand = self._compStrand
            coord = strand.virtualHelix().coord()
            inst = self._insertion
            strand.oligo().incrementLength(inst.length())
            self._insertions[self._idx] = inst
            strand.strandInsertionAddedSignal.emit(strand, inst)
            if cStrand:
                cStrand.oligo().incrementLength(inst.length())
                cStrand.strandInsertionAddedSignal.emit(cStrand, inst)
        # end def
    # end class

    class ChangeInsertionCommand(QUndoCommand):
        """
        Changes the length of an insertion to a non-zero value
        the caller of this needs to handle the case where a zero length
        is required and call RemoveInsertionCommand
        """
        def __init__(self, strand, idx, newLength):
            super(Strand.ChangeInsertionCommand, self).__init__()
            self._strand = strand
            coord = strand.virtualHelix().coord()
            self._insertions = strand.part().insertions()[coord]
            self._idx = idx
            self._newLength = newLength
            self._oldLength = self._insertions[idx].length()
            self._compStrand = \
                        strand.strandSet().complementStrandSet().getStrand(idx)
        # end def

        def redo(self):
            strand = self._strand
            cStrand = self._compStrand
            inst = self._insertions[self._idx]
            inst.setLength(self._newLength)
            strand.oligo().incrementLength(self._newLength - self._oldLength)
            strand.strandInsertionChangedSignal.emit(strand, inst)
            if cStrand:
                cStrand.oligo().incrementLength(
                                            self._newLength - self._oldLength)
                cStrand.strandInsertionChangedSignal.emit(cStrand, inst)
        # end def

        def undo(self):
            strand = self._strand
            cStrand = self._compStrand
            inst = self._insertions[self._idx]
            inst.setLength(self._oldLength)
            strand.oligo().decrementLength(self._newLength - self._oldLength)
            strand.strandInsertionChangedSignal.emit(strand, inst)
            if cStrand:
                cStrand.oligo().decrementLength(
                                            self._newLength - self._oldLength)
                cStrand.strandInsertionChangedSignal.emit(cStrand, inst)
        # end def
    # end class
# end class
