#!/usr/bin/env python
# encoding: utf-8

import cadnano2.util as util


class SkipItem(AbstractDecoratorItem):
    def __init__(self, parent):
        """The parent should be a VirtualHelixItem."""
        super(SkipItem, self).__init__(parent)

    ### SIGNALS ###

    ### SLOTS ###

    ### METHODS ###

    ### COMMANDS ###
