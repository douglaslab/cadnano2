from .abstractpathtool import AbstractPathTool
import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), [])
util.qtWrapImport('QtGui', globals(), [])


class DecoratorTool(AbstractPathTool):
    """
    docstring for DecoratorTool
    """
    def __init__(self, controller):
        super(DecoratorTool, self).__init__(controller)

    def __repr__(self):
        return "decoratorTool"  # first letter should be lowercase
