import re
from graph import makeBarGraph
from numpy import random
from typing import *
from collections import defaultdict

# Started at 2.75 runtime
# Now at 2.41

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
        return sum
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
        return DicePool(init_pool=self.vals.copy())
    def asList(self):
        rval = []
        for k, v in self.vals.items():
            for i in range(v):
                rval.append(k)
        return rval

class Interpreter:
    ws_re         = re.compile(r'\s+')
    int_re        = re.compile(r'\d+')
    s_re          = re.compile(r'S')
    c_re          = re.compile(r'C')
    d_re          = re.compile(r'D')
    plus_re       = re.compile(r'\+')
    minus_re      = re.compile(r'\-')
    mult_re       = re.compile(r'\*')
    h_re          = re.compile(r'H')
    l_re          = re.compile(r'L')
    g_re          = re.compile(r'G')
    start_curly_re = re.compile(r'\{')
    start_square_re = re.compile(r'\[')
    end_curly_re = re.compile(r'\}')
    end_square_re = re.compile(r'\]')

    def __init__(self, script, pool=None, end_re=None, nest_level=None):
        # Purge all comments from the script
        script = ''.join(re.split(r'#.*\n', script+'\n'))
        self.original_script = script
        self.script_tail = script
        self.pool = pool if pool else DicePool()
        self.arg_stack = [] # Stack of integers
        self.end_re = end_re if end_re else None
        self.nest_level = nest_level if nest_level is not None else 0
        self.verbose = 0
    def print(self, *args):
        if not self.verbose:
            return
        print(self.nest_level * '    ', *args)
    def advanceByMatch(self, exp:Union[re.Pattern,str])->str:
        if type(exp) == str:
            if self.script_tail[0] == exp:
                matching = exp
        else:
            matching = re.match(exp, self.script_tail)
            if matching is None:
                return None
            matching = matching.group()
        rval = self.script_tail[:len(matching)]
        self.script_tail = self.script_tail[len(matching):]
        return rval
    def grabPostFixArgument(self):
        # This is kinda ugly b/c we need to break the order of interpretation...
        self.advanceByMatch(self.ws_re)
        # The only valid post-fix values are integer literals, S or C
        if matched := self.advanceByMatch(self.int_re):
            return int(matched)
        if self.advanceByMatch(self.s_re):
            return self.pool.sum()
        if self.advanceByMatch(self.c_re):
            return len(self.pool)
        return None
    def doWS(self):
        return self.advanceByMatch(self.ws_re)
    def doInt(self):
        matched = self.advanceByMatch(self.int_re)
        if matched:
            self.arg_stack.append(int(matched))
        return matched
    def doS(self):
        matched = self.advanceByMatch(self.s_re)
        if matched:
            self.arg_stack.append(self.pool.sum())
            self.print("Sum is %d" % self.arg_stack[0])
        return matched
    def doC(self):
        matched = self.advanceByMatch(self.c_re)
        if matched:
            self.arg_stack.append(len(self.pool))
            self.print("Count is %d" % self.arg_stack[0])
        return matched
    def doD(self):
        matched = self.advanceByMatch(self.d_re)
        if matched:
            n_dice  = self.arg_stack.pop()
            n_sides = self.grabPostFixArgument()
            self.pool = DicePool(random.randint(1, n_sides+1, n_dice))
            self.print("Rolled %dD%d, got:"%(n_dice, n_sides))
            self.print(self.pool)
        return matched
    def doPlus(self):
        matched = self.advanceByMatch(self.plus_re)
        if matched:
            # Is this a "X+" filter or a "+X" appending to the pool?
            if len(self.arg_stack):
                # This is an X+
                thresh = self.arg_stack.pop()
                start_len = len(self.pool)
                self.pool = self.pool.getGeqSubset(thresh)
                self.print("Pass on %d+"%thresh)
                end_len = len(self.pool)
                removed = start_len - end_len
                self.print("Removed %d dice, leaving %d"%(removed,end_len))
            else:
                # This is a +X
                to_append = self.grabPostFixArgument()
                self.pool.addDie(to_append)
                self.print("Added +%d to pool"%to_append)
        return matched
    def doMinus(self):
        matched = self.advanceByMatch(self.minus_re)
        if matched:
            if len(self.arg_stack):
                thresh = self.arg_stack.pop()
                start_len = len(self.pool)
                self.pool = self.pool.getLeqSubset(thresh)
                self.print("Pass on %d-" % thresh)
                end_len = len(self.pool)
                removed = start_len - end_len
                self.print("Removed %d dice, leaving %d" % (removed, end_len))
            else:
                # This is a -X
                to_append = self.grabPostFixArgument()
                to_append *= -1
                self.pool.add(to_append)
                self.print("Added %d to pool" % to_append)
        return matched
    def doMult(self):
        matched = self.advanceByMatch(self.mult_re)
        if matched:
            factor = self.grabPostFixArgument()
            self.pool.mulInt(factor)
            self.print("Multiplied pool by %d, pool has %d elements"%(factor, len(self.pool)))
        return matched
    def doH(self):
        matched = self.advanceByMatch(self.h_re)
        if matched:
            count = self.grabPostFixArgument()
            self.pool = self.pool.getTop(count)
            self.print("Grabbed %d highest elements"%count)
        return matched
    def doL(self):
        matched = self.advanceByMatch(self.l_re)
        if matched:
            count = self.grabPostFixArgument()
            self.pool = self.pool.getBottom(count)
            self.print("Grabbed %d lowest elements" % count)
        return matched
    def doCurlyBracket(self, pool_override=None):
        matched = self.advanceByMatch(self.start_curly_re)
        if matched:
            repeat_count = self.arg_stack.pop() if len(self.arg_stack) else 1
            new_tail = None
            new_entries = DicePool()
            for i in range(repeat_count):
                self.print("{} run %d"%i)
                sub = Interpreter(self.script_tail,
                                  pool_override.copy() if pool_override is not None else self.pool.copy(),
                                  self.end_curly_re, self.nest_level+1)
                sub.run()
                new_tail = sub.script_tail
                # By convention: If the sub left arguments in its stack, append those to the pool.
                # Otherwise, append the subpool to the pool.
                if len(sub.arg_stack):
                    new_entries.addDice(sub.arg_stack)
                else:
                    new_entries.addPool(sub.pool)
            self.print("{} finished, adding %d new entries:"%len(new_entries))
            self.print(new_entries)
            self.pool.addPool(new_entries)
            self.script_tail = new_tail
        return matched
    def doSquareBracket(self):
        matched = self.advanceByMatch(self.start_square_re)
        if matched:
            self.print("[] starting")
            sub = Interpreter(self.script_tail,
                              self.pool.copy(),
                              self.end_square_re, self.nest_level+1)
            sub.run()
            self.script_tail = sub.script_tail

            # Remove all elements of the subpool from the main pool
            self.pool.subPool(sub.pool)
            self.print("[] finished, subpool has %d entries:" % len(sub.pool))
            self.print(sub.pool)

            # If there is a curly block after this, we need to pass it the sub pool
            self.doWS()
            self.doCurlyBracket(sub.pool)
        return matched
    def doG(self):
        matched = self.advanceByMatch(self.g_re)
        if matched:
            self.print("Graphing...")
            makeBarGraph(self.pool.asList())
        return matched
    def run(self):
        keyword_checkers = [
            self.doWS,
            self.doInt,
            self.doS,
            self.doC,
            self.doD,
            self.doPlus,
            self.doMinus,
            self.doCurlyBracket,
            self.doSquareBracket,
            self.doMult,
            self.doH,
            self.doL,
            self.doG,
        ]
        while len(self.script_tail):
            found_keyword = False
            for checker in keyword_checkers:
                if checker():
                    found_keyword = True
                    break
            if found_keyword: continue
            if self.end_re and self.advanceByMatch(self.end_re):
                # We found the end condition, we rejoin the parent
                break
            raise SyntaxError("Can't find a valid next token!")

import cProfile
import pstats

if 1:
    inter = Interpreter(open('test.txt').read())
    #inter.run()
    cProfile.run('inter.run()', 'out.dat')
    p = pstats.Stats('out.dat')
    p.sort_stats('cumulative')
    p.print_stats()
