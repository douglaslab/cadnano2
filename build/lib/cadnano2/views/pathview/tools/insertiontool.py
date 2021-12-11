import sys
from .abstractpathtool import AbstractPathTool
import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), [])
util.qtWrapImport('QtGui', globals(), [])


class InsertionTool(AbstractPathTool):
    """
    docstring for InsertionTool
    """
    def __init__(self, controller):
        super(InsertionTool, self).__init__(controller)

    def __repr__(self):
        return "insertionTool"  # first letter should be lowercase