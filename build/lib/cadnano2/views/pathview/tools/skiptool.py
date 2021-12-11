from .abstractpathtool import AbstractPathTool
import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), [])
util.qtWrapImport('QtGui', globals(), [])


class SkipTool(AbstractPathTool):
    """
    docstring for SkipTool
    """
    def __init__(self, controller):
        super(SkipTool, self).__init__(controller)

    def __repr__(self):
        return "skipTool"  # first letter should be lowercase