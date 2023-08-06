import re
from Runtime import *



# Started at 2.75 runtime
# Now at 2.41 after moving from lists for dice to a dicepool class
# Now at 1.766 after reducing the number of regular expressions and doing simple string comparisons for next operator
# Now 1.261 after using a dictionary to look up the next operation instead of constantly cycling
# Now 0.433 after implementing JIT compiler


class Compiler:
    ws_re      = re.compile(r'\s+')
    int_re     = re.compile(r'\d+')
    comment_re = re.compile(r'#.*\n')
    def __init__(self, global_script, subscript=None, end_re=None, nest_level=None, pos_offset=0):
        self.compiler_pos_offset = pos_offset
        if len(global_script) == 0 or global_script[-1] != '\n':
            global_script += '\n'
        self.global_script = global_script
        if subscript is None:
            subscript = global_script
        self.starting_subscript = subscript
        self.script_tail = subscript
        self.end_re = end_re if end_re else None
        self.nest_level = nest_level if nest_level is not None else 0
        self.verbose = 0
        self.arg_stack_len = 0
        self.ilist = []
    def getGlobalScriptLineForPosition(self, pos):
        total_len = 0
        for lineno, line in enumerate(self.global_script.splitlines()):
            total_len += len(line) + 1
            if total_len >= pos:
                return lineno+1, line # Line numbers count from 1, not 0
        return 0, ''
    def getGlobalCompilerPosition(self)->int:
        return len(self.starting_subscript) - len(self.script_tail) + self.compiler_pos_offset
    def getEndOfPresentLine(self)->str:
        return self.script_tail.splitlines()[0]
    def addInstruction(self, instruction_subclass, *args):
        to_add = instruction_subclass(*args)
        to_add.setDebugParams(script_i=self.getGlobalCompilerPosition())
        self.ilist.append(to_add)
    def advanceByMatch(self, exp:Union[re.Pattern,str])->str:
        if type(exp) == str:
            if self.script_tail[0] == exp:
                matching = exp
            else:
                return None
        else:
            matching = re.match(exp, self.script_tail)
            if matching is None:
                return None
            matching = matching.group()
        rval = self.script_tail[:len(matching)]
        self.script_tail = self.script_tail[len(matching):]
        return rval
    def grabPostFixArgument(self)->bool:
        self.advanceByMatch(self.ws_re)
        # The only valid post-fix values are integer literals, S or C
        if matched := self.advanceByMatch(self.int_re):
            self.addInstruction(IntLiteral,int(matched))
            self.arg_stack_len += 1
            return True
        if self.advanceByMatch('S'):
            self.addInstruction(RunS)
            self.arg_stack_len += 1
            return True
        if self.advanceByMatch('C'):
            self.addInstruction(RunC)
            self.arg_stack_len += 1
            return True
        return False
    def requirePostFixArgument(self):
        assert self.grabPostFixArgument(), "Couldn't get post-fix argument from: \"%s\""%self.getEndOfPresentLine()
    def doWS(self):
        return self.advanceByMatch(self.ws_re)
    def doComments(self):
        return self.advanceByMatch(self.comment_re)
    def doInt(self):
        matched = self.advanceByMatch(self.int_re)
        if matched:
            self.addInstruction(IntLiteral,int(matched))
            self.arg_stack_len+=1
        return matched
    def doS(self):
        self.addInstruction(RunS)
        self.arg_stack_len += 1
    def doC(self):
        self.addInstruction(RunC)
        self.arg_stack_len += 1
    def doD(self):
        if self.arg_stack_len == 0:
            self.addInstruction(IntLiteral, 1)
        self.requirePostFixArgument()
        self.addInstruction(RunD)
        self.arg_stack_len -= 2
    def doPlus(self):
        # Is this a "X+" filter or a "+X" appending to the pool?
        if self.arg_stack_len > 0:
            # This is an X+
            self.addInstruction(RunGeq)
        else:
            # This is a +X
            self.requirePostFixArgument()
            self.addInstruction(RunPlusX)
        self.arg_stack_len -= 1
    def doMinus(self):
        if self.arg_stack_len > 0:
            # This is an X+
            self.addInstruction(RunLeq)
        else:
            # This is a +X
            self.requirePostFixArgument()
            self.addInstruction(RunMinusX)
        self.arg_stack_len -= 1
    def doMult(self):
        self.requirePostFixArgument()
        self.addInstruction(RunMult)
        self.arg_stack_len -= 1
    def doH(self):
        self.requirePostFixArgument()
        self.addInstruction(RunH)
        self.arg_stack_len -= 1
    def doL(self):
        self.requirePostFixArgument()
        self.addInstruction(RunL)
        self.arg_stack_len -= 1
    def doCurlyBracket(self):
        self.addInstruction(self.doCaptiveCurlyBracket)
    def doCaptiveCurlyBracket(self):
        sub = Compiler(self.global_script, self.script_tail,
                          '}', self.nest_level + 1, self.getGlobalCompilerPosition())
        sub.compile()
        self.script_tail = sub.script_tail
        if self.arg_stack_len < 1:
            self.addInstruction(IntLiteral,1)
            self.arg_stack_len += 1
        self.arg_stack_len -= 1
        return RunCurlyBlock(sub.ilist)
    def doSquareBracket(self):
        sub1 = Compiler(self.global_script, self.script_tail,
                          ']', self.nest_level + 1, self.getGlobalCompilerPosition())
        sub1.compile()
        self.script_tail = sub1.script_tail
        ilist1 = sub1.ilist
        self.doWS()
        if self.script_tail[0] == '{':
            self.script_tail = self.script_tail[1:]
            captive_curly = self.doCaptiveCurlyBracket()
        else:
            captive_curly = None
        self.addInstruction(RunSquareBlock, ilist1, captive_curly)
    def doG(self):
        self.addInstruction(RunG)
    def doV(self):
        self.requirePostFixArgument()
        self.addInstruction(RunV)
        self.arg_stack_len -= 1
    def compile(self)->Executor:
        single_letter_ops = {
            'S':self.doS,
            'C':self.doC,
            'D':self.doD,
            '+':self.doPlus,
            '-':self.doMinus,
            '{':self.doCurlyBracket,
            '[':self.doSquareBracket,
            '*':self.doMult,
            'H':self.doH,
            'L':self.doL,
            'G':self.doG,
            'V':self.doV,
        }
        try:
            while len(self.script_tail):
                next_char = self.script_tail[0]
                if next_char in single_letter_ops:
                    self.script_tail = self.script_tail[1:]
                    single_letter_ops[next_char]()
                    continue
                if self.doWS():       continue
                if self.doComments(): continue
                if self.doInt():      continue
                if self.end_re and self.advanceByMatch(self.end_re):
                    # We found the end condition, we rejoin the parent
                    break
                raise SyntaxError("Can't find a valid next token in: \"%s\""%self.getEndOfPresentLine())
        except Exception as e:
            cpos = self.getGlobalCompilerPosition()
            lineno, line = self.getGlobalScriptLineForPosition(cpos)
            print("Compilation error at line %d:"%lineno)
            print(line)
            print(e)
            raise e
        return Executor(self.ilist, self.global_script)

if __name__ == '__main__':
    cmp = Compiler(open('test.txt').read())
    e = cmp.compile()
    e.run()
