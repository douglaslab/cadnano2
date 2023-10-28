#!/usr/bin/env python
# encoding: utf-8

import cadnano2.util as util
import copy
from .strand import Strand
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject'])
util.qtWrapImport('QtGui', globals(), ['QUndoCommand'])


class Oligo(QObject):
    """
    Oligo is a group of Strands that are connected via 5' and/or 3'
    connections. It corresponds to the physical DNA strand, and is thus
    used tracking and storing properties that are common to a single strand,
    such as its color.

    Commands that affect Strands (e.g. create, remove, merge, split) are also
    responsible for updating the affected Oligos.
    """
    def __init__(self, part, color=None):
        super(Oligo, self).__init__(part)
        self._part = part
        self._strand5p = None
        self._length = 0
        self._isLoop = False
        self._color = color if color else "#0066cc"
    # end def

    def __repr__(self):
        clsName = self.__class__.__name__
        olgId = str(id(self))[-4:]
        strandType = "Stap" if self.isStaple() else "Scaf"
        vhNum = self._strand5p.strandSet().virtualHelix().number()
        idx = self._strand5p.idx5Prime()
        return "<%s %s>(%s %d[%d])" % (clsName, olgId, strandType, vhNum, idx)

    def shallowCopy(self):
        olg = Oligo(self._part)
        olg._strand5p = self._strand5p
        olg._length = self._length
        olg._isLoop = self._isLoop
        olg._color = self._color
        return olg
    # end def

    def deepCopy(self, part):
        olg = Oligo(part)
        olg._strand5p = None
        olg._length = self._length
        olg._isLoop = self._isLoop
        olg._color = self._color
        return olg
    # end def

    ### SIGNALS ###
    oligoIdentityChangedSignal = pyqtSignal(QObject)  # new oligo
    oligoAppearanceChangedSignal = pyqtSignal(QObject)  # self
    oligoSequenceAddedSignal = pyqtSignal(QObject)  # self
    oligoSequenceClearedSignal = pyqtSignal(QObject)  # self

    ### SLOTS ###

    ### ACCESSORS ###
    def color(self):
        return self._color
    # end def

    def locString(self):
        vhNum = self._strand5p.strandSet().virtualHelix().number()
        idx = self._strand5p.idx5Prime()
        return "%d[%d]" % (vhNum, idx)
    # end def

    def part(self):
        return self._part
    # end def

    def strand5p(self):
        return self._strand5p
    # end def

    def setStrand5p(self, strand):
        self._strand5p = strand
    # end def

    def undoStack(self):
        return self._part.undoStack()
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def isLoop(self): # isCircular
        return self._isLoop

    def isStaple(self):
        return self._strand5p.isStaple()

    def length(self):
        return self._length
    # end def

    def sequence(self):
        temp = self.strand5p()
        if not temp:
            return None
        if temp.sequence():
            return ''.join([Strand.sequence(strand) \
                        for strand in self.strand5p().generator3pStrand()])
        else:
            return None
    # end def

    def sequenceExport(self):
        vhNum5p = self.strand5p().virtualHelix().number()
        idx5p = self.strand5p().idx5Prime()
        seq = ''
        if self.isLoop():
            # print "A loop exists"
            raise Exception
        for strand in self.strand5p().generator3pStrand():
            seq = seq + Strand.sequence(strand, forExport=True)
            if strand.connection3p() == None:  # last strand in the oligo
                vhNum3p = strand.virtualHelix().number()
                idx3p = strand.idx3Prime()
        output = "%d[%d],%d[%d],%s,%s,%s\n" % \
                (vhNum5p, idx5p, vhNum3p, idx3p, seq, len(seq), self._color)
        return output
    # end def

    def shouldHighlight(self):
        if not self._strand5p:
            return False
        if self._strand5p.isScaffold():
            return False
        if self.length() < 18:
            return True
        if self.length() > 50:
            return True
        return False
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def remove(self, useUndoStack=True):
        c = Oligo.RemoveOligoCommand(self)
        util.execCommandList(self, [c], desc="Color Oligo", useUndoStack=useUndoStack)
    # end def

    def applyColor(self, color, useUndoStack=True):
        if color == self._color:
            return  # oligo already has color
        c = Oligo.ApplyColorCommand(self, color)
        util.execCommandList(self, [c], desc="Color Oligo", useUndoStack=useUndoStack)
    # end def

    def applySequence(self, sequence, useUndoStack=True):
        c = Oligo.ApplySequenceCommand(self, sequence)
        util.execCommandList(self, [c], desc="Apply Sequence", useUndoStack=useUndoStack)
    # end def

    def applySequenceCMD(self, sequence, useUndoStack=True):
        return Oligo.ApplySequenceCommand(self, sequence)
    # end def

    def setLoop(self, bool):
        self._isLoop = bool

    ### PUBLIC SUPPORT METHODS ###
    def addToPart(self, part):
        self._part = part
        self.setParent(part)
        part.addOligo(self)
    # end def

    def destroy(self):
        # QObject also emits a destroyed() Signal
        self.setParent(None)
        self.deleteLater()
    # end def

    def decrementLength(self, delta):
        self.setLength(self._length-delta)
    # end def

    def incrementLength(self, delta):
        self.setLength(self._length+delta)
    # end def

    def refreshLength(self):
        temp = self.strand5p()
        if not temp:
            return
        length = 0
        for strand in temp.generator3pStrand():
            length += strand.totalLength()
        self.setLength(length)
    # end def

    def removeFromPart(self):
        """
        This method merely disconnects the object from the model.
        It still lives on in the undoStack until clobbered

        Note: don't set self._part = None because we need to continue passing
        the same reference around.
        """
        self._part.removeOligo(self)
        self.setParent(None)
    # end def

    def setColor(self, color):
        self._color = color
    # end def

    def setLength(self, length):
        before = self.shouldHighlight()
        self._length = length
        if before != self.shouldHighlight():
            self.oligoSequenceClearedSignal.emit(self)
            self.oligoAppearanceChangedSignal.emit(self)
    # end def

    def strandMergeUpdate(self, oldStrandLow, oldStrandHigh, newStrand):
        """
        This method sets the isLoop status of the oligo and the oligo's
        5' strand.
        """
        # check loop status
        if oldStrandLow.oligo() == oldStrandHigh.oligo():
            self._isLoop = True
            self._strand5p = newStrand
            return 
            # leave the _strand5p as is?
        # end if

        # Now get correct 5p end to oligo
        if oldStrandLow.isDrawn5to3():
            if oldStrandLow.connection5p() != None:
                self._strand5p = oldStrandLow.oligo()._strand5p
            else:
                self._strand5p = newStrand
        else:
            if oldStrandHigh.connection5p() != None:
                self._strand5p = oldStrandHigh.oligo()._strand5p
            else:
                self._strand5p = newStrand
        # end if
    # end def

    def strandResized(self, delta):
        """
        Called by a strand after resize. Delta is used to update the length,
        which may case an appearance change.
        """
        pass
    # end def

    def strandSplitUpdate(self, newStrand5p, newStrand3p, oligo3p, oldMergedStrand):
        """
        If the oligo is a loop, splitting the strand does nothing. If the
        oligo isn't a loop, a new oligo must be created and assigned to the
        newStrand and everything connected to it downstream.
        """
        # if you split it can't be a loop
        self._isLoop = False
        if oldMergedStrand.oligo().isLoop():
            self._strand5p = newStrand3p
            return
        else:
            if oldMergedStrand.connection5p() == None:
                self._strand5p = newStrand5p
            else:
                self._strand5p = oldMergedStrand.oligo()._strand5p
            oligo3p._strand5p = newStrand3p
        # end else
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### COMMANDS ###
    class ApplyColorCommand(QUndoCommand):
        def __init__(self, oligo, color):
            super(Oligo.ApplyColorCommand, self).__init__()
            self._oligo = oligo
            self._newColor = color
            self._oldColor = oligo.color()
        # end def

        def redo(self):
            olg = self._oligo
            olg.setColor(self._newColor)
            olg.oligoAppearanceChangedSignal.emit(olg)
        # end def

        def undo(self):
            olg = self._oligo
            olg.setColor(self._oldColor)
            olg.oligoAppearanceChangedSignal.emit(olg)
        # end def
    # end class

    class ApplySequenceCommand(QUndoCommand):
        def __init__(self, oligo, sequence):
            super(Oligo.ApplySequenceCommand, self).__init__()
            self._oligo = oligo
            self._newSequence = sequence
            self._oldSequence = oligo.sequence()
            self._strandType = oligo._strand5p.strandSet().strandType()
        # end def

        def redo(self):
            olg = self._oligo
            nS = ''.join(self._newSequence) if self._newSequence else None
            nS_original = self._newSequence
            oligoList = [olg]
            for strand in olg.strand5p().generator3pStrand():
                usedSeq, nS = strand.setSequence(nS)
                # get the compliment ahead of time
                usedSeq = util.comp(usedSeq) if usedSeq else None
                compSS = strand.strandSet().complementStrandSet()
                for compStrand in compSS._findOverlappingRanges(strand):
                    subUsedSeq = compStrand.setComplementSequence(usedSeq, strand)
                    oligoList.append(compStrand.oligo())
                # end for
                # as long as the new Applied Sequence is not None
                if nS == None and nS_original:
                    break
            # end for
            for oligo in oligoList:
                oligo.oligoSequenceAddedSignal.emit(oligo)
        # end def

        def undo(self):
            olg = self._oligo
            oS = ''.join(self._oldSequence) if self._oldSequence else None

            oligoList = [olg]

            for strand in olg.strand5p().generator3pStrand():
                usedSeq, oS = strand.setSequence(oS)

                # get the compliment ahead of time
                usedSeq = util.comp(usedSeq) if usedSeq else None
                compSS = strand.strandSet().complementStrandSet()
                for compStrand in compSS._findOverlappingRanges(strand):
                    subUsedSeq = compStrand.setComplementSequence(usedSeq, strand)
                    oligoList.append(compStrand.oligo())
                # end for
            # for

            for oligo in oligoList:
                oligo.oligoSequenceAddedSignal.emit(oligo)
        # end def
    # end class
    class ApplyColorCommand(QUndoCommand):
        def __init__(self, oligo, color):
            super(Oligo.ApplyColorCommand, self).__init__()
            self._oligo = oligo
            self._newColor = color
            self._oldColor = oligo.color()
        # end def

        def redo(self):
            olg = self._oligo
            olg.setColor(self._newColor)
            olg.oligoAppearanceChangedSignal.emit(olg)
        # end def

        def undo(self):
            olg = self._oligo
            olg.setColor(self._oldColor)
            olg.oligoAppearanceChangedSignal.emit(olg)
        # end def
    # end class

    class RemoveOligoCommand(QUndoCommand):
        def __init__(self,oligo):
            super(Oligo.RemoveOligoCommand, self).__init__()
            self._oligo = oligo
            self._part = oligo.part()
            self._strandIdxList = []
            self._strand3p = None
        # end def

        def redo(self):
            sIList = self._strandIdxList
            o = self._oligo
            s5p = o.strand5p()
            part = self._part

            for strand in s5p.generator3pStrand():
                strandSet = strand.strandSet()
                strandSet._doc.removeStrandFromSelection(strand)
                isInSet, overlap, sSetIdx = strandSet._findIndexOfRangeFor(strand)
                sIList.append(sSetIdx)
                strandSet._strandList.pop(sSetIdx)
                # Emit a signal to notify on completion
                strand.strandRemovedSignal.emit(strand)
                # for updating the Slice View displayed helices
                strandSet.part().partStrandChangedSignal.emit(strandSet.part(), strandSet.virtualHelix())
            # end def
            # set the 3p strand for the undo
            self._strand3p = strand

            # remove Oligo from part but don't set parent to None?
            # o.removeFromPart()
            part.removeOligo(o)
        # end def

        def undo(self):
            sIList = self._strandIdxList
            o = self._oligo
            s3p = self._strand3p
            part = self._part

            for strand in s3p.generator5pStrand():
                strandSet = strand.strandSet()
                sSetIdx = sIList.pop(-1)
                strandSet._strandList.insert(sSetIdx, strand)
                # Emit a signal to notify on completion
                strandSet.strandsetStrandAddedSignal.emit(strandSet, strand)
                # for updating the Slice View displayed helices
                part.partStrandChangedSignal.emit(strandSet.part(), strandSet.virtualHelix())
            # end def

            # add Oligo to part but don't set parent to None?
            # o.addToPart(part)
            part.addOligo(o)
        # end def
    # end class
# end class
    