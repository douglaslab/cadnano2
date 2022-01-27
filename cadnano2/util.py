"""
util
Created by Jonathan deWerd.
"""
import inspect
from traceback import extract_stack
from random import Random
import string
import sys
import os 

import platform
from itertools import dropwhile, starmap
prng = Random()

# qtWrapImport will try using each framework listed
# in the qtFramework list until it finds one that works.
# At that point, qtFramework becomes a string indicating
# the framework that will thereafer be used to load qt classes.
#  Dummy   Uses dummy Qt classes (used by the model when loaded as a module)
#  PyQt    Tries to load Qt classes from PyQt4
#  PySide  Tries to load Qt classes
# The list is defined to consist only of the Dummy qt framework if util is the
# only module that gets loaded. The main.py of applications actually using qt
# need to redefine qtFramework to include PyQt and PySide.

qtFrameworkList = ['PyQt', 'Dummy']
chosenQtFramework = None
# def qtWrapImport(name, globaldict, fromlist):
#     """
#     special function that allows for the import of PySide or PyQt modules
#     as available
# 
#     name is the name of the Qt top level class such as QtCore, or QtGui
# 
#     globaldict is a the module level global namespace dictionary returned from
#     calling the globals() method
# 
#     fromlist is a list of subclasses such as [QFont, QColor], or [QRectF]
#     """
#     global qtWrapFramework  # This method is a stub. It gets swapped out for
#     global qtFrameworkList  # a framework-specific version when called
#     for trialFmwk in qtFrameworkList:
#         if trialFmwk == 'Dummy':
#             qtWrapImport = qtWrapImportFromDummy
#             return qtWrapImport(name, globaldict, fromlist)
#         elif trialFmwk == 'PyQt':
#             try:
#                 import PyQt4
#                 chosenQtFramework = 'PyQt'
#                 qtWrapImport = qtWrapImportFromPyQt
#                 return qtWrapImport(name, globaldict, fromlist)
#             except ImportError:
#                 pass
#         elif trialFmwk == 'PySide':
#             try:
#                 import PySide
#                 chosenQtFramework = 'PySide'
#                 qtWrapImport = qtWrapImportFromPySide
#                 return qtWrapImport(name, globaldict, fromlist)
#             except ImportError:
#                 pass
#         else:
#             raise NameError('Illegal qt framework %s'%trialFmwk)
#     assert(False)  # Have not found a suitable qt framework


def qtWrapImport(name, globaldict, fromlist):
    """
    special function that allows for the import of PySide or PyQt modules
    as available

    name is the name of the Qt top level class such as QtCore, or QtGui

    globaldict is a the module level global namespace dictionary returned from
    calling the globals() method

    fromlist is a list of subclasses such as [QFont, QColor], or [QRectF]
    """
    global qtWrapFramework  # This method is a stub. It gets swapped out for
    global qtFrameworkList  # a framework-specific version when called
    for trialFmwk in qtFrameworkList:
        if trialFmwk == 'PyQt':
            try:
                import PyQt6
                chosenQtFramework = 'PyQt'
                qtWrapImport = qtWrapImportFromPyQt
                return qtWrapImport(name, globaldict, fromlist)
            except ImportError:
                pass
        elif trialFmwk == 'PySide':
            try:
                import PySide
                chosenQtFramework = 'PySide'
                qtWrapImport = qtWrapImportFromPySide
                return qtWrapImport(name, globaldict, fromlist)
            except ImportError:
                pass
        elif trialFmwk == 'Dummy':
            qtWrapImport = qtWrapImportFromDummy
            return qtWrapImport(name, globaldict, fromlist)
        else:
            raise NameError('Illegal qt framework %s'%trialFmwk)
    assert(False)  # Have not found a suitable qt framework


def qtWrapImportFromDummy(name, globaldict, fromlist):
    modName = 'dummyqt.%s'%(name)
    imports = __import__(modName, globaldict, locals(), fromlist, 0)
    canary = object()
    for k in fromlist:
        binding = getattr(imports, k, canary)
        if binding == canary:
            raise KeyError("Couldn't import key '%s' from module '%s'"%(k, modName))
        globaldict[k] = binding


def qtWrapImportFromPyQt(name, globaldict, fromlist):
    modName = 'PyQt6.%s'%(name)
    imports = __import__(modName, globaldict, locals(), fromlist, 0)
    canary = object()
    for key in fromlist:
        binding = getattr(imports, key, canary)
        if binding == canary:
            raise KeyError("Couldn't import key '%s' from module '%s'"%(key, modName))
        globaldict[key] = binding


