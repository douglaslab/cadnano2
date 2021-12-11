from cadnano2.cadnano import app
from cadnano2.model.enum import LatticeType
from .part import Part


class Crossovers:
    squareScafLow = [[4, 26, 15], [18, 28, 7], [10, 20, 31], [2, 12, 23]]
    squareScafHigh = [[5, 27, 16], [19, 29, 8], [11, 21, 0], [3, 13, 24]]
    squareStapLow = [[31], [23], [15], [7]]
    squareStapHigh = [[0], [24], [16], [8]]


class SquarePart(Part):
    _step = 32  # 21 in honeycomb
    _subStepSize = _step / 4
    _turnsPerStep = 3.0
    _helicalPitch = _step/_turnsPerStep
    _twistPerBase = 360/_helicalPitch  # degrees
    _twistOffset = 180 + _twistPerBase/2  # degrees

    # Used in VirtualHelix::potentialCrossoverList
    _scafL = Crossovers.squareScafLow
    _scafH = Crossovers.squareScafHigh
    _stapL = Crossovers.squareStapLow
    _stapH = Crossovers.squareStapHigh

    def __init__(self, *args, **kwargs):
        super(SquarePart, self).__init__(self, *args, **kwargs)
        self._maxRow = kwargs.get('maxRow', app().prefs.squareRows)
        self._maxCol = kwargs.get('maxCol', app().prefs.squareCols)
        self._maxBase = int(kwargs.get('maxSteps', app().prefs.squareSteps) * self._step - 1)

    def crossSectionType(self):
        return LatticeType.Square
    # end def

    def isEvenParity(self, row, column):
        return (row % 2) == (column % 2)
    # end def

    def isOddParity(self, row, column):
        return (row % 2) ^ (column % 2)
    # end def

    def getVirtualHelixNeighbors(self, virtualHelix):
        """
        returns the list of neighboring virtualHelices based on parity of an
        input virtualHelix

        If a potential neighbor doesn't exist, None is returned in it's place
        """
        neighbors = []
        vh = virtualHelix
        if vh == None:
            return neighbors

        # assign the method to a a local variable
        getVH = self.virtualHelixAtCoord
        # get the vh's row and column r,c
        (r, c) = vh.coord()

        if self.isEvenParity(r, c):
            neighbors.append(getVH((r,c+1)))  # p0 neighbor (p0 is a direction)
            neighbors.append(getVH((r+1,c)))  # p1 neighbor
            neighbors.append(getVH((r,c-1)))  # p2 neighbor
            neighbors.append(getVH((r-1,c)))  # p2 neighbor
        else:
            neighbors.append(getVH((r,c-1)))  # p0 neighbor (p0 is a direction)
            neighbors.append(getVH((r-1,c)))  # p1 neighbor
            neighbors.append(getVH((r,c+1)))  # p2 neighbor
            neighbors.append(getVH((r+1,c)))  # p3 neighbor
        # For indices of available directions, use range(0, len(neighbors))
        return neighbors  # Note: the order and presence of Nones is important
    # end def

    def latticeCoordToPositionXY(self, row, column, scaleFactor=1.0):
        """
        make sure self._radius is a float
        """
        radius = self._radius
        y = row*2*radius
        x = column*2*radius
        return scaleFactor*x, scaleFactor*y
    # end def

    def positionToCoord(self, x, y, scaleFactor=1.0):
        """
        """
        radius = self._radius
        row = int(y/(2*radius*scaleFactor) + 0.5)
        column = int(x/(2*radius*scaleFactor) + 0.5)
        return row, column
    # end def

    def fillSimpleRep(self, sr):
        super(SquarePart, self).fillSimpleRep(sr)
        sr['.class'] = 'SquarePart'
