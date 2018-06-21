import util, cadnano
import heapq
from model.strandset import StrandSet
from model.enum import StrandType
from model.parts.part import Part
from model.oligo import Oligo
from multiprocessing import Pool, cpu_count
from operator import itemgetter

try:
    from . import staplegraph
    nx = True
except Exception as e:
    print("AutoBreak warning - Could not import staplegraph!")
    print(e)
    nx = False

token_cache = {}

def breakStaples(part, settings):
    clearTokenCache()
    breakOligos = part.document().selectedOligos()
    if not breakOligos:
        breakOligos = part.oligos()
    else:
        part.document().clearAllSelected()
    for o in list(breakOligos):
        if not o.isStaple():
            continue
        if nx:
            nxBreakStaple(o, settings)
        else:
            print("Not breaking")
            # breakStaple(o, settings)
# end def

def nxBreakStaple(oligo, settings):
    stapleScorer = settings.get('stapleScorer', tgtLengthStapleScorer)
    minStapleLegLen = settings.get('minStapleLegLen', 3)
    minStapleLen = settings.get('minStapleLen', 30)
    minStapleLenMinusOne = minStapleLen-1
    maxStapleLen = settings.get('maxStapleLen', 40)
    maxStapleLenPlusOne = maxStapleLen+1
    tgtStapleLen = settings.get('tgtStapleLen', 35)
    
    tokenList = tokenizeOligo(oligo, settings)

    # print "tkList", tokenList, oligo.length(), oligo.color()
    if len(tokenList) == 0:
        return
    cacheString = stringifyToken(oligo, tokenList)
    if cacheString in token_cache:
        # print "cacheHit!"
        breakItems, shortestScoreIdx = token_cache[cacheString]
        nxPerformBreaks(oligo, breakItems, tokenList, shortestScoreIdx, minStapleLegLen)
    else:
        staple_limits = [minStapleLen, maxStapleLen, tgtStapleLen] 
        tokenLists = [(tokenList, staple_limits,0)]
        tokenCount = tokenList[0]
        if oligo.isLoop():
            lenList = len(tokenList)
            for i in range(1, lenList):
                if tokenCount > 2*maxStapleLen:
                    break
                tL = tokenLists[i-1][0]
                rotatedList =  tL[1:-1] + tL[0:1]   # assumes lenList > 1
                tokenCount += rotatedList[0]
                tokenLists.append((rotatedList, staple_limits, i))
            # end for
        # end if
        # p = Pool(cpu_count() * 2)
        # p = Pool(4)
        # returns ( [breakStart, [breakLengths, ], score], tokenIdx)
        # results = p.map(staplegraph.minimumPath, tokenLists)
        results = list(map(staplegraph.minimumPath, tokenLists))

        f = itemgetter(0)   # get the graph results
        g = itemgetter(2)    # get the score
        # so this is
        scoreTuple = min(results, key=lambda x: g(f(x)) if x else 10000)
        # ensure there's at least one result
        if scoreTuple:
            shortestScore, shortestScoreIdx = scoreTuple
            breakItems = results[shortestScoreIdx][0][1]
            addToTokenCache(cacheString, breakItems, shortestScoreIdx)
            nxPerformBreaks(oligo, breakItems, tokenList, shortestScoreIdx, minStapleLegLen)
        else:
            if oligo.isLoop():
                print("unbroken Loop", oligo, oligo.length())
# end def

def addToTokenCache(cacheString, breakItems, shortestScoreIdx):
    token_cache[cacheString] = (breakItems, shortestScoreIdx)
# end def

def clearTokenCache():
    token_cache = {}
# end def

def stringifyToken(oligo, tokenList):
    cacheString = str(tokenList)
    if oligo.isLoop():
        cacheString = 'L' + cacheString
    return cacheString
# end def

def tokenizeOligo(oligo, settings):
    """
    Split the oligo into sub-tokens. Strands with insertions are not tokenized
    and their full length is added.
    """
    tokenList = []
    minStapleLegLen = settings.get('minStapleLegLen', 2)
    minStapleLen = settings.get('minStapleLen', 30)
    minStapleLenMinusOne = minStapleLen-1
    maxStapleLen = settings.get('maxStapleLen', 40)
    maxStapleLenPlusOne = maxStapleLen+1
    oligoL = oligo.length()
    if oligoL < 2*minStapleLen+1 or oligoL < minStapleLen:
        return tokenList

    totalL = 0
    strandGen = oligo.strand5p().generator3pStrand()
    for strand in strandGen:
        a = strand.totalLength()
        totalL += a
        # check length, and also for insertions
        if a > 2*minStapleLegLen-1 and not strand.hasInsertion():
            if len(tokenList) == 0:
                tokenList.append(minStapleLegLen)
            else:
                tokenList[-1] = tokenList[-1] + minStapleLegLen
            a -= minStapleLegLen
            while a > minStapleLegLen:
                tokenList.append(1)
                a -= 1
            # end while
            tokenList.append(minStapleLegLen)
        else:
            tokenList.append(a)
        # end if
    # end for

    if oligo.isLoop():
        loop_token = tokenList.pop(-1)
        tokenList[0] += loop_token

    # print "check", sum(tokenList), "==", oligoL, totalL
    if sum(tokenList) != oligoL:
        oligo.applyColor("#ff3333", useUndoStack=False)
        return []
    assert(sum(tokenList) == oligoL)
    return tokenList
# end def

def nxPerformBreaks(oligo, breakItems, tokenList, startingToken, minStapleLegLen):
    """ fullBreakptSoln is in the format of an IBS (see breakStrands).
    This function performs the breaks proposed by the solution. """
    part = oligo.part()
    if breakItems:
        util.beginSuperMacro(part, desc="Auto-Break")

        # temp = []
        # for s in oligo.strand5p().generator3pStrand():
        #     temp.append(s.length())
        # print "the segments", sum(temp), temp

        # print "the sum is ", sum(breakList[1]), "==", oligo.length(), "isLoop", oligo.isLoop()
        # print "the breakItems", breakItems

        strand = oligo.strand5p()
        if oligo.isLoop():
            # start things off make first cut
            length0 = sum(tokenList[0:startingToken+1])
            strand, idx, is5to3 = getStrandAtLengthInOligo(strand, length0-minStapleLegLen)
            sS = strand.strandSet()
            found, sSIdx = sS.getStrandIndex(strand)
            # found, overlap, sSIdx = sS._findIndexOfRangeFor(strand)
            strand.split(idx, updateSequence=False)
            strand = sS._strandList[sSIdx+1] if is5to3 else sS._strandList[sSIdx]

        # now iterate through all the breaks
        for b in breakItems[0:-1]:
            if strand.oligo().length() > b:
                strand, idx, is5to3 = getStrandAtLengthInOligo(strand, b)
                sS = strand.strandSet()
                found, sSIdx = sS.getStrandIndex(strand)
                # found, overlap, sSIdx = sS._findIndexOfRangeFor(strand)
                strand.split(idx, updateSequence=False)
                strand = sS._strandList[sSIdx+1] if is5to3 else sS._strandList[sSIdx]
            else:
                raise Exception("Oligo length %d is shorter than break length %d" % (strand.oligo().length(), b))
        util.endSuperMacro(part)
# end def

def getStrandAtLengthInOligo(strandIn, length):
    strandGen = strandIn.generator3pStrand()
    strand = next(strandGen)
    assert(strand == strandIn)
    # find the starting strand
    strandCounter = strand.totalLength()
    while strandCounter < length:
        try:
            strand = next(strandGen)
        except:
            print("yikes: ", strand.connection3p(), strandCounter, length, strand.oligo().isLoop(), strandIn.oligo().length())
            raise Exception
        strandCounter += strand.totalLength()
    # end while
    is5to3 = strand.isDrawn5to3()
    delta = strand.totalLength() - (strandCounter - length) - 1
    idx5p = strand.idx5Prime()
    # print "diff", delta, "idx5p", idx5p, "5to3", is5to3, "sCount", strandCounter, "L", length
    outIdx = idx5p + delta if is5to3 else idx5p - delta
    return (strand, outIdx, is5to3)
# end def

