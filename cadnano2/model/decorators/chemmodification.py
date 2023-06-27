#!/usr/bin/env python
# encoding: utf-8

import cadnano2.util as util
from .decorator import Decorator

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QObject', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QUndoStack', 'QUndoCommand'])

class ChemModification(Decorator):
    """
    Decorators do not affect an applied sequence
    """
    def __init__(self, index, name):
        super(ChemModification, self).__init__(index)
        self._name = name
    # end def

    def name(self):
        """
        This is the string of a decorator f.i. the name of the chemical modification
        """
        return self._name

    def set_name(self, name):
        self._name = name
# end class
