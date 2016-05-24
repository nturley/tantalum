import sys
from PySide import QtUiTools
from PySide.QtGui import *
from PySide.QtCore import *
import qdarkstyle
from collections import deque


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

    def __str__(self):
        return 'date: ' + self.date +\
               '\nversion: ' + self.version +\
               '\ntimescale: ' + self.timescale +\
               '\n' + str(self.rootscope)[:-1]


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

    def __str__(self):
        return self.signame


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

    indent_level = 0

    def __str__(self):
        ret = ''
        for _ in range(Scope.indent_level):
            ret += '  '
        ret += self.name + '\n'
        Scope.indent_level += 1
        for sig in self.childsigs:
            for _ in range(Scope.indent_level):
                ret += '  '
            ret += sig.signame + '\n'
        for scope in self.childscopes:
            ret += str(scope)
        Scope.indent_level -= 1
        return ret


# simulation or declaration command
class Command:
    def __init__(self, command_type):
        self.comtype = command_type
        self.text = None

    def add_text(self, text):
        if self.text:
            self.text += ' ' + text
        else:
            self.text = text

    def __str__(self):
        if self.text:
            return self.comtype + ': ' + self.text
        return self.comtype


class ValueChange:
    def __init__(self, val):
        self.val = val
        self.sid = None

    def __str__(self):
        return self.sid + '=' + self.val


class SimulationTime:
    def __init__(self, time):
        self.time = time

    def __str__(self):
        return '#' + self.time

# 2005 table 18.3
decl_keywords = set(['$comment',
                     '$timescale',
                     '$date',
                     '$upscope',
                     '$enddefinitions',
                     '$var',
                     '$scope',
                     '$version'])
sim_keywords = set(['$dumpall',
                    '$dumpvars',
                    '$dumpon',
                    '$dumpoff'])

scalars = ('0', '1', 'x', 'X', 'z', 'Z')
vec_types = ('b', 'B', 'r', 'R')

keywords = decl_keywords | sim_keywords


class StateMachine:
    """
    vcd parser state machine
    builds list of commands (Command, ValueChange, or SimulationTime)
    stores completed commands in command_stream
    """

    def __init__(self):
        # partially constructed command
        self.current_command = None
        # list of completed commands
        self.command_stream = []

    def start_state(self, word, word_stack):
        if word in keywords:
            self.current_command = Command(word[1:])
            return self.command_state

        # otherwise only consume one character
        # there is no guaranteed whitespace before next token
        word_stack.appendleft(word[1:])

        if word.startswith('#'):
            return self.time_state

        # otherwise it's one of the value changes
        self.current_command = ValueChange(word[0].lower())

        # scalar values are one character so goto sid
        if word.startswith(scalars):
            return self.vchange_sid_state
        # vector values keep going so goto val before sid
        if word.startswith(vec_types):
            return self.vchange_val_state
        assert False

    def command_state(self, word, word_stack):
        if word == '$end':
            self.command_stream.append(self.current_command)
            return self.start_state
        self.current_command.add_text(word)
        return self.command_state

    def vchange_sid_state(self, word, word_stack):
        self.current_command.sid = word
        self.command_stream.append(self.current_command)
        return self.start_state

    def vchange_val_state(self, word, word_stack):
        self.current_command.val += word
        return self.vchange_sid_state

    def time_state(self, word, word_stack):
        time = SimulationTime(word)
        self.command_stream.append(time)
        return self.start_state


def generate_commands(file_handle):
    machine = StateMachine()
    next_state = machine.start_state
    for line in file_handle:
        # we use a deque so we can consume entire words or partial words
        # we pop words and then put unconsumed characters back onto the stack
        word_stack = deque(line.split())

        # we are mutating word_stack, so we can't iterate
        while len(word_stack) > 0:
            word = word_stack.popleft()
            if len(word) is 0:
                continue

            # execute state, returns next state to execute
            next_state = next_state(word, word_stack)

            # yield any completed commands
            if len(machine.command_stream) > 0:
                yield machine.command_stream.pop()


def get_header(file_name):
    header = Header()
    scope = None
    with open(file_name) as f:
        for com in generate_commands(f):
            if com.comtype == 'date':
                header.date = com.text
            if com.comtype == 'version':
                header.version = com.text
            if com.comtype == 'timescale':
                header.timescale = com.text
            if com.comtype == 'scope':
                scope = Scope(com.text, scope)
                if header.rootscope is None:
                    header.rootscope = scope
            if com.comtype == 'var':
                Signal(com.text, scope)
            if com.comtype == 'upscope':
                scope = scope.parent
            if com.comtype == 'enddefinitions':
                header.validate()
                return header


class MyScene(QGraphicsScene):

    def dragEnterEvent(self, e):
        e.acceptProposedAction()

    def dropEvent(self, e):
        data = e.mimeData().text()
        self.addText(data)

    def dragMoveEvent(self, e):
        e.acceptProposedAction()


class SigListModel(QStandardItemModel):
    def __init__(self):
        super(SigListModel, self).__init__()

    def mimeData(self, indices):
        data = QMimeData()
        data.setText(self.item(0).data().signame)
        return data


class AppResources():
    def __init__(self):
        self.blockIcon = QPixmap("block.png")
        self.icon = QPixmap("signal.png")
        self.bgcolor = QColor(32, 31, 31)
        self.textColor = Qt.lightGray


class MainApp():
    def __init__(self):
        # start the application and load the UI
        self.app = QApplication(sys.argv)
        self.window = QtUiTools.QUiLoader().load("mainwindow.ui")

        # setup widgets
        self.window.treeWidget.clear()
        self.siglistmodel = SigListModel()
        self.window.listView.setModel(self.siglistmodel)
        self.window.listView.setDragEnabled(True)
        self.scene = MyScene()
        self.window.graphicsView.setScene(self.scene)
        self.window.graphicsView.setAcceptDrops(True)

        # connect signals
        self.window.actionOpen.triggered.connect(self.openfile)
        self.window.treeWidget.itemSelectionChanged.connect(self.treeselectchanged)

        # setup look and feel
        self.res = AppResources()
        self.app.setStyleSheet(qdarkstyle.load_stylesheet())
        self.scene.setBackgroundBrush(QBrush(self.res.bgcolor))

        self.window.show()

    def treeselectchanged(self):
        self.loadsigs(self.window.treeWidget.selectedItems()[0].scope)

    def openfile(self):
        fname, _ = QFileDialog.getOpenFileName(self.window,
                                               'Open file',
                                               "",
                                               "Waveform Files (*.vcd)")
        if fname:
            head = get_header(fname)
            self.window.treeWidget.clear()
            root = self.loadScopes(head.rootscope, self.window.treeWidget)
            self.window.treeWidget.expandAll()
            self.window.treeWidget.setCurrentItem(root, 0)
            self.loadsigs(head.rootscope)

    def loadsigs(self, scope):
        self.siglistmodel.clear()
        for sig in scope.childsigs:
            newitem = QStandardItem(self.res.icon, sig.signame)
            newitem.setDragEnabled(True)
            newitem.setData(sig)
            self.siglistmodel.appendRow(newitem)

    def loadScopes(self, scope, currparent):
        newItem = QTreeWidgetItem(currparent)
        newItem.setText(0, scope.name)
        newItem.setIcon(0, self.res.blockIcon)
        newItem.scope = scope
        for childscope in scope.childscopes:
            self.loadScopes(childscope, newItem)
        return newItem


if __name__ == '__main__':
    app = MainApp()
    sys.exit(app.app.exec_())