def qtWrapImportFromPySide(name, globaldict, fromlist):
    modName = 'PySide.%s'%(name)
    imports = __import__(modName, globaldict, locals(), fromlist, -1)
    canary = object()
    for key in fromlist:
        if key in ('pyqtSignal', 'pyqtSlot', 'QString', 'QStringList'):
            if key == 'pyqtSignal':
                globaldict[key] = getattr(imports, 'Signal') 
            elif key == 'pyqtSlot':
                globaldict[key] = getattr(imports, 'Slot')
            elif key == 'QString':
                globaldict[key] = str
            elif key == 'QStringList':
                globaldict[key] = list
        else:
            binding = getattr(_temp, k, canary)
            if binding == canary:
                raise KeyError("Couldn't import key '%s' from module '%s'"%(key, modName))
            globaldict[key] = binding


def clamp(x, minX, maxX):
    if x < minX:
        return minX
    elif x > maxX:
        return maxX
    else:
        return x


def overlap(x,y, a,b):
    """
    finds the overlap of the range x to y in a to b
    assumes an overlap exists, i.e.
        y >= a and b >= x
    """
    c = clamp(x, a, b)
    d = clamp(y, a, b)
    return c, d
# end def


def trace(n):
    """Returns a stack trace n frames deep"""
    s = extract_stack()
    frames = []
    for f in s[-n-1:-1]:
        # f is a stack frame like
        # ('/path/script.py', 42, 'funcname', 'current = line - of / code')
        frames.append( (os.path.basename(f[0])+':%i'%f[1])+'(%s)'%f[2] )
    return " > ".join(frames)


def defineEventForwardingMethodsForClass(classObj, forwardedEventSuffix, eventNames):
    """Automatically defines methods of the form eventName0Event(self, event) on
    classObj that call self.activeTool().eventName0ForwardedEventSuffix(self, event).
    Note that self here is the 2nd argument of eventName0ForwardedEventSuffix which 
    will be defined with 3 arguments, the first of which will implicitly be the
    activeTool(). If self.activeTool() does not implement eventName0ForwardedEventSuffix,
    no error is raised.
    """
    qtWrapImport('QtGui', globals(), [ 'QGraphicsItem', 'QMouseEvent',\
                                       'QGraphicsSceneMouseEvent'])
    for evName in eventNames:
        delegateMethodName = evName + forwardedEventSuffix
        eventMethodName = evName + 'Event'
        defaultMethodName = evName + 'Default'
        forwardDisablingPropertyName = delegateMethodName + 'Unused'

        def makeTemplateMethod(eventMethodName, delegateMethodName):
            def templateMethod(self, event):
                # see if the event also exists
                defaultMethod = getattr(classObj,defaultMethodName,None)
                if defaultMethod != None:
                    defaultMethod(self,event)

                activeTool = self.activeTool()
                if activeTool and not getattr(activeTool, forwardDisablingPropertyName, False):
                    delegateMethod = getattr(activeTool, delegateMethodName, None)
                    if delegateMethod:
                        delegateMethod(self, event)
                    else:
                        superMethod = getattr(QGraphicsItem, eventMethodName)
                        excludeSuperCallBecauseOfTypeIntolerance = \
                                 isinstance(event, QMouseEvent) and\
                                 not isinstance(event, )
                        if not excludeSuperCallBecauseOfTypeIntolerance:
                            superMethod(self, event)
                else:
                    superMethod = getattr(QGraphicsItem, eventMethodName)
                    superMethod(self, event)
            return templateMethod
        eventHandler = makeTemplateMethod(eventMethodName, delegateMethodName)
        setattr(classObj, eventMethodName, eventHandler)


def strToDna(seqStr):
    """Returns str having been reduced to capital ACTG."""
    return "".join([c for c in seqStr if c in 'ACGTacgt']).upper()


complement = str.maketrans('ACGTacgt','TGCATGCA')


def rcomp(seqStr):
    """Returns the reverse complement of the sequence in seqStr."""
    return seqStr.translate(complement)[::-1]


def comp(seqStr):
    """Returns the complement of the sequence in seqStr."""
    return seqStr.translate(complement)


whitetoQ = str.maketrans(' ','?')


def markwhite(seqStr):
    return seqStr.translate(whitetoQ)


def nowhite(seqStr):
    """Gets rid of whitespace in a string."""
    return ''.join([c for c in seqStr if c in string.letters])


