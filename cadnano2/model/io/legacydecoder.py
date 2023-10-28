from collections import defaultdict

from cadnano2.model.document import Document
from cadnano2.model.enum import LatticeType, StrandType
from cadnano2.model.parts.honeycombpart import HoneycombPart
from cadnano2.model.parts.squarepart import SquarePart
from cadnano2.model.virtualhelix import VirtualHelix
from cadnano2.views import styles
import cadnano2.util as util
import cadnano2.cadnano as cadnano
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtGui', globals(),  ['QColor'])
if cadnano.app().isGui():
    from cadnano2.ui.dialogs.ui_latticetype import Ui_LatticeType
    util.qtWrapImport('QtWidgets', globals(),  ['QDialog', 'QDialogButtonBox'])

NODETAG = "node"
NAME = "name"
OBJ_ID = "objectid"
INST_ID = "instanceid"
DONE = "done"
CHECKED = "check"
LOCKED = "locked"

VHELIX = "vhelix"
NUM = "num"
COL = "col"
ROW = "row"
SCAFFOLD = "scaffold"
STAPLE = "staple"
INSERTION = "insertion"
DELETION = "deletion"


def import_legacy_dict(document, obj, latticeType=LatticeType.Honeycomb):
    """
    Parses a dictionary (obj) created from reading a json file and uses it
    to populate the given document with model data.
    """
    numBases = len(obj['vstrands'][0]['scaf'])
    if cadnano.app().isGui():
        # from ui.dialogs.ui_latticetype import Ui_LatticeType
        # util.qtWrapImport('QtGui', globals(),  ['QDialog', 'QDialogButtonBox'])
        dialog = QDialog()
        dialogLT = Ui_LatticeType()
        dialogLT.setupUi(dialog)
        # DETERMINE LATTICE TYPE
        if numBases % 21 == 0 and numBases % 32 == 0:
            if dialog.exec() == 1:
                latticeType = LatticeType.Square
            else:
                latticeType = LatticeType.Honeycomb
        elif numBases % 32 == 0:
            latticeType = LatticeType.Square
        elif numBases % 21 == 0:
            latticeType = LatticeType.Honeycomb
        else:
            if dialog.exec() == 1:
                latticeType = LatticeType.Square
            else:
                latticeType = LatticeType.Honeycomb
    else:  # Headless, assume the latticeType arg was meaningful
        pass

    # DETERMINE MAX ROW,COL
    maxRowJson = maxColJson = 0
    for helix in obj['vstrands']:
        maxRowJson = max(maxRowJson, int(helix['row'])+1)
        maxColJson = max(maxColJson, int(helix['col'])+1)

    # CREATE PART ACCORDING TO LATTICE TYPE
    if latticeType == LatticeType.Honeycomb:
        steps = numBases/21
        nRows = max(30, maxRowJson, cadnano.app().prefs.honeycombRows)
        nCols = max(32, maxColJson, cadnano.app().prefs.honeycombCols)
        part = HoneycombPart(document=document, maxRow=nRows, maxCol=nCols, maxSteps=steps)
    elif latticeType == LatticeType.Square:
        isSQ100 = True  # check for custom SQ100 format
        for helix in obj['vstrands']:
            if helix['col'] != 0:
                isSQ100 = False
                break
        if isSQ100:
            dialogLT.label.setText("Is this a SQ100 file?")
            if dialog.exec() == 1:
                nRows, nCols = 100, 1
            else:
                nRows, nCols = 40, 30
        else:
            nRows, nCols = 40, 30
        steps = numBases/32
        nRows = max(30, maxRowJson, cadnano.app().prefs.squareRows)
        nCols = max(32, maxColJson, cadnano.app().prefs.squareCols)
        part = SquarePart(document=document, maxRow=nRows, maxCol=nCols, maxSteps=steps)
    else:
        raise TypeError("Lattice type not recognized")
    document._addPart(part, useUndoStack=False)

    # POPULATE VIRTUAL HELICES
    orderedCoordList = []
    vhNumToCoord = {}
    for helix in obj['vstrands']:
        vhNum = helix['num']
        row = helix['row']
        col = helix['col']
        scaf= helix['scaf']
        coord = (row, col)
        vhNumToCoord[vhNum] = coord
        orderedCoordList.append(coord)
    # make sure we retain the original order
    for vhNum in sorted(vhNumToCoord.keys()):
        row, col = vhNumToCoord[vhNum]
        part.createVirtualHelix(row, col, useUndoStack=False)
    part.setImportedVHelixOrder(orderedCoordList)

    # INSTALL STRANDS AND COLLECT XOVER LOCATIONS
    numHelixes = len(obj['vstrands'])-1
    scaf_seg = defaultdict(list)
    scaf_xo = defaultdict(list)
    stap_seg = defaultdict(list)
    stap_xo = defaultdict(list)
    try:
        for helix in obj['vstrands']:
            vhNum = helix['num']
            row = helix['row']
            col = helix['col']
            scaf = helix['scaf']
            stap = helix['stap']
            insertions = helix['loop']
            skips = helix['skip']
            vh = part.virtualHelixAtCoord((row, col))
            scafStrandSet = vh.scaffoldStrandSet()
            stapStrandSet = vh.stapleStrandSet()
            assert(len(scaf)==len(stap) and len(stap)==part.maxBaseIdx()+1 and\
                   len(scaf)==len(insertions) and len(insertions)==len(skips))
            # read scaffold segments and xovers
            for i in range(len(scaf)):
                fiveVH, fiveIdx, threeVH, threeIdx = scaf[i]
                if fiveVH == -1 and threeVH == -1:
                    continue  # null base
                if isSegmentStartOrEnd(StrandType.Scaffold, vhNum, i, fiveVH,\
                                       fiveIdx, threeVH, threeIdx):
                    scaf_seg[vhNum].append(i)
                if fiveVH != vhNum and threeVH != vhNum:  # special case
                    scaf_seg[vhNum].append(i)  # end segment on a double crossover
                if is3primeXover(StrandType.Scaffold, vhNum, i, threeVH, threeIdx):
                    scaf_xo[vhNum].append((i, threeVH, threeIdx))
            assert (len(scaf_seg[vhNum]) % 2 == 0)
            # install scaffold segments
            for i in range(0, len(scaf_seg[vhNum]), 2):
                lowIdx = scaf_seg[vhNum][i]
                highIdx = scaf_seg[vhNum][i+1]
                scafStrandSet.createStrand(lowIdx, highIdx, useUndoStack=False)
            # read staple segments and xovers
            for i in range(len(stap)):
                fiveVH, fiveIdx, threeVH, threeIdx = stap[i]
                if fiveVH == -1 and threeVH == -1:
                    continue  # null base
                if isSegmentStartOrEnd(StrandType.Staple, vhNum, i, fiveVH,\
                                       fiveIdx, threeVH, threeIdx):
                    stap_seg[vhNum].append(i)
                if fiveVH != vhNum and threeVH != vhNum:  # special case
                    stap_seg[vhNum].append(i)  # end segment on a double crossover
                if is3primeXover(StrandType.Staple, vhNum, i, threeVH, threeIdx):
                    stap_xo[vhNum].append((i, threeVH, threeIdx))
            assert (len(stap_seg[vhNum]) % 2 == 0)
            # install staple segments
            for i in range(0, len(stap_seg[vhNum]), 2):
                lowIdx = stap_seg[vhNum][i]
                highIdx = stap_seg[vhNum][i+1]
                stapStrandSet.createStrand(lowIdx, highIdx, useUndoStack=False)
    except AssertionError:
        if not cadnano.app().isGui():
            print("Unrecognized file format.")
        else:
            dialogLT.label.setText("Unrecognized file format.")
            dialogLT.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Ok)
            dialog.exec()

    # INSTALL XOVERS
    for helix in obj['vstrands']:
        vhNum = helix['num']
        row = helix['row']
        col = helix['col']
        scaf = helix['scaf']
        stap = helix['stap']
        insertions = helix['loop']
        skips = helix['skip']
        fromVh = part.virtualHelixAtCoord((row, col))
        scafStrandSet = fromVh.scaffoldStrandSet()
        stapStrandSet = fromVh.stapleStrandSet()
        # install scaffold xovers
        for (idx5p, toVhNum, idx3p) in scaf_xo[vhNum]:
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            strand5p = scafStrandSet.getStrand(idx5p)
            toVh = part.virtualHelixAtCoord(vhNumToCoord[toVhNum])
            strand3p = toVh.scaffoldStrandSet().getStrand(idx3p)
            part.createXover(strand5p, idx5p, strand3p, idx3p, useUndoStack=False)
        # install staple xovers
        for (idx5p, toVhNum, idx3p) in stap_xo[vhNum]:
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            strand5p = stapStrandSet.getStrand(idx5p)
            toVh = part.virtualHelixAtCoord(vhNumToCoord[toVhNum])
            strand3p = toVh.stapleStrandSet().getStrand(idx3p)
            part.createXover(strand5p, idx5p, strand3p, idx3p, useUndoStack=False)

    # SET DEFAULT COLOR
    for oligo in part.oligos():
        if oligo.isStaple():
            defaultColor = styles.DEFAULT_STAP_COLOR
        else:
            defaultColor = styles.DEFAULT_SCAF_COLOR
        oligo.applyColor(defaultColor, useUndoStack=False)

    # COLORS, INSERTIONS, SKIPS
    for helix in obj['vstrands']:
        vhNum = helix['num']
        row = helix['row']
        col = helix['col']
        scaf = helix['scaf']
        stap = helix['stap']
        insertions = helix['loop']
        skips = helix['skip']
        vh = part.virtualHelixAtCoord((row, col))
        scafStrandSet = vh.scaffoldStrandSet()
        stapStrandSet = vh.stapleStrandSet()
        # install insertions and skips
        for baseIdx in range(len(stap)):
            sumOfInsertSkip = insertions[baseIdx] + skips[baseIdx]
            if sumOfInsertSkip != 0:
                scaf_strand = scafStrandSet.getStrand(baseIdx)
                stap_strand = stapStrandSet.getStrand(baseIdx)
                if scaf_strand:
                    scaf_strand.addInsertion(baseIdx, sumOfInsertSkip, useUndoStack=False)
                elif stap_strand:
                    stap_strand.addInsertion(baseIdx, sumOfInsertSkip, useUndoStack=False)

        # populate staple colors
        for baseIdx, colorNumber in helix['stap_colors']:
            color = QColor((colorNumber>>16)&0xFF, (colorNumber>>8)&0xFF, colorNumber&0xFF).name()
            strand = stapStrandSet.getStrand(baseIdx)
            strand.oligo().applyColor(color, useUndoStack=False)

        # populate scaffold colors, if any
        if 'scaf_colors' in helix:
            for baseIdx, colorNumber in helix['scaf_colors']:
                color = QColor((colorNumber>>16)&0xFF, (colorNumber>>8)&0xFF, colorNumber&0xFF).name()
                strand = scafStrandSet.getStrand(baseIdx)
                strand.oligo().applyColor(color, useUndoStack=False)

