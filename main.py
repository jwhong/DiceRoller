import sys
from Compiler import Compiler

#import cProfile
#import pstats

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Please provide the name of the script you want to run on the command line")
        exit(0)
    cmp = Compiler(open(sys.argv[1]).read())
    e = cmp.compile()
    e.run()
    #cProfile.run('e.run()', 'out.dat')
    #p = pstats.Stats('out.dat')
    #p.sort_stats('cumulative')
    #p.print_stats()