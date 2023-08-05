import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
from typing import *

def findQuartiles(pool)->Tuple[int,int,int]:
    sp = sorted(pool)
    l = len(pool)
    def findCenterMassForValue(val)->float:
        left_edge = 0
        right_edge = l
        for i in range(0, l):
            if sp[i] == val:
                left_edge = i
                break
        for i in range(left_edge,l):
            if sp[i] != val:
                right_edge = i
                break
        return (left_edge+right_edge)/2
    def findInterpolatedValueFromIndex(i):
        val = sp[int(i+0.5)]
        cm = findCenterMassForValue(val)
        other_val = val+1 if i > cm else val-1
        other_cm = findCenterMassForValue(other_val)
        rval = val * abs(other_cm - i) + other_val * abs(cm - i)
        rval /= abs(cm - other_cm)
        return rval
    return findInterpolatedValueFromIndex(l/4), findInterpolatedValueFromIndex(l/2), findInterpolatedValueFromIndex(3*l/4)




def makeBarGraph(pool:List[int]):
    counter = Counter(pool)
    plt.figure(figsize=(10, 5))
    plt.bar(counter.keys(), counter.values(), color='skyblue', width=0.975)
    q1, q2, q3 = findQuartiles(pool)
    plt.axvline(x=q1, color='green', linestyle='--', label='Q1: %0.2f'%q1)
    plt.axvline(x=q2, color='red',   linestyle='--', label='Q2: %0.2f'%q2)
    plt.axvline(x=q3, color='blue',  linestyle='--', label='Q3: %0.2f'%q3)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('Pool distribution for %d values'%len(pool))
    plt.xticks(range(min(counter.keys()), max(counter.keys()) + 1))
    plt.legend()
    plt.grid(axis='y', linestyle='--')
    plt.show()

if __name__ == "__main__":
    makeBarGraph([1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,3,3])