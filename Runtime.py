from dataclasses import dataclass
from DicePool import DicePool
from Graph import makeBarGraph
from numpy import random
from typing import List, Iterable, Union

#FIXME: Not reset between invocations
VERBOSITY_GLOBAL = 0

@dataclass
class ExecState:
    pool        : DicePool
    arg_stack   : List[int]
    nest_level  : int
    debug_script: str
    def shouldPrint(self):
        global VERBOSITY_GLOBAL
        return VERBOSITY_GLOBAL > self.nest_level
    def nestPrint(self, *args):
        print('    '*self.nest_level, *args)

class RunnableUnit:
    def setDebugParams(self, script_i:int):
        self.script_i = script_i # Index of this instruction in the script
    def run(self, estate:ExecState):
        raise NotImplemented("Should be overridden by subclass")

class Executor:
    def __init__(self, instructions:Iterable[RunnableUnit], debug_script:str):
        self.instructions = instructions
        self.debug_script = debug_script
    def getGlobalScriptLineForPosition(self, pos):
        total_len = 0
        for lineno, line in enumerate(self.debug_script.splitlines()):
            total_len += len(line) + 1
            if total_len >= pos:
                return lineno+1, line # Line numbers count from 1, not 0
        return 0, ''
    def run(self, pool_override:DicePool=None, nest_level=0)->ExecState:
        s = ExecState(DicePool() if pool_override is None else pool_override.copy(), [],
                      nest_level, self.debug_script)
        for inst in self.instructions:
            try:
                inst.run(s) # The instructions will mutate s
            except Exception as e:
                lineno, line = self.getGlobalScriptLineForPosition(inst.script_i)
                print("Runtime error on line %d:"%lineno)
                print(line)
                raise(e)
        return s

class IntValue(RunnableUnit): pass

class IntLiteral(IntValue):
    def __init__(self, val:int):
        self.val = val
    def run(self, estate:ExecState):
        estate.arg_stack.append(self.val)

class RunS(IntValue):
    def run(self, estate:ExecState):
        s = estate.pool.sum()
        if estate.shouldPrint():
            estate.nestPrint("Sum is %d"%s)
        estate.arg_stack.append(s)


class RunC(IntValue):
    def run(self, estate:ExecState):
        c = len(estate.pool)
        estate.arg_stack.append(c)
        if estate.shouldPrint():
            estate.nestPrint("Count is %d"%c)

class RunD(RunnableUnit):
    def run(self, estate:ExecState):
        n_sides = estate.arg_stack.pop()
        n_dice  = estate.arg_stack.pop()
        estate.pool = DicePool(random.randint(1, n_sides + 1, n_dice))
        if estate.shouldPrint():
            estate.nestPrint("Rolled %dD%d, got:" % (n_dice, n_sides))
            estate.nestPrint(estate.pool)

class RunGeq(RunnableUnit):
    def run(self, estate:ExecState):
        thresh = estate.arg_stack.pop()
        start_len = len(estate.pool)
        estate.pool = estate.pool.getGeqSubset(thresh)
        if estate.shouldPrint():
            estate.nestPrint("Pass on %d+" % thresh)
            end_len = len(estate.pool)
            removed = start_len - end_len
            estate.nestPrint("Removed %d dice, leaving %d" % (removed, end_len))

class RunPlusX(RunnableUnit):
    def run(self, estate:ExecState):
        die = estate.arg_stack.pop()
        estate.pool.addDie(die)
        if estate.shouldPrint():
            estate.nestPrint("Added +%d to pool" % die)

class RunLeq(RunnableUnit):
    def run(self, estate:ExecState):
        thresh = estate.arg_stack.pop()
        start_len = len(estate.pool)
        estate.pool = estate.pool.getLeqSubset(thresh)
        if estate.shouldPrint():
            estate.nestPrint("Pass on %d-" % thresh)
            end_len = len(estate.pool)
            removed = start_len - end_len
            estate.nestPrint("Removed %d dice, leaving %d" % (removed, end_len))

class RunMult(RunnableUnit):
    def run(self, estate:ExecState):
        factor = estate.arg_stack.pop()
        estate.pool.mulInt(factor)
        if estate.shouldPrint():
            estate.nestPrint("Multiplied pool by %d"%factor)

class RunMinusX(RunnableUnit):
    def run(self, estate:ExecState):
        die = -1*estate.arg_stack.pop()
        estate.pool.addDie(die)
        if estate.shouldPrint():
            estate.nestPrint("Added %d to pool" % die)

class RunH(RunnableUnit):
    def run(self, estate:ExecState):
        count = estate.arg_stack.pop()
        estate.pool = estate.pool.getTop(count)
        if estate.shouldPrint():
            estate.nestPrint("Grabbing top %d dice"%count)

class RunL(RunnableUnit):
    def run(self, estate:ExecState):
        count = estate.arg_stack.pop()
        estate.pool = estate.pool.getBottom(count)
        if estate.shouldPrint():
            estate.nestPrint("Grabbing bottom %d dice"%count)

class RunV(RunnableUnit):
    def run(self, estate:ExecState):
        global VERBOSITY_GLOBAL
        VERBOSITY_GLOBAL = estate.arg_stack.pop()
        estate.nestPrint("Verbosity set to %d"%VERBOSITY_GLOBAL)

class RunG(RunnableUnit):
    def run(self, estate:ExecState):
        if estate.shouldPrint():
            estate.nestPrint("Graphing...")
        makeBarGraph(estate.pool)

class RunCurlyBlock(RunnableUnit):
    def __init__(self, ilist:Iterable[RunnableUnit]):
        self.ilist = ilist
    def run(self, estate:ExecState, pool_override:DicePool=None):
        e = Executor(self.ilist, estate.debug_script)
        reps = estate.arg_stack.pop()
        if pool_override is not None:
            pool_arg = pool_override.copy()
        else:
            pool_arg = estate.pool.copy()
            estate.pool.clear()
        if reps == 0:
            if estate.shouldPrint():
                estate.nestPrint("Rep target is 0, not running sub block")
            return
        agg_pool = DicePool()
        for i in range(reps):
            if estate.shouldPrint():
                estate.nestPrint("Sub-block run %d of %d" % (i,reps))
            sub_s = e.run(pool_arg, estate.nest_level+1)
            if len(sub_s.arg_stack):
                agg_pool.addDice(sub_s.arg_stack)
            else:
                agg_pool.addPool(sub_s.pool)
        estate.pool.addPool(agg_pool)
        if estate.shouldPrint():
            estate.nestPrint("Sub-block finished %d reps, added %d values" %(reps,len(agg_pool)))

class RunSquareBlock(RunnableUnit):
    def __init__(self, filt_ilist:Iterable[RunnableUnit], curly_block:Union[RunCurlyBlock, None]):
        self.filt_ilist = filt_ilist
        self.curly_block = curly_block
    def run(self, estate:ExecState):
        e = Executor(self.filt_ilist, estate.debug_script)
        substate = e.run(estate.pool, estate.nest_level+1)
        if estate.shouldPrint():
            estate.nestPrint("Removing %d values from outer pool"%len(substate.pool))
        estate.pool.subPool(substate.pool)
        if self.curly_block is not None:
            if estate.shouldPrint():
                estate.nestPrint("Passing %d values to inner code block"%len(substate.pool))
            self.curly_block.run(estate, substate.pool)
