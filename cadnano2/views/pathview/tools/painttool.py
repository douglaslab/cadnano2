import sys
from .abstractpathtool import AbstractPathTool
import cadnano2.util as util
util.qtWrapImport('QtCore', globals(), [])
util.qtWrapImport('QtGui', globals(), [])
util.qtWrapImport('QtWidgets', globals(), ['QApplication'])


class PaintTool(AbstractPathTool):
    """
    Handles visibility and color cycling for the paint tool.
    """
    def __init__(self, controller):
        super(PaintTool, self).__init__(controller)
        self._isMacrod = False

    def __repr__(self):
        return "paintTool"  # first letter should be lowercase

    def setActive(self, willBeActive):
        """Show the ColorPicker widget when active, hide when inactive."""
        if willBeActive:
            self._window.pathColorPanel.show()
        else:
            self._window.pathColorPanel.hide()
            self._window.pathColorPanel.prevColor()

    def widgetClicked(self):
        """Cycle through colors on 'p' keypress"""
        self._window.pathColorPanel.nextColor()

    def customMouseRelease(self, event):
        if self._isMacrod:
            self._isMacrod = False
            self._window.undoStack().endMacro()
    # end def

    def isMacrod(self):
        return self._isMacrod
    # end def

    def setMacrod(self):
        self._isMacrod = True
        self._window.undoStack().beginMacro("Group Paint")
        self._window.pathGraphicsView.addToPressList(self)
    # end def