# Scoring functions takes an incremental breaking solution (IBS, see below)
# which is a linked list of breakpoints (nodes) and calculates the score
# (edge weight) of the staple that would lie between the last break in
# currentIBS and proposedNextNode. Lower is better.
def tgtLengthStapleScorer(currentIBS, proposedNextBreakNode, settings):
    """ Gives staples a better score for being
    closer to settings['tgtStapleLen'] """
    tgtStapleLen = settings.get('tgtStapleLen', 35)
    lastBreakPosInOligo = currentIBS[2][0]
    proposedNextBreakPos = proposedNextBreakNode[0]
    stapleLen = proposedNextBreakPos - lastBreakPosInOligo
    # Note the exponent. This allows Djikstra to try solutions
    # with fewer length deviations first. If you don't include
    # it, most paths that never touch a leaf get visited, decreasing
    # efficiency for long proto-staples. Also, we want to favor solutions
    # with several small deviations from tgtStapleLen over solutions with
    # a single larger deviation.
    return abs(stapleLen - tgtStapleLen)**3

def breakStaple(oligo, settings):
    # We were passed a super-long, highly suboptimal staple in the
    # oligo parameter. Our task is to break it into more reasonable staples.
    # We create a conceptual graph which represents breakpoints as
    # nodes. Each edge then represents a staple (bounded by two breakpoints
    # = nodes). The weight of each edge is an optimality score, lower is
    # better. Then we use Djikstra to find the most optimal way to break
    # the super-long staple passed in the oligo parameter into smaller staples
    # by finding the minimum-weight path from "starting" nodes to "terminal"
    # nodes.

    # The minimum number of bases after a crossover
    stapleScorer = settings.get('stapleScorer', tgtLengthStapleScorer)
    minStapleLegLen = settings.get('minStapleLegLen', 2)
    minStapleLen = settings.get('minStapleLen', 30)
    minStapleLenMinusOne = minStapleLen-1
    maxStapleLen = settings.get('maxStapleLen', 40)
    maxStapleLenPlusOne = maxStapleLen+1

    # First, we generate a list of valid breakpoints = nodes. This amortizes
    # the search for children in the inner loop of Djikstra later. Format:
    # node in nodes := (
    #   pos,        position of this break in oligo
    #   strand,     strand where the break occurs
    #   idx,        the index on strand where the break occurs
    #   isTerminal) True if this node can represent the last break in oligo
    nodes = possibleBreakpoints(oligo, settings)
    lengthOfNodesArr = len(nodes)
    if lengthOfNodesArr == 0:
        print("nada", minStapleLegLen, oligo.length())
        return

    # Each element of heap represents an incremental breakpoint solution (IBS)
    # which is a linked list of nodes taking the following form:
    # (totalWeight,   # the total weight of this list is first for automaic sorting
    #  prevIBS,       # the tuple representing the break before this (or None)
    #  node,          # the tuple from nodes representing this break
    #  nodeIdxInNodeArray)
    # An IBS becomes a full breakpoint solution iff
    #    Its first node is an initial node (got added during "add initial nodes")
    #    Its last node is a terminal node (got flagged as such in possibleBreakpoints)
    # Djikstra says: the first full breakpoint solution to be visited will be the optimal one
    heap = []
    firstStrand = oligo.strand5p()

    # Add everything on the firstStrand as an initial break
    # for i in xrange(len(nodes)):
    #     node = nodes[i]
    #     pos, strand, idx, isTerminal = node
    #     if strand != firstStrand:
    #         break
    #     newIBS = (0, None, node, i)
    #     heapq.heappush(heap, newIBS)

    # Just add the existing endpoint as an initial break
    # print "the nodes", nodes
    newIBS = (0, None, nodes[0], 0)
    heap.append(newIBS)

    # nodePosLog = []
    while heap:
        # Pop the min-weight node off the heap
        curIBS = heapq.heappop(heap)
        curTotalScore, prevIBS, node, nodeIdxInNodeArr = curIBS
        if node[3]:  # If we popped a terminal node, we win
            # print "Full Breakpt Solution Found"
            return performBreaks(oligo.part(), curIBS)
        # Add its children (set of possible next breaks) to the heap
        nodePos = node[0]
        nextNodeIdx = nodeIdxInNodeArr + 1
        while nextNodeIdx < lengthOfNodesArr:
            nextNode = nodes[nextNodeIdx]
            nextNodePos = nextNode[0]
            proposedStrandLen = nextNodePos - nodePos
            if minStapleLenMinusOne < proposedStrandLen < maxStapleLenPlusOne:
                # nodePosLog.append(nextNodePos)
                nextStapleScore = tgtLengthStapleScorer(curIBS, nextNode, settings)
                newChildIBS = (curTotalScore + nextStapleScore,\
                               curIBS,\
                               nextNode,\
                               nextNodeIdx)
                heapq.heappush(heap, newChildIBS)
            elif proposedStrandLen > maxStapleLen:
                break
            nextNodeIdx += 1
    # print nodePosLog
    # print "No Breakpt Solution Found"

