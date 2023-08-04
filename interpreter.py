from enum import Enum
from typing import *
import random

def xDy(x, y)->List[int]:
    return [random.randint(1, y) for i in range(x)]

def process(script, starting_pool=None, indent_level=0)->List[int]:
    tail = script

    loaded_int = None
    loaded_subpool = None
    pool = [] if starting_pool is None else starting_pool

    def iPrint(*args):
        print('    '*indent_level, *args)

    def printPool():
        iPrint("Pool has %d dice, sums to %d"%(len(pool), sum(pool)))
        iPrint(pool)

    def cutHeadWhitespace(s):
        for i in range(len(s)):
            if not s[i].isspace():
                return s[i:]
        return ''

    def grabMatching(s, start_delim, end_delim):
        # We are assuming s starts immediately AFTER the first start delim
        # Returns the block of text from the start of s to the ending delim, and the tail after the ending delim.
        # Ending delim is lost.
        nest_count = 1
        for i in range(len(s)):
            if s[i] == start_delim:
                nest_count += 1
            if s[i] == end_delim:
                nest_count -= 1
                if nest_count == 0:
                    return s[:i], s[i+1:]
        raise Exception("Ending delimiter for %s not found!"%start_delim)

    def popInteger(s):
        # Check special case arguments first
        if len(s) == 0:
            return None, ''
        if s[0].upper() == 'S':
            return sum(pool), s
        if s[0].upper() == 'C':
            return len(pool), s
        i = 0
        while i < len(s) and s[i].isdigit():
            i += 1
        integer_part = s[:i]
        s = s[i:]
        return int(integer_part), s

    while tail:
        c = tail[0]
        tail = tail[1:]
        if c.isspace():
            continue
        if c.isdigit():
            assert (loaded_int is None)
            loaded_int, tail = popInteger(c+tail)
            continue
        if c.upper() == 'D':
            n_sides, tail = popInteger(tail)
            assert(loaded_int is not None)
            pool = xDy(loaded_int, n_sides)
            loaded_int = None
            continue
        if c == '<':
            thresh, tail = popInteger(cutHeadWhitespace(tail))
            pool = list(filter(lambda x: x < thresh, pool))
            continue
        if c == '>':
            thresh, tail = popInteger(cutHeadWhitespace(tail))
            pool = list(filter(lambda x: x > thresh, pool))
            continue
        if c == '*':
            mult, tail = popInteger(cutHeadWhitespace(tail))
            pool *= mult
            continue
        if c.upper() == 'S':
            assert(loaded_int is None)
            loaded_int = sum(pool)
            continue
        if c.upper() == 'C':
            assert (loaded_int is None)
            loaded_int = len(pool)
            continue
        if c.upper() == 'P':
            printPool()
            continue
        if c == '{':
            subscript, tail = grabMatching(tail, '{', '}')
            poolarg = None
            if loaded_subpool is None:
                poolarg = pool
            else:
                poolarg = loaded_subpool
                loaded_subpool = None
            reparg = 1
            if loaded_int is not None:
                reparg = loaded_int
                loaded_int = None
            for i in range(reparg):
                pool.extend(process(subscript, poolarg.copy(), indent_level+1))
            continue
        if c == '[':
            subscript, tail = grabMatching(tail, '[', ']')
            assert(loaded_subpool is None)
            loaded_subpool = process(subscript, pool.copy(), indent_level+1) # ONLY USE FILTERS IN THIS SUBSCRIPT
            for x in loaded_subpool:
                pool.remove(x)
            continue
        if c == '+':
            # Meaning is contextual, depends if it's a "+2" or "2+"
            if loaded_int is None:
                int_arg, tail = popInteger(cutHeadWhitespace(tail))
                pool = [x+int_arg for x in pool]
            else:
                pool = list(filter(lambda x: x >= loaded_int, pool))
                loaded_int = None
            continue
        if c == '-':
            # Meaning is contextual, depends if it's a "-2" or "2-"
            if loaded_int is None:
                int_arg, tail = popInteger(cutHeadWhitespace(tail))
                pool = [x-int_arg for x in pool]
            else:
                pool = list(filter(lambda x: x <= loaded_int, pool))
                loaded_int = None
            continue
        if c == '#':
            # Comment
            comment, tail = grabMatching(tail, None, '\n')
            iPrint("#", comment)
            printPool()
            continue
        if c.upper() == 'H':
            assert(loaded_int is None)
            int_arg, tail = popInteger(cutHeadWhitespace(tail))
            pool = sorted(pool)[-int_arg:]
            continue
        if c.upper() == 'L':
            assert (loaded_int is None)
            int_arg, tail = popInteger(cutHeadWhitespace(tail))
            pool = sorted(pool)[:int_arg]
            continue
        if c.upper() == 'A':
            assert (loaded_int is None)
            int_arg, tail = popInteger(cutHeadWhitespace(tail))
            pool.append(int_arg)
            continue
    # Special case: The user has loaded up an argument before the end of the script, we assume they want that returned
    # instead of the pool.
    if loaded_int is not None:
        return [loaded_int]
    return pool

#test_script = "10D3 P SD6 P [1-]{CD6} [6+]{*3}  P 5+ CD6 P 5+ P"
process(open('test.txt').read())