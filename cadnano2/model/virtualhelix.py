#!/usr/bin/env python
# encoding: utf-8

from .strandset import StrandSet
import cadnano2.util as util
from .enum import StrandType

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QUndoStack', 'QUndoCommand'])


class VirtualHelix(QObject):
    """
    VirtualHelix is a container class for two StrandSet objects (one scaffold
    and one staple). The Strands all share the same helix axis. It is called
    "virtual" because many different Strands (i.e. sub-oligos) combine to
    form the "helix", just as many fibers may be braided together to 
    form a length of rope.
    """

    def __init__(self, part, row, col, idnum=0):
        super(VirtualHelix, self).__init__(part)
        self._coord = (row, col) # col, row
        self._part = part
        self._doc = part.document()
        self._scafStrandSet = StrandSet(StrandType.Scaffold, self)
        self._stapStrandSet = StrandSet(StrandType.Staple, self)
        # If self._part exists, it owns self._number
        # in that only it may modify it through the
        # private interface. The public interface for
        # setNumber just routes the call to the parent
        # dnapart if one is present. If self._part == None
        # the virtualhelix owns self._number and may modify it.
        self._number = None
        self.setNumber(idnum)
    # end def

    def __repr__(self):
        return "<%s(%d)>" % (self.__class__.__name__, self._number)

    ### SIGNALS ###
    virtualHelixRemovedSignal = pyqtSignal(QObject)  # self
    virtualHelixNumberChangedSignal = pyqtSignal(QObject, int)  # self, num

    ### SLOTS ###

    ### ACCESSORS ###
    def scaf(self, idx):
        """ Returns the strand at idx in self's scaffold, if any """
        return self._scafStrandSet.getStrand(idx)

    def stap(self, idx):
        """ Returns the strand at idx in self's scaffold, if any """
        return self._stapStrandSet.getStrand(idx)

    def coord(self):
        return self._coord
    # end def

    def number(self):
        return self._number
    # end def

    def part(self):
        return self._part
    # end def
    
    def document(self):
        return self._doc
    # end def
    
    def setNumber(self, number):
        if self._number != number:
            numToVhDict = self._part._numberToVirtualHelix
            numToVhDict[self._number] = None
            self._number = number
            self.virtualHelixNumberChangedSignal.emit(self, number)
            numToVhDict[number] = self
    # end def

    def setPart(self, newPart):
        self._part = newPart
        self.setParent(newPart)
    # end def

    def scaffoldStrandSet(self):
        return self._scafStrandSet
    # end def

    def stapleStrandSet(self):
        return self._stapStrandSet
    # end def

    def undoStack(self):
        return self._part.undoStack()
    # end def

    ### METHODS FOR QUERYING THE MODEL ###
    def scaffoldIsOnTop(self):
        return self.isEvenParity()

    def getStrandSetByIdx(self, idx):
        """
        This is a path-view-specific accessor
        idx == 0 means top strand
        idx == 1 means bottom strand
        """
        if idx == 0:
            if self.isEvenParity():
                return self._scafStrandSet
            else:
                return self._stapStrandSet
        else:
            if self.isEvenParity():
                return self._stapStrandSet
            else:
                return self._scafStrandSet
    # end def

    def getStrandSetByType(self, strandType):
        if strandType == StrandType.Scaffold:
            return self._scafStrandSet
        else:
            return self._stapStrandSet
    # end def

    def getStrandSets(self):
        """Return a tuple of the scaffold and staple StrandSets."""
        return self._scafStrandSet, self._stapStrandSet
    # end def

    def hasStrandAtIdx(self, idx):
        return self._scafStrandSet.hasStrandAt(idx, idx)
    # end def

    def indexOfRightmostNonemptyBase(self):
        """Returns the rightmost nonempty base in either scaf of stap."""
        return max(self._scafStrandSet.indexOfRightmostNonemptyBase(),\
                   self._stapStrandSet.indexOfRightmostNonemptyBase())
    # end def

    def isDrawn5to3(self, strandSet):
        isScaf = strandSet == self._scafStrandSet
        isEven = self.isEvenParity()
        return isEven == isScaf
    # end def

    def isEvenParity(self):
        return self._part.isEvenParity(*self._coord)
    # end def

    def strandSetBounds(self, indexHelix, indexType):
        """
        forwards the query to the strandSet
        """
        return self.strandSet(indexHelix, indexType).bounds()
    # end def

    ### METHODS FOR EDITING THE MODEL ###
    def destroy(self):
        # QObject also emits a destroyed() Signal
        self.setParent(None)
        self.deleteLater()
    # end def
    
    def remove(self, useUndoStack=True):
        """
        Removes a VirtualHelix from the model. Accepts a reference to the 
        VirtualHelix, or a (row,col) lattice coordinate to perform a lookup.
        """
        if useUndoStack:
            self.undoStack().beginMacro("Delete VirtualHelix")
        self._scafStrandSet.remove(useUndoStack)
        self._stapStrandSet.remove(useUndoStack)
        c = VirtualHelix.RemoveVirtualHelixCommand(self.part(), self)
        if useUndoStack:
            self.undoStack().push(c)
            self.undoStack().endMacro()
        else:
            c.redo()
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def deepCopy(self, part):
        """
        This only copies as deep as the VirtualHelix
        strands get copied at the oligo and added to the Virtual Helix
        """
        vh = VirtualHelix(part, self._number)
        vh._coords = (self._coord[0], self._coord[1])
        # If self._part exists, it owns self._number
        # in that only it may modify it through the
        # private interface. The public interface for
        # setNumber just routes the call to the parent
        # dnapart if one is present. If self._part == None
        # the virtualhelix owns self._number and may modify it.
        self._number = idnum
    # end def

    def getLegacyStrandSetArray(self, strandType):
        """Called by legacyencoder."""
        if strandType == StrandType.Scaffold:
            return self._scafStrandSet.getLegacyArray()
        else:
            return self._stapStrandSet.getLegacyArray()

    def shallowCopy(self):
        pass
    # end def

    # def translateCoords(self, deltaCoords):
    #     """
    #     for expanding a helix
    #     """
    #     deltaRow, deltaCol = deltaCoords
    #     row, col = self._coord
    #     self._coord = row + deltaRow, col + deltaCol
    # # end def

    class RemoveVirtualHelixCommand(QUndoCommand):
        """Inserts strandToAdd into strandList at index idx."""
        def __init__(self, part, virtualHelix):
            super(VirtualHelix.RemoveVirtualHelixCommand, self).__init__()
            self._part = part
            self._vhelix = virtualHelix
            self._idNum = virtualHelix.number()
            # is the number even or odd?  Assumes a valid idNum, row,col combo
            self._parityEven = (self._idNum % 2) == 0
            
        # end def

        def redo(self):
            vh = self._vhelix
            part = self._part
            idNum = self._idNum
            
            part._removeVirtualHelix(vh)
            part._recycleHelixIDNumber(idNum)
            # clear out part references
            vh.virtualHelixRemovedSignal.emit(vh)
            part.partActiveSliceResizeSignal.emit(part)
            # vh.setPart(None)
            # vh.setNumber(None)
        # end def

        def undo(self):
            vh = self._vhelix
            part = self._part
            idNum = self._idNum
            
            vh.setPart(part)
            part._addVirtualHelix(vh)
            # vh.setNumber(idNum)
            if not vh.number():
                part._reserveHelixIDNumber(self._parityEven, requestedIDnum=idNum)
            part.partVirtualHelixAddedSignal.emit(part, vh)
            part.partActiveSliceResizeSignal.emit(part)
        # end def
    # end class