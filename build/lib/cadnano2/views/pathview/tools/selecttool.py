from .abstractpathtool import AbstractPathTool
import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), [])
util.qtWrapImport('QtGui', globals(), [])


class SelectTool(AbstractPathTool):
    """
    SelectTool is the default tool. It allows editing of breakpoints
    (by clicking and dragging) and toggling of crossovers.
    """
    def __init__(self, controller):
        super(SelectTool, self).__init__(controller)

    def __repr__(self):
        return "selectTool"  # first letter should be lowercase