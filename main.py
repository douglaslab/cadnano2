#!/usr/bin/env python

"""
main.py

Created by Shawn Douglas on 2010-09-26.
"""

import sys
import os
sys.path.insert(0, '.')
import cadnano

if "-t" in sys.argv:
    os.environ['CADNANO_IGNORE_ENV_VARS_EXCEPT_FOR_ME'] = 'YES'

cadnano.initAppWithGui()

if __name__ == '__main__':
    app = cadnano.app()
    if "-p" in sys.argv:
        print("Collecting profile data into cadnano.profile")
        import cProfile
        cProfile.run('app.exec_()', 'cadnano.profile')
        print("Done collecting profile data. Use -P to print it out.")
        exit()
    elif "-P" in sys.argv:
        from pstats import Stats
        s = Stats('cadnano.profile')
        print("Internal Time Top 10:")
        s.sort_stats('cumulative').print_stats(10)
        print("")
        print("Total Time Top 10:")
        s.sort_stats('time').print_stats(10)
        exit()
    elif "-t" in sys.argv:
        print("running tests")
        from tests.runall import main as runTests
        runTests(useXMLRunner=False)
        exit()
    app.exec_()