def performBreaks(part, fullBreakptSoln):
    """ fullBreakptSoln is in the format of an IBS (see breakStrands).
    This function performs the breaks proposed by the solution. """
    util.beginSuperMacro(part, desc="Auto-Break")
    breakList, oligo = [], None  # Only for logging purposes
    if fullBreakptSoln != None:  # Skip the first breakpoint
        fullBreakptSoln = fullBreakptSoln[1]
    while fullBreakptSoln != None:
        curNode = fullBreakptSoln[2]
        fullBreakptSoln = fullBreakptSoln[1]  # Walk up the linked list
        if fullBreakptSoln == None:  # Skip last breakpoint
            break
        pos, strand, idx, isTerminal = curNode
        if strand.isDrawn5to3():
            idx -= 1 # Our indices correspond to the left side of the base
        strand.split(idx, updateSequence=False)
        breakList.append(curNode)  # Logging purposes only
    # print 'Breaks for %s at: %s'%(oligo, ' '.join(str(p) for p in breakList))
    util.endSuperMacro(part)

def possibleBreakpoints(oligo, settings):
    """ Returns a list of possible breakpoints (nodes) in the format:
    node in nodes := (             // YOU CANNOT UNSEE THE SADFACE :P
      pos,        position of this break in oligo
      strand,     strand where the break occurs
      idx,        the index on strand where the break occurs
      isTerminal) True if this node can represent the last break in oligo"""

    # The minimum number of bases after a crossover
    minStapleLegLen = settings.get('minStapleLegLen', 2)
    minStapleLen = settings.get('minStapleLen', 30)
    maxStapleLen = settings.get('maxStapleLen', 40)

    nodes = []
    strand = firstStrand = oligo.strand5p()
    isLoop = strand.connection5p() != None
    pos, idx = 0, 0  # correspond to pos, idx above
    while True:
        nextStrand = strand.connection3p()
        isTerminalStrand = nextStrand in (None, firstStrand)
        if strand.isDrawn5to3():
            idx, maxIdx = strand.lowIdx(), strand.highIdx() + 1
            if strand != firstStrand:
                idx += minStapleLegLen
                pos += minStapleLegLen
            if not isTerminalStrand:
                maxIdx -= minStapleLegLen
            while idx <= maxIdx:
                isTerminalNode = isTerminalStrand and idx == maxIdx
                nodes.append((pos, strand, idx, isTerminalNode))
                idx += 1
                pos += 1
            pos += minStapleLegLen - 1
        else:
            minIdx, idx = strand.lowIdx(), strand.highIdx() + 1
            if strand != firstStrand:
                idx -= minStapleLegLen
                pos += minStapleLegLen
            if not isTerminalStrand:
                minIdx += minStapleLegLen
            while idx >= minIdx:
                isTerminalNode = isTerminalStrand and idx == minIdx
                nodes.append((pos, strand, idx, isTerminalNode))
                idx -= 1
                pos += 1
            pos += minStapleLegLen - 1
        strand = nextStrand
        if isTerminalStrand:
            break
    # if nodes:  # dump the node array to stdout
    #     print ' '.join(str(n[0])+':'+str(n[2]) for n in nodes) + (' :: %i'%oligo.length()) + repr(nodes[-1])
    return nodes

cadnano.app().breakStaples = breakStaples
