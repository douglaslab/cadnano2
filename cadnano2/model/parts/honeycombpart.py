#!/usr/bin/env python
# encoding: utf-8

from cadnano2.cadnano import app
from .part import Part
from cadnano2.model.enum import LatticeType


class Crossovers:
    honeycombScafLow = [[1, 11], [8, 18], [4, 15]]
    honeycombScafHigh = [[2, 12], [9, 19], [5, 16]]
    honeycombStapLow = [[6], [13], [20]]
    honeycombStapHigh = [[7], [14], [0]]


root3 = 1.732051


class HoneycombPart(Part):
    _step = 21  # 32 in square
    _turnsPerStep = 2.0
    _helicalPitch = _step/_turnsPerStep
    _twistPerBase = 360/_helicalPitch  # degrees
    _twistOffset = 0 # degrees

    _activeBaseIndex = _step
    _subStepSize = _step / 3
    # Used in VirtualHelix::potentialCrossoverList
    _scafL = Crossovers.honeycombScafLow
    _scafH = Crossovers.honeycombScafHigh
    _stapL = Crossovers.honeycombStapLow
    _stapH = Crossovers.honeycombStapHigh

    def __init__(self, *args, **kwargs):
        super(HoneycombPart, self).__init__(self, *args, **kwargs)
        self._maxRow = kwargs.get('maxRow', app().prefs.honeycombRows)
        self._maxCol = kwargs.get('maxCol', app().prefs.honeycombCols)
        self._maxBase = int(kwargs.get('maxSteps', app().prefs.honeycombSteps) * self._step - 1)

    def crossSectionType(self):
        """Returns the cross-section type of the DNA part."""
        return LatticeType.Honeycomb

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
            neighbors.append(getVH((r-1,c)))  # p1 neighbor
            neighbors.append(getVH((r,c-1)))  # p2 neighbor
        else:
            neighbors.append(getVH((r,c-1)))  # p0 neighbor (p0 is a direction)
            neighbors.append(getVH((r+1,c)))  # p1 neighbor
            neighbors.append(getVH((r,c+1)))  # p2 neighbor
        # For indices of available directions, use range(0, len(neighbors))
        return neighbors  # Note: the order and presence of Nones is important
    # end def

    def latticeCoordToPositionXY(self, row, column, scaleFactor=1.0):
        """make sure self._radius is a float"""
        radius = self._radius
        x = column*radius*root3
        if self.isOddParity(row, column):   # odd parity
            y = row*radius*3 + radius
        else:                               # even parity
            y = row*radius*3
        return scaleFactor*x, scaleFactor*y
    # end def

    def positionToCoord(self, x, y, scaleFactor=1.0):
        radius = self._radius
        column = int(x/(radius*root3*scaleFactor) + 0.5)

        rowTemp = y/(radius*scaleFactor)
        if (rowTemp % 3) + 0.5 > 1.0:
            # odd parity
            row = int((rowTemp-1)/3 + 0.5)
        else:
            # even parity
            row = int(rowTemp/3 + 0.5)
    # end def

    ########################## Archiving / Unarchiving #########################
    def fillSimpleRep(self, sr):
        super(HoneycombPart, self).fillSimpleRep(sr)
        sr['.class'] = 'HoneycombPart'
