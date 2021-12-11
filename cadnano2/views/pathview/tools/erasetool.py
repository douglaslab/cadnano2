import sys
from .abstractpathtool import AbstractPathTool
import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), [])
util.qtWrapImport('QtGui', globals(), [])


class EraseTool(AbstractPathTool):
    """
    docstring for EraseTool
    """
    def __init__(self, controller):
        super(EraseTool, self).__init__(controller)

    def __repr__(self):
        return "eraseTool"  # first letter should be lowercase