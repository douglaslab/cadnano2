"""
This file houses the code that allows the opening of cadnano files by dragging
to the icon in the dock or double clicking on the icon.
"""

import objc, os
from Foundation import *
from AppKit import *
from controllers.documentcontroller import DocumentController
from cadnano2.model.io.decoder import decode
from cadnano2.cadnano import app as sharedCadnanoObj


class CNApplicationDelegate(NSObject):
    def application_openFile_(self, app, f):
        if f == "main.py":  # ignore
            return
        extension = os.path.splitext(f)[1].lower()
        if extension not in ('.nno', '.json', '.cadnano'):
            print("Could not open file %s (bad extension %s)"%(f, extension))
            return
        dc = list(sharedCadnanoObj().documentControllers)[0]
        decode(dc.document(), file(str(f)).read())
        return None

    def application_openFiles_(self, app, fs):
        if fs.isKindOfClass_(NSCFString):
            self.application_openFile_(app, fs)
            return
        for f in fs:
            self.application_openFiles_(app, f)

    def applicationShouldTerminate_(self, app):
        for dc in sharedCadnanoObj().documentControllers:
            if not dc.maybeSave():
                return NSTerminateCancel
        return NSTerminateNow

sharedDelegate = CNApplicationDelegate.alloc().init()
NSApplication.sharedApplication().setDelegate_(sharedDelegate)
