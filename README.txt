This language is intended for simulating dice rolls and plotting results. The input is a test file, which is compiled
to an intermediate format and executed.

Core concepts:
The pool: This is an unordered collection of integer values. Integer values can be repeated.
The argument stack: This is a stack of integers which operators will push and pop values to/from

An execution context has exactly one pool and exactly one argument stack. An execution context may contain nested
contexts with their own pools and stacks.

Whitespace:
All whitespace is ignored

Comments:
Anything between a '#' and a newline is ignored

Integer types:
The following tokens can be used anywhere an integer type is called for:
Integer literal, like "123" or "9": This will be placed directly on the stack
S: This will take the sum of the pool and put it on the stack
C: This will take the number of values in the pool and put it on the stack

Operators:
Instructions are all single characters. Most instructions require an argument or two.
Arguments are popped from the stack, with some instructions allowing a post-fix argument (like the 3 in "H3")
xDy: This is the dice rolling workhorse. It accepts two arguments, one prefix and one postfix, eg. 3D6 or CD3.
D will clear the pool and replace it with 'x' integers between 1 and 'y' inclusive.
+: The + operator is sensitive to context. If there is no argument on the stack, it will grab a post-fix value
and be interpreted as a "+X", where X is an integer type which will be appended to the active pool.
If there is an argument on the stack, it will be interpreted as an "X+", which will reject all values from the pool less than X
-: This operator is just like the + operator, but reversed
*x: Repeats the pool X times. So if the pool is [1,2,3] and the interpreter executes a "*3",
the pool becomes [1,2,3,1,2,3,1,2,3]
Hx: Reduce the pool to the x highest values
Lx: Reduce the pool to the x lowest values
Vx: Set verbosity level to x. Statements with a nesting level below the verbosity level will print their output. V0 prints nothing.
G: Produce a bar graph showing the present distribution of the pool

Nesting and subpools:
x{ subscript }: Curly brackets do the following:
1. Copy the present pool into a new execution context, then clear the main pool.
2. Execute the subscript in that context
3. If the subcontext terminates with arguments in its stack, the subcontext's argument stack is appended to the main pool.
   If it terminates without arguments in its stack, the subcontext's pool is appended to the main pool.
If x is present, steps 2 and 3 will be repeated x times, with step 2 always receiving the same value.

[ filter script ]: Square brackets do the following:
1. Copy the present pool into a new execution context
2. Execute the filter script in that context
3. Remove the subcontext's pool from the main pool
Note that since an error will occur if you try to remove values not present in the main pool, the subscript should only
be a filtering operation. It effectively inverts the filter operation.

x[ filter script ]{ subscript }: This is a compound statement which splits the main pool and performs operations on a subset of it
1. Copy the present pool into a new execution context
2. Run the filter script in that context
3. Remove the filter subcontext's pool from the main pool
4. Handle the curly brackets as normal, EXCEPT that instead of receiving a copy of the main pool it receives the filtered results.
   The curly brackets will not clear the main pool when executed in this way.

Examples:

# Make a graph of the sum of 1000 pairs of D6 rolls
1000 { 2D6 S } G

# Make a graph 1000 3D6 rolls, keeping only the highest two dice
1000 { 3D6 H2 S } G

# Warhammer example: Roll 6x(D3+1) hit dice, hitting on 5s with exploding 6s, wounding on 6s with rerolled misses,
# armor save 5+, 2 damage per wound, 6+ feel no pain
V2         # Turn on verbosity 2 so we can see prints
6{1D3+1 S} # Roll for number of attacks
SD6        # Sum, roll to hit
[6+]{*2}   # Explode 6s
5+         # Hit on 5+
CD6        # Roll to wound
[[6+]]{CD6}# Reroll everything that fails 6+
6+         # Pass on 6+
CD6        # Roll armor save
[5+]       # Remove 5+ (saved)
*2         # 2 damage per wound
CD6        # Roll FNP
[6+]       # Remove 6+
C          # Remainder is amount of damage

# Roll 2D6, sum, and reroll if the sum is less than 8. Do this 1000 times and graph the result.
10000{
{2D6S}
[7-]{C{2D6S}}
} G

