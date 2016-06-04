from collections import deque
import model

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

keywords = decl_keywords


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

        self.simtime = 0

    def start_state(self, word, word_stack):
        if word in decl_keywords:
            self.current_command = model.Command(word[1:])
            return self.command_state
        if word in sim_keywords or word == '$end':
            # it looks the same as a value change
            return self.start_state

        # otherwise only consume one character
        # there is no guaranteed whitespace before next token
        word_stack.appendleft(word[1:])

        if word.startswith('#'):
            return self.time_state

        # otherwise it's one of the value changes
        self.current_command = model.ValueChange(word[0].lower(), self.simtime)

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
        time = model.SimulationTime(word)
        self.simtime = time.time
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
    header = model.Header()
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
                scope = model.Scope(com.text, scope)
                if header.rootscope is None:
                    header.rootscope = scope
            if com.comtype == 'var':
                model.Signal(com.text, scope)
            if com.comtype == 'upscope':
                scope = scope.parent
            if com.comtype == 'enddefinitions':
                header.validate()
                return header


def get_signal_changes(file_name, signal_id):
    """ yields all value changes for a signal """
    with open(file_name) as f:
        for com in generate_commands(f):
            if com.comtype == 'vc':
                if com.sid != signal_id:
                    continue
                yield com
