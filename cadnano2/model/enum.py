
class LatticeType:
    Honeycomb = 0
    Square = 1


class EndType:
    FivePrime = 0
    ThreePrime = 1


class StrandType:
    Scaffold = 0
    Staple = 1


class Parity:
    Even = 0
    Odd = 1


class BreakType:
    Left5Prime = 0
    Left3Prime = 1
    Right5Prime = 2
    Right3Prime = 3


class Crossovers:
    honeycombScafLeft = [[1, 11], [8, 18], [4, 15]]
    honeycombScafRight = [[2, 12], [9, 19], [5, 16]]
    honeycombStapLeft = [[6], [13], [20]]
    honeycombStapRight = [[7], [14], [0]]
    squareScafLeft = [[4, 26, 15], [18, 28, 7], [10, 20, 31], [2, 12, 23]]
    squareScafRight = [[5, 27, 16], [19, 29, 8], [11, 21, 0], [3, 13, 24]]
    squareStapLeft = [[31], [23], [15], [7]]
    squareStapRight = [[0], [24], [16], [8]]


class HandleOrient:
    LeftUp = 0
    RightUp = 1
    LeftDown = 2
    RightDown = 3