def isSegmentStartOrEnd(strandType, vhNum, baseIdx, fiveVH, fiveIdx, threeVH, threeIdx):
    """Returns True if the base is a breakpoint or crossover."""
    if strandType == StrandType.Scaffold:
        offset = 1
    else:
        offset = -1
    if (fiveVH == vhNum and threeVH != vhNum):
        return True
    if (fiveVH != vhNum and threeVH == vhNum):
        return True
    if (vhNum % 2 == 0 and fiveVH == vhNum and fiveIdx != baseIdx-offset):
        return True
    if (vhNum % 2 == 0 and threeVH == vhNum and threeIdx != baseIdx+offset):
        return True
    if (vhNum % 2 == 1 and fiveVH == vhNum and fiveIdx != baseIdx+offset):
        return True
    if (vhNum % 2 == 1 and threeVH == vhNum and threeIdx != baseIdx-offset):
        return True
    if (fiveVH == -1 and threeVH != -1):
        return True
    if (fiveVH != -1 and threeVH == -1):
        return True
    return False

def is3primeXover(strandType, vhNum, baseIdx, threeVH, threeIdx):
    """Returns True of the threeVH doesn't match vhNum, or threeIdx
    is not a natural neighbor of baseIdx."""
    if threeVH == -1:
        return False
    if vhNum != threeVH:
        return True
    if strandType == StrandType.Scaffold:
        offset = 1
    else:
        offset = -1
    if (vhNum % 2 == 0 and threeVH == vhNum and threeIdx != baseIdx+offset):
        return True
    if (vhNum % 2 == 1 and threeVH == vhNum and threeIdx != baseIdx-offset):
        return True
    return False
