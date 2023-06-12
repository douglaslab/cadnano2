from os.path import basename
from cadnano2.model.enum import StrandType


def legacy_dict_from_doc(document, fname, helixOrderList):
    part = document.selectedPart()
    numBases = part.maxBaseIdx()+1

    # iterate through virtualhelix list
    vhList = []
    for row, col in helixOrderList:
        vh = part.virtualHelixAtCoord((row, col))
        # insertions and skips
        insertionDict = part.insertions()[(row, col)]
        insts = [0 for i in range(numBases)]
        skips = [0 for i in range(numBases)]
        for idx, insertion in insertionDict.items():
            if insertion.isSkip():
                skips[idx] = insertion.length()
            else:
                insts[idx] = insertion.length()
        # colors
        stapColors = []
        stapStrandSet = vh.stapleStrandSet()
        for strand in stapStrandSet:
            if strand.connection5p() is None:
                c = str(strand.oligo().color())[1:]  # drop the hash
                stapColors.append([strand.idx5Prime(), int(c, 16)])
        # sequence
        highIdx = stapStrandSet.partMaxBaseIdx()
        stapSeq = [""] * highIdx
        for strand in stapStrandSet:
            stapSeq[strand._baseIdxLow:strand._baseIdxHigh] = strand.sequenceList()
        scafSeq = [""] * highIdx
        for strand in vh.scaffoldStrandSet():
            scafSeq[strand._baseIdxLow:strand._baseIdxHigh] = strand.sequenceList()

        vhDict = {"row": row,
                  "col": col,
                  "num": vh.number(),
                  "scaf": vh.getLegacyStrandSetArray(StrandType.Scaffold),
                  "stap": vh.getLegacyStrandSetArray(StrandType.Staple),
                  "loop": insts,
                  "skip": skips,
                  "scafLoop": [],
                  "stapLoop": [],
                  "scafSeq": scafSeq,
                  "stapSeq": stapSeq,
                  "stap_colors": stapColors}
        vhList.append(vhDict)
    bname = basename(str(fname))
    obj = {"name": bname, "vstrands": vhList}
    return obj
