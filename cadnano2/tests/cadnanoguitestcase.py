# from PyQt4.QtCore import *
# from PyQt4.QtGui import *
import cadnano
import tests.guitestcase

main = tests.guitestcase.main


class CadnanoGuiTestCase(tests.guitestcase.GUITestCase):
    """
    SEE: http://docs.python.org/library/unittest.html
    """
    def setUp(self):
        """
        The setUp method is called before running any test. It is used
        to set the general conditions for the tests to run correctly.
        For GUI Tests, you always have to call setWidget to tell the
        framework what you will be testing.
        """
        import sys

        self.app = cadnano.initAppWithGui() # kick off a Gui style app
        self.documentController = list(self.app.documentControllers)[0]
        self.mainWindow = self.documentController.win

        # Include this or the automatic build will hang
        self.app.dontAskAndJustDiscardUnsavedChanges = True

        # By setting the widget to the main window we can traverse and
        # interact with any part of it. Also, tearDown will close
        # the application so we don't need to worry about that.
        self.setWidget(self.mainWindow, False, None)

    def tearDown(self):
        """
        The tearDown method is called at the end of running each test,
        generally used to clean up any objects created in setUp
        """
        tests.guitestcase.GUITestCase.tearDown(self)

if __name__ == '__main__':
    tests.guitestcase.main()
