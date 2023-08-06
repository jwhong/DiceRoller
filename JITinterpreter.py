import re
from graph import makeBarGraph
from numpy import random
from typing import *
from collections import defaultdict
from dataclasses import dataclass

# Started at 2.75 runtime
# Now at 2.41 after moving from lists for dice to a dicepool class
# Now at 1.766 after reducing the number of regular expressions and doing simple string comparisons for next operator
# Now 1.261 after using a dictionary to look up the next operation instead of constantly cycling
# Now 0.433 after implementing JIT compiler

class DicePool:
    def __init__(self, dice:Iterable[int]=None, init_pool=None):
        self.vals = defaultdict(int) if init_pool is None else init_pool.copy()
        if dice is not None:
            self.addDice(dice)
    def addDie(self, val:int):
        self.vals[val] += 1
    def addDice(self, vals:Iterable[int]):
        for v in vals:
            self.vals[v] += 1
    def addPool(self, other):
        for k, v in other.vals.items():
            self.vals[k] += v
    def subPool(self, other):
        for k, v in other.vals.items():
            self.vals[k] -= v
            if self.vals[k] < 0:
                raise RuntimeError("Can't remove an X from a dice pool without X in it!")
    def mulInt(self, factor:int):
        for k, v in self.vals.items():
            self.vals[k] = factor*v
    def __len__(self):
        return sum(self.vals.values())
    def __iter__(self):
        for k, v in self.vals.items():
            for i in range(v):
                yield k
    def sum(self):
        rval = 0
        for k, v in self.vals.items():
            rval += k*v
        return rval
    def __repr__(self):
        if len(self.vals) == 0:
            return "Empty pool"
        low  = min(self.vals.keys())
        high = max(self.vals.keys())
        rval = ''
        for i in range(low, high+1):
            rval += '%d : %d '%(i, self.vals[i])
        return rval
    def getGeqSubset(self, thresh):
        ss = defaultdict(int)
        for k, v in self.vals.items():
            if k >= thresh:
                ss[k] = v
        return DicePool(init_pool=ss)
    def getLeqSubset(self, thresh):
        ss = defaultdict(int)
        for k, v in self.vals.items():
            if k <= thresh:
                ss[k] = v
        return DicePool(init_pool=ss)
    def getTop(self, count):
        ss = defaultdict(int)
        sorted_keys = sorted(self.vals.keys(), reverse=True)
        for k in sorted_keys:
            v = self.vals[k]
            if count > v:
                ss[k] = v
                count -= v
            else:
                ss[k] = count
                break
        return DicePool(init_pool=ss)
    def getBottom(self, count):
        ss = defaultdict(int)
        sorted_keys = sorted(self.vals.keys(), reverse=False)
        for k in sorted_keys:
            v = self.vals[k]
            if count > v:
                ss[k] = v
                count -= v
            else:
                ss[k] = count
                break
        return DicePool(init_pool=ss)
    def copy(self):
        return DicePool(init_pool=self.vals)
    def asList(self):
        rval = []
        for k, v in self.vals.items():
            for i in range(v):
                rval.append(k)
        return rval

@dataclass
class VMState:
    pool       : DicePool
    arg_stack  : List[int]
    nest_level : int

class Instruction:
    def setDebugParams(self, script_i:int):
        self.script_i = script_i # Index of this instruction in the script
    def run(self, vm:VMState):
        raise NotImplemented("Should be overridden by subclass")

class Executor:
    def __init__(self, instructions:Iterable[Instruction]):
        self.instructions = instructions
    def run(self, pool_override:DicePool=None)->VMState:
        s = VMState(DicePool() if pool_override is None else pool_override.copy(), [], 0)
        for inst in self.instructions:
            inst.run(s) # The instructions will mutate s
        return s

class IntValue(Instruction):
    pass

class IntLiteral(IntValue):
    def __init__(self, val:int):
        self.val = val
    def run(self, vm:VMState):
        vm.arg_stack.append(self.val)

class DoS(IntValue):
    def run(self, vm:VMState):
        vm.arg_stack.append(vm.pool.sum())
        # self.print("Sum is %d" % self.arg_stack[0])

class DoC(IntValue):
    def run(self, vm:VMState):
        vm.arg_stack.append(len(vm.pool))
        # self.print("Count is %d" % self.arg_stack[0])

class DoD(Instruction):
    def run(self, vm:VMState):
        n_sides = vm.arg_stack.pop()
        n_dice  = vm.arg_stack.pop()
        vm.pool = DicePool(random.randint(1, n_sides + 1, n_dice))
        #self.print("Rolled %dD%d, got:" % (n_dice, n_sides))
        #self.print(self.pool)

class DoGeq(Instruction):
    def run(self, vm:VMState):
        thresh = vm.arg_stack.pop()
        #start_len = len(vm.pool)
        vm.pool = vm.pool.getGeqSubset(thresh)
        #vm.print("Pass on %d+" % thresh)
        #end_len = len(vm.pool)
        #removed = start_len - end_len
        #vm.print("Removed %d dice, leaving %d" % (removed, end_len))

class DoPlusX(Instruction):
    def run(self, vm:VMState):
        vm.pool.addDie(vm.arg_stack.pop())
        #self.print("Added +%d to pool" % to_append)

class DoLeq(Instruction):
    def run(self, vm:VMState):
        thresh = vm.arg_stack.pop()
        vm.pool = vm.pool.getLeqSubset(thresh)

class DoMult(Instruction):
    def run(self, vm:VMState):
        vm.pool.mulInt(vm.arg_stack.pop())

class DoMinusX(Instruction):
    def run(self, vm:VMState):
        vm.pool.addDie(-1*vm.arg_stack.pop())

