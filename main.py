import random
from typing import *
from time import sleep
from static import loc_names, warp_rift_events

def stdout(*args):
    print(*args, end='', flush=True)

def is_affirmative(s):
    affirmative_strings = {'yes', 'y', 'ok', 'okay', 'sure', 'affirmative', 'whatever', 'yup', 'you bet', 'you betcha', 'whatev', 'k'}
    return s.lower() in affirmative_strings

def pool_has_sequence(pool, seq):
    for i in range(len(pool)-len(seq)):
        subseq = pool[i+len(seq)]
        matches = [subseq[j] == seq[j] for j in range(len(seq))]
        if sum(matches) == 0:
            return True
    return False

def pool_ends_w_seq(pool, seq):
    if len(pool) < len(seq):
        return False
    subseq = pool[-len(seq):]
    matches = [subseq[j] == seq[j] for j in range(len(seq))]
    if all(matches):
        return True
    return False

def warpRift():
    print(random.choice(warp_rift_events))

def Dx(x)->int: return random.randint(1, x)

def xDy(x, y)->List[int]:
    rval = []
    for i in range(x):
        roll = Dx(y)
        stdout("%d%s" % (roll, Dx(3)*" "))
        if random.random() < 0.05:
            print()
        while random.random() < 0.01:
            choice = input("Oh no it fell %s! Does it count?" % random.choice(loc_names))
            choice = is_affirmative(choice)
            if random.random() < 0.5:
                print("Nah, I do what I want")
                choice = not choice
            if choice:
                print("Sorry Joe, it counts")
                break
            print("Rerolling that one")
            roll = Dx(y)
            stdout("%d%s" % (roll, Dx(3)*" "))
        rval.append(roll)
        if pool_ends_w_seq(rval, [6,6,6,6]):
            print("A WARP RIFT HAS OPENED")
            warpRift()
            while True:
                choice = input("CONFIRM THAT YOU HAVE RECEIVED THIS DIRECTIVE")
                if is_affirmative(choice):
                    break
        sleep(0.1)
    print()
    return rval

class DicePool:
    def __init__(self, n_dice=0, n_sides=6):
        self.stack = [] # List of list[int] for stashing parts of rolls. Useful for skipping filters on subsets of rolls (like lethal hits, exploding wounds)
        self.roll(n_dice, n_sides)
    def append(self, pool:List[int]):
        print("Adding %d dice manually to the pool"%len(pool))
        self.pool.extend(pool)
        self.printPool()
    def stackPush(self, pool:List[int]):
        print("Pushing %d dice to the stack"%len(pool))
        self.stack.append(pool)
    def stackPop(self):
        print("Popping %d dice from the stack"%len(self.stack[-1]))
        self.pool.extend(self.stack.pop())
    def printPool(self):
        print("Pool has %dD%d:"%(len(self.pool),self.n_sides))
        for i in range(1, self.n_sides + 1):
            print("    %ds: %02d : %s" % (i, self.pool.count(i), self.pool.count(i)*"|"))
    def roll(self, n_dice=None, n_sides=None):
        if n_dice is None:
            n_dice = len(self.pool)
        if n_sides is None:
            n_sides = self.n_sides
        print("Rolling %dD%d"%(n_dice, n_sides))
        self.pool = xDy(n_dice, n_sides)
        self.n_sides = n_sides
        self.printPool()
    def reroll(self):
        self.roll(None, None)
    def addRoll(self, n_dice):
        print("Adding %dD%d" % (n_dice, self.n_sides))
        self.pool.extend(xDy(n_dice, self.n_sides))
        self.printPool()
    def geq(self, val:int):
        print("Pass on %d+"%val)
        rval = []
        for die in self.pool.copy():
            if die < val:
                self.pool.remove(die)
                rval.append(die)
        print("Removed %dD%d, leaving %dD%d"%(len(rval),self.n_sides,len(self.pool),self.n_sides))
        return rval
    def leq(self, val:int):
        print("Pass on %d-" % val)
        rval = []
        for die in self.pool.copy():
            if die > val:
                self.pool.remove(die)
                rval.append(die)
        print("Removed %dD%d, leaving %dD%d"%(len(rval),self.n_sides,len(self.pool),self.n_sides))
        return rval
    def rerollLeq(self,val):
        print("Reroll %d-"%val)
        to_reroll = len(self.geq(val+1))
        self.addRoll(to_reroll)
    def countVal(self, val:int):
        return self.pool.count(val)
    def len(self):
        return len(self.pool)
    def sum(self):
        return sum(self.pool)

########### ALL ROLL PARAMETERS HERE ###############

critical_hit_val = 6
critical_wound_val = 6

lethal_hits = False
devastating_wounds = False
sustained_hits = 0
reroll_crit_fail_hit   = False
reroll_crit_fail_wound = False

n_attacks = 30
to_hit = 6       # Hit on X+
to_wound = 5     # Wound on X+
armor_save = 3   # Save on X+. If unused, set to 7
feel_no_pain = 7 # Save on X+. If unused, set to 7
wounds_to_damage = lambda wounds: 1*wounds#sum(Dx(6)+6 for x in range(wounds))

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    input("ROLL %d DICE TO HIT..."%n_attacks)
    pool = DicePool(n_attacks)
    if reroll_crit_fail_hit:
        input("REROLL CRITICAL HIT FAILURES")
        pool.rerollLeq(1)
    if lethal_hits or sustained_hits:
        # This logic is necessary because of the way critical hits and sustained hits interact
        # lethal hits must ONLY apply to the native 6s, not sustained hits
        # Filter out critical hits
        critical_hits = pool.leq(critical_hit_val-1)
        if lethal_hits:
            print("STASHING LETHAL HITS")
            pool.stackPush(critical_hits)
        else:
            # Non-lethal hits, they go back in the primary pool
            pool.append(critical_hits)
        if sustained_hits:
            print("SUSTAINED HITS %d"%sustained_hits)
            to_append = []
            for i in range(sustained_hits):
                to_append.extend([6 for x in range(len(critical_hits))])
            pool.append(to_append)
    print("HIT ON %d+"%to_hit)
    pool.geq(to_hit)
    input("ROLL %d DICE TO WOUND..."%pool.len())
    pool.reroll()
    if lethal_hits:
        pool.stackPop()
    pool.geq(to_wound)
    if devastating_wounds:
        # Stash devastating wounds
        print("STASHING DEVASTATING WOUNDS")
        pool.stackPush(pool.leq(critical_wound_val-1))
    if armor_save < 7:
        input("ROLL %d DICE FOR ARMOR SAVE..."%pool.len())
        pool.reroll()
        pool.leq(armor_save-1)
    if devastating_wounds:
        pool.stackPop()
    print("%d UNSAVED WOUND ROLLS"%len(pool.pool))
    damage = wounds_to_damage(pool.len())
    print("Expands into %d damage"%damage)
    if feel_no_pain < 7:
        input("ROLL %d DICE FOR FEEL NO PAIN..."%damage)
        pool.roll(damage, 6)
        pool.leq(feel_no_pain-1)
    print("%d painful wounds"%damage)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
