#!/usr/bin/env python
# encoding: utf-8

from operator import attrgetter
import cadnano2.util as util
from array import array

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QObject', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QUndoStack', 'QUndoCommand'])

class Decorator(object):
    """
    Decorators do not affect an applied sequence
    """
    def __init__(self, index):
        if self.__class__ == Decorator:
            e = "Decorator should be subclassed."
            raise NotImplementedError(e)
        self._index = idex
        self._dType = None
        self._privateSequence = None
    # end def

    def privateLength(self):
        """
        This is the length of a sequence that is immutable by the strand
        """
        return length(self._privateSequence)

    def decoratorType(self):
        return self._dtype
# end class