class DoH(Instruction):
    def run(self, vm:VMState):
        count = vm.arg_stack.pop()
        vm.pool = vm.pool.getTop(count)

class DoL(Instruction):
    def run(self, vm:VMState):
        count = vm.arg_stack.pop()
        vm.pool = vm.pool.getBottom(count)

class DoG(Instruction):
    def run(self, vm:VMState):
        makeBarGraph(vm.pool)

class DoCurlyBlock(Instruction):
    def __init__(self, ilist:Iterable[Instruction]):
        self.ilist = ilist
    def run(self, vm:VMState, pool_override:DicePool=None):
        e = Executor(self.ilist)
        reps = vm.arg_stack.pop()
        pool_arg = vm.pool.copy() if pool_override is None else pool_override
        for i in range(reps):
            sub_s = e.run(pool_arg)
            if len(sub_s.arg_stack):
                vm.pool.addDice(sub_s.arg_stack)
            else:
                vm.pool.addPool(sub_s.pool)

class DoSquareBlock(Instruction):
    def __init__(self, filt_ilist:Iterable[Instruction], curly_block:Union[DoCurlyBlock,None]):
        self.filt_ilist = filt_ilist
        self.curly_block = curly_block
    def run(self, vm:VMState):
        e = Executor(self.filt_ilist)
        substate = e.run(vm.pool)
        vm.pool.subPool(substate.pool)
        if self.curly_block is not None:
            self.curly_block.run(vm, substate.pool)

class Interpreter:
    ws_re         = re.compile(r'\s+')
    int_re        = re.compile(r'\d+')
    def __init__(self, script, end_re=None, nest_level=None):
        # Purge all comments from the script
        script = ''.join(re.split(r'#.*\n', script+'\n'))
        self.original_script = script
        self.script_tail = script
        self.end_re = end_re if end_re else None
        self.nest_level = nest_level if nest_level is not None else 0
        self.verbose = 0
        self.arg_stack_len = 0
        self.ilist = []
    def print(self, *args):
        if not self.verbose:
            return
        print(self.nest_level * '    ', *args)
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
            self.ilist.append(IntLiteral(int(matched)))
            self.arg_stack_len+=1
            return True
        if self.advanceByMatch('S'):
            self.ilist.append(DoS())
            self.arg_stack_len += 1
            return True
        if self.advanceByMatch('C'):
            self.ilist.append(DoC())
            self.arg_stack_len += 1
            return True
        return False
    def doWS(self):
        return self.advanceByMatch(self.ws_re)
    def doInt(self):
        matched = self.advanceByMatch(self.int_re)
        if matched:
            self.ilist.append(IntLiteral(int(matched)))
            self.arg_stack_len+=1
        return matched
    def doS(self):
        self.ilist.append(DoS())
        self.arg_stack_len += 1
    def doC(self):
        self.ilist.append(DoC())
        self.arg_stack_len += 1
    def doD(self):
        self.grabPostFixArgument()
        self.ilist.append(DoD())
        self.arg_stack_len -= 2
    def doPlus(self):
        # Is this a "X+" filter or a "+X" appending to the pool?
        if self.arg_stack_len > 0:
            # This is an X+
            self.ilist.append(DoGeq())
        else:
            # This is a +X
            assert(self.grabPostFixArgument())
            self.ilist.append(DoPlusX())
        self.arg_stack_len -= 1
    def doMinus(self):
        if self.arg_stack_len > 0:
            # This is an X+
            self.ilist.append(DoLeq())
        else:
            # This is a +X
            assert(self.grabPostFixArgument())
            self.ilist.append(DoMinusX())
        self.arg_stack_len -= 1
    def doMult(self):
        assert(self.grabPostFixArgument())
        self.ilist.append(DoMult())
        self.arg_stack_len -= 1
    def doH(self):
        self.grabPostFixArgument()
        self.ilist.append(DoH())
        self.arg_stack_len -= 1
    def doL(self):
        self.grabPostFixArgument()
        self.ilist.append(DoL())
        self.arg_stack_len -= 1
    def doCurlyBracket(self):
        self.ilist.append(self.doCaptiveCurlyBracket())
    def doCaptiveCurlyBracket(self):
        sub = Interpreter(self.script_tail,
                          '}', self.nest_level + 1)
        sub.compile()
        self.script_tail = sub.script_tail
        if self.arg_stack_len < 1:
            self.ilist.append(IntLiteral(1))
            self.arg_stack_len += 1
        self.arg_stack_len -= 1
        return DoCurlyBlock(sub.ilist)
    def doSquareBracket(self):
        sub1 = Interpreter(self.script_tail,
                          ']', self.nest_level+1)
        sub1.compile()
        self.script_tail = sub1.script_tail
        ilist1 = sub1.ilist

        self.doWS()

        if self.script_tail[0] == '{':
            self.script_tail = self.script_tail[1:]
            captive_curly = self.doCaptiveCurlyBracket()
        else:
            captive_curly = None
        self.ilist.append(DoSquareBlock(ilist1, captive_curly))
    def doG(self):
        self.ilist.append(DoG())
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
        }
        while len(self.script_tail):
            next_char = self.script_tail[0]
            if next_char in single_letter_ops:
                self.script_tail = self.script_tail[1:]
                single_letter_ops[next_char]()
                continue
            if self.doWS(): continue
            if self.doInt(): continue
            if self.end_re and self.advanceByMatch(self.end_re):
                # We found the end condition, we rejoin the parent
                break
            raise SyntaxError("Can't find a valid next token!")
        return Executor(self.ilist)

import cProfile
import pstats

if 1:
    inter = Interpreter(open('test.txt').read())
    e = inter.compile()
    #e.run()
    cProfile.run('e.run()', 'out.dat')
    p = pstats.Stats('out.dat')
    p.sort_stats('cumulative')
    p.print_stats()
