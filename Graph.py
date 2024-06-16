import matplotlib.pyplot as plt
from collections import Counter
from typing import *

def findQuartiles(pool, val_increment=1.0)->Tuple[float, float, float]:
    # Find quartiles by graph area method.
    # IE first quartile should have 1/4 of the total bar graph area to the left
    # This assumes all bars are 1 unit wide. In cases where the histogram is regularly gappy,
    # eg. when there are only EVEN bars, it might be argued that the interpolated values should
    # be able to appear in the gaps, which this function will not do.
    l = len(pool)
    counter = Counter(pool)
    def helper(frac)->float:
        # Return a value such that frac amount of graph area is to the left of the argument
        area_target = l * frac
        area = 0.0
        val = min(counter)
        while True:
            new_area = area + counter[val]
            if new_area > area_target:
                # This iteration would put us over the area_target
                break
            area = new_area
            val += 1
        # val represents the bar which must now be sub-divided
        bar_height = counter[val] / val_increment
        bar_left_edge = val - (0.5*val_increment)
        area_delta = area_target - area
        rval = bar_left_edge + (area_delta / bar_height)
        return rval
    return helper(0.25), helper(0.5), helper(0.75)

def determineIncrement(counter:Counter)->int:
    # Create a new counter of the deltas between adjacent values
    sorted_unique_vals = sorted(counter.keys())
    if len(sorted_unique_vals) == 1: return 1
    sorted_unique_deltas = sorted(sorted_unique_vals[i+1]-sorted_unique_vals[i] for i in range(len(sorted_unique_vals)-1))
    # Now we need to find the largest integer which divides into all deltas
    for span in range(sorted_unique_deltas[0], 0, -1):
        if all(d % span == 0 for d in sorted_unique_deltas):
            return span
    assert(False, "Should never get here!")

def makeBarGraph(pool):
    counter = Counter(pool)
    increment = determineIncrement(counter)
    plt.figure(figsize=(10, 5))
    pool_len = len(pool)
    percentages = [100*v / pool_len for v in counter.values()]
    plt.bar(counter.keys(), percentages, color='skyblue', width=increment-0.025)
    q1, q2, q3 = findQuartiles(pool, increment)
    plt.axvline(x=q1, color='green', linestyle='--', label='Q1: %0.2f'%q1)
    plt.axvline(x=q2, color='red',   linestyle='--', label='Q2: %0.2f'%q2)
    plt.axvline(x=q3, color='blue',  linestyle='--', label='Q3: %0.2f'%q3)
    plt.xlabel('Value')
    plt.ylabel('Frequency (%)')
    plt.title('Pool distribution for %d values'%len(pool))
    plt.xticks(range(min(counter.keys()), max(counter.keys()) + 1, increment))
    plt.legend()
    plt.grid(axis='y', linestyle='--')
    plt.show()

if __name__ == "__main__":
    #makeBarGraph([1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,3,3])
    makeBarGraph([1]*10 + [3]*20 + [5]*10)
    makeBarGraph([1] * 10)
    makeBarGraph([1] * 10 + [4] * 10 + [7] * 10)
    makeBarGraph([1] * 10 + [4] * 10 + [7] * 10 + [9] * 10)
    makeBarGraph([1] * 10 + [3] * 10 + [5] * 10)
