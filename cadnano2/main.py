#!/usr/bin/env python

"""
main.py

Created by Shawn Douglas on 2010-09-26.
"""

import sys
import os
import pkg_resources  # part of setuptools
sys.path.insert(0, '.')
from . import cadnano

if "-t" in sys.argv:
    os.environ['CADNANO_IGNORE_ENV_VARS_EXCEPT_FOR_ME'] = 'YES'

cadnano.initAppWithGui()

welcome_message = """
Thank you for using Cadnano2 ({})!

We invite you to support the project by citing this reference:

Rapid prototyping of 3D DNA-origami shapes with caDNAno
Douglas et al. Nucleic Acids Res: 37(15):5001–6 (2009)
https://doi.org/10.1093/nar/gkp436

Report bugs at https://github.com/douglaslab/cadnano2 (include terminal output)
Contact: shawn.douglas [at] ucsf.edu
"""

version = pkg_resources.require("cadnano2")[0].version

def main(args=None):
    print(welcome_message.format(version))
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


if __name__ == '__main__':
    sys.exit(main() or 0)