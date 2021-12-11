#!/usr/bin/env python
# encoding: utf-8


class Modifier(object):
    """
    Modifiers do affect an applied sequence and do not store a sequence
    themselves.  They cause a base changed to another sequence.
    Modifiers DO NOT affect the length of a strand
    """
    def __init__(self, idx):
        if self.__class__ == Modifier:
            e = "Modifier should be subclassed."
            raise NotImplementedError(e)
        self._mType = None
        self._lowIdx  = idx
        self._highIdx = self._lowIdx
        self._privateSequence = None
    # end def

    def length(self):
        """
        This is the length of a sequence that is immutable by the strand
        """
        return self._highIdx - self._lowIdx + 1

    def modifierType(self):
        return self._mtype
# end class