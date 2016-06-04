

class ViewPortModel():
    def __init__(self, fname, sigdict, header):
        self.fname = fname
        self.sigdict = sigdict
        self.header = header


class Header:
    def __init__(self):
        self.date = None
        self.version = None
        self.timescale = None
        self.rootscope = None

    def validate(self):
        assert self.date and \
            self.version and \
            self.timescale and \
            self.rootscope


class Signal:
    def __init__(self, text, scope):
        words = [word for word in text.split() if len(word) > 0]
        assert len(words) == 4
        self.sigtype = words[0]
        self.size = words[1]
        self.sid = words[2]
        self.signame = words[3]
        self.scope = scope
        scope.addsig(self)
        self.changes = None


class Scope:
    def __init__(self, text, parent=None):
        words = [word for word in text.split() if len(word) > 0]
        assert len(words) == 2
        self.scopetype = words[0]
        self.name = words[1]
        self.childscopes = []
        self.childsigs = []
        self.parent = parent
        if parent:
            parent.addscope(self)

    def addscope(self, child):
        self.childscopes.append(child)

    def addsig(self, child):
        self.childsigs.append(child)

    def getsigdict(self, parentdict=None):
        if parentdict is None:
            parentdict = {}
        for sig in self.childsigs:
            parentdict[sig.sid] = sig
        for scope in self.childscopes:
            scope.getsigdict(parentdict)
        return parentdict


class Command:
    """simulation or declaration command"""
    def __init__(self, command_type):
        self.comtype = command_type
        self.text = None

    def add_text(self, text):
        if self.text:
            self.text += ' ' + text
        else:
            self.text = text


class ValueChange:
    def __init__(self, val, time):
        self.comtype = 'vc'
        self.val = val
        self.sid = None
        self.time = int(time)

    def __str__(self):
        return self.sid + '=' + self.val + ' @' + str(self.time)


class SimulationTime:
    def __init__(self, time):
        self.comtype = 'time'
        self.time = time

    def __str__(self):
        return '#' + self.time