nearest=lambda a,l:min(l,key=lambda x:abs(x-a))


def isWindows():
    if platform.system() == 'Windows':
        return True
    else:
        return False


def isMac():
    try:
        return platform.system() == 'Darwin'
    except:
        return os.path.exists('/System/Library/CoreServices/Finder.app')


def isLinux():
    if platform.system() == 'Linux':
        return True
    else:
        return False


def methodName():
    """Returns string containing name of the calling method."""
    return inspect.stack()[1][3]


def starmapExec(f, tupleIter):
    """
    takes a function f and * starmaps the list but drops the results
    """
    list(dropwhile(lambda x: True, starmap(f, tupleIter)))
# end def


def execCommandList(modelObject, commands, desc=None, useUndoStack=True):
    """
    This is a wrapper for performing QUndoCommands, meant to ensure
    uniform handling of the undoStack and macro descriptions.

    When using the undoStack, commands are pushed onto self.undoStack()
    as part of a macro with description desc. Otherwise, command redo
    methods are called directly.
    """
    if useUndoStack:
        undoStackId = str(id(modelObject.undoStack()))[-4:]
        # print "<QUndoStack %s> %s" % (undoStackId, desc)
        modelObject.undoStack().beginMacro(desc)
        for c in commands:
            modelObject.undoStack().push(c)
        modelObject.undoStack().endMacro()
    else:
        # print "<NoUndoStack> %s" % (desc)
        for c in commands:
            c.redo()
# end def


def beginSuperMacro(modelObject, desc=None):
    """
    SuperMacros can be used to nest multiple command lists.

    Normally execCommandList macros all the commands in a list.
    In some cases, multiple command lists need to be executed separately
    because of dependency issues. (e.g. in part.autoStaple, strands
    must be completely 1. created and 2. split before 3. xover installation.)
    """
    modelObject.undoStack().beginMacro(desc)
# end def


def endSuperMacro(modelObject):
    """Ends a SuperMacro. Should be called after beginSuperMacro."""
    modelObject.undoStack().endMacro()
# end def


def findChild(self):
    """
    When called when self isa QGraphicsItem, iterates through self's
    childItems(), placing a red rectangle (a sibling of self) around
    each item in sequence (press return to move between items). Since
    the index of each child item is displayed as it is highlighted,
    one can use findChild() to quickly get a reference to one of self's
    children. At each step, one can type a command letter before
    hitting return. The command will apply to the current child.
    Command Letter:     Action:
    <return>            Advance to next child
    s<return>           Show current child
    S<return>           Show current child, hide siblings
    h<return>           Hide current child
    r<return>           return current child
    """
    qtWrapImport('QtGui', globals(), ['QGraphicsRectItem', 'QPen'])
    qtWrapImport('QtCore', globals(), ['Qt'])
    children = self.childItems()
    parent = self.parentItem()
    childVisibility = [(child, child.isVisible()) for child in children]
    for n in range(len(children)):
        child = children[n]
        print("Highlighting %s.childItems()[%i] = %s"%(self, n, child))
        childBR = child.mapToItem(parent, child.boundingRect())
        childBR = childBR.boundingRect()  # xform gives us a QPolygonF
        debugHighlighter = QGraphicsRectItem(childBR, parent)
        debugHighlighter.setPen(QPen(Qt.GlobalColor.red))
        debugHighlighter.setZValue(9001)
        while True:
            # wait for return to be pressed while spinning the event loop.
            # also process single-character commands.
            command = input()
            if command == 's':    # Show current child
                child.show()
            elif command == 'h':  # Hde current child
                child.hide()
            elif command == 'S':  # Show only current child
                for c in children:
                    c.hide()
                child.show()
            elif command == 'r':  # Return current child
                for child, wasVisible in childVisibility:
                    child.setVisible(wasVisible)
                return child
            else:
                break
        debugHighlighter.scene().removeItem(debugHighlighter)
        for child, wasVisible in childVisibility:
            child.setVisible(wasVisible)



# From https://stackoverflow.com/questions/11130156/
# Define a context manager to suppress stdout and stderr.
class suppress_stdout_stderr(object):
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in 
    Python, i.e. will suppress all print, even if the print originates in a 
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).      

    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds =  [os.open(os.devnull,os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0],1)
        os.dup2(self.null_fds[1],2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0],1)
        os.dup2(self.save_fds[1],2)
        # Close all file descriptors
        for fd in self.null_fds + self.save_fds:
            os.close(fd)
