class QUndoCommand(object):
    children = []
    name = "untitled"
    def undo(self):
        for c in reversed(self.children):
            c.undo()
    def redo(self):
        for c in self.children:
            c.redo()

class QUndoStack(object):
    undoCmds = []
    macroStack = []  # list of lists
    macroNameStack = []
    index = 0
    clean = True
    def isClean(self):
        return self.clean
    def setClean(self):
        self.clean = True
    def clean(self):
        self.clean = True
        self.undoCmds = []
        self.index = 0
    def beginMacro(self, macroName):
        self.macroStack.append([])
        self.macroNameStack.append(macroName)
        self.clean = False
    def push(self, cmd):
        if self.macroStack:
            self.macroStack[-1].append(cmd)
        else:
            self.undoCmds.append(cmd)
            self.index = len(self.undoCmds) - 1
        cmd.redo()
        self.clean = False
    def endMacro(self):
        l = len(self.macroStack)
        if l == 0:
            assert(False)  # Can't end a macro that wasn't begun
        cmd = QUndoCommand()
        cmd.children = self.macroStack.pop()
        cmd.name = self.macroNameStack.pop()
        if l == 1:
            self.undoCmds.append(cmd)
            self.index = len(self.undoCmds) - 1
        else:
            self.macroStack[-1].append(cmd)
        self.clean = False
    def undo(self):
        assert(not self.macroStack)  # Can't undo in the middle of a macro!
        if self.index > 0:
            cmd = self.undoCmds[self.index]
            self.index = self.index - 1
            cmd.undo()
    def redo(self):
        assert(not macroStack)  # Can't redo in the middle of a macro
        if self.index < len(self.undoCmds) - 1:
            cmd = self.undoCmds[self.index + 1]
            self.index = self.index + 1
            cmd.redo()

class QColor(object):
    r = 0
    g = 0
    b = 0
    a = 0
    def __init__(self, *args):
        if len(args) == 1:
            assert(type(args[0]) == str)
            hvals = re.findall('[0-9a-fA-F]{2}', args[0])
            hvals = [int(hv, 16) for hv in hvals]
        elif len(args) == 3:
            hvals = list(args)
        elif len(args) == 4:
            hvals = list(args)
        else:
            hvals = []
        while len(hvals) < 3:
            hvals.append(0)
        if len(hvals) < 4:
            hvals.append(255)
        for hv in hvals:
            assert(0 <= hv <= 255)
        r, g, b, a = hvals

class QFont(object):
    dummy = True
    Bold = None
    def __init__(self, *args):
        pass

class QFontMetricsF(object):
    def __init__(self, *args):
        pass
