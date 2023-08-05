import re
from graph import makeBarGraph
from numpy import random

class Interpreter:
    ws_re  = r'\s+'
    int_re = r'\d+'
    s_re   = r'S'
    c_re   = r'C'
    end_curly_re = r'\}'
    end_square_re = r'\]'
    def __init__(self, script, pool=None, end_re=None, nest_level=None):
        # Purge all comments from the script
        script = ''.join(re.split(r'#.*\n', script+'\n'))
        self.original_script = script
        self.script_tail = script
        self.pool = pool if pool else []
        self.arg_stack = [] # Stack of integers
        self.end_re = end_re if end_re else None
        self.nest_level = nest_level if nest_level is not None else 0
        self.verbose = 0
    def print(self, *args):
        if not self.verbose:
            return
        print(self.nest_level * '    ', *args)
    def advanceByMatch(self, exp)->str:
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
            return sum(self.pool)
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
            self.arg_stack.append(sum(self.pool))
            self.print("Sum is %d" % self.arg_stack[0])
        return matched
    def doC(self):
        matched = self.advanceByMatch(self.c_re)
        if matched:
            self.arg_stack.append(len(self.pool))
            self.print("Count is %d" % self.arg_stack[0])
        return matched
    def doD(self):
        matched = self.advanceByMatch(r'D')
        if matched:
            n_dice  = self.arg_stack.pop()
            n_sides = self.grabPostFixArgument()
            self.pool = list(random.randint(1, n_sides+1, n_dice))
            self.print("Rolled %dD%d, got:"%(n_dice, n_sides))
            self.print(self.pool)
        return matched
    def doPlus(self):
        matched = self.advanceByMatch(r'\+')
        if matched:
            # Is this a "X+" filter or a "+X" appending to the pool?
            if len(self.arg_stack):
                # This is an X+
                thresh = self.arg_stack.pop()
                to_remove = list(filter(lambda x: x < thresh, self.pool))
                for x in to_remove:
                    self.pool.remove(x)
                # This is basically a 2nd argument register... Maybe find a more elegant way
                self.subpool = to_remove
                self.print("Pass on %d+"%thresh)
                self.print("Removed %d dice, leaving %d"%(len(to_remove),len(self.pool)))
            else:
                # This is a +X
                to_append = self.grabPostFixArgument()
                self.pool.append(to_append)
                self.print("Added +%d to pool"%to_append)
        return matched
    def doMinus(self):
        matched = self.advanceByMatch(r'\-')
        if matched:
            if len(self.arg_stack):
                thresh = self.arg_stack.pop()
                to_remove = list(filter(lambda x: x > thresh, self.pool))
                for x in to_remove:
                    self.pool.remove(x)
                # This is basically a 2nd argument register... Maybe find a more elegant way
                self.subpool = to_remove
                self.print("Pass on %d-" % thresh)
                self.print("Removed %d dice, leaving %d"%(len(to_remove),len(self.pool)))
            else:
                # This is a -X
                to_append = self.grabPostFixArgument()
                to_append *= -1
                self.pool.append(to_append)
                self.print("Added %d to pool" % to_append)
        return matched
    def doMult(self):
        matched = self.advanceByMatch(r'\*')
        if matched:
            factor = self.grabPostFixArgument()
            self.pool *= factor
            self.print("Multiplied pool by %d, pool has %d elements"%(factor, len(self.pool)))
        return matched
    def doH(self):
        matched = self.advanceByMatch(r'H')
        if matched:
            count = self.grabPostFixArgument()
            self.pool = sorted(self.pool)[-count:]
            self.print("Grabbed %d highest elements"%count)
        return matched
    def doL(self):
        matched = self.advanceByMatch(r'L')
        if matched:
            count = self.grabPostFixArgument()
            self.pool = sorted(self.pool)[:count]
            self.print("Grabbed %d lowest elements" % count)
        return matched
    def doCurlyBracket(self, pool_override=None):
        matched = self.advanceByMatch(r'{')
        if matched:
            repeat_count = self.arg_stack.pop() if len(self.arg_stack) else 1
            new_tail = None
            new_entries = []
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
                    new_entries.extend(sub.arg_stack)
                else:
                    new_entries.extend(sub.pool)
            self.print("{} finished, adding %d new entries:"%len(new_entries))
            self.print(new_entries)
            self.pool.extend(new_entries)
            self.subpool = None
            self.script_tail = new_tail
        return matched
    def doSquareBracket(self):
        matched = self.advanceByMatch(r'\[')
        if matched:
            self.print("[] starting")
            sub = Interpreter(self.script_tail,
                              self.pool.copy(),
                              self.end_square_re, self.nest_level+1)
            sub.run()
            self.script_tail = sub.script_tail

            # Remove all elements of the subpool from the main pool
            for x in sub.pool:
                self.pool.remove(x)
            self.print("[] finished, subpool has %d entries:" % len(sub.pool))
            self.print(sub.pool)

            # If there is a curly block after this, we need to pass it the sub pool
            self.doWS()
            self.doCurlyBracket(sub.pool)
        return matched
    def doG(self):
        matched = self.advanceByMatch(r'G')
        if matched:
            self.print("Graphing...")
            makeBarGraph(self.pool)
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

if 1:
    inter = Interpreter(open('test.txt').read())
    inter.run()
