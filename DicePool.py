from collections import defaultdict
from typing import Iterable

class DicePool:
    def __init__(self, dice:Iterable[int]=None, init_pool=None):
        self.vals = defaultdict(int) if init_pool is None else init_pool.copy()
        if dice is not None:
            self.addDice(dice)
    def clear(self):
        self.vals = defaultdict(int)
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
        lines = []
        for i in range(low, high+1):
            lines.append('%d:%d'%(i, self.vals[i]))
        return ' - '.join(lines)
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
    def getEqSubset(self, val):
        ss = defaultdict(int)
        ss[val] = self.vals[val]
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
    def getCountOfVal(self, val):
        return self.vals[val]
    def copy(self):
        return DicePool(init_pool=self.vals)
    def asList(self):
        rval = []
        for k, v in self.vals.items():
            for i in range(v):
                rval.append(k)
        return rval