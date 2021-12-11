"""
unittests.py

Created by Shawn Douglas on 2011-06-28.
"""

import sys, os
sys.path.insert(0, '.')

import time, code
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import tests.cadnanoguitestcase
from tests.cadnanoguitestcase import CadnanoGuiTestCase
from cadnano2.model.enum import StrandType
from cadnano2.model.virtualhelix import VirtualHelix
import unittest
from rangeset import RangeSet, rangeIntersection
import random
seed = random.Random().randint(0,1<<32)
enviroseed = os.environ.get('UNITTESTS_PRNG_SEED', False)
if enviroseed != False:
    seed = int(enviroseed)
del enviroseed
print("Seeding tests.unittests; use setenv UNITTESTS_PRNG_SEED=%i to replay."%seed)


class UnitTests(CadnanoGuiTestCase):
    """
    Unit tests should test individual modules, and do not necessarily need
    to simulate user interaction.

    Create new tests by adding methods to this class that begin with "test".
    See for more detail: http://docs.python.org/library/unittest.html

    Run unit tests by calling "python -m test.unittests" from cadnano2 root
    directory.
    """
    def setUp(self):
        """
        The setUp method is called before running any test. It is used
        to set the general conditions for the tests to run correctly.
        """
        CadnanoGuiTestCase.setUp(self)
        self.prng = random.Random(seed)
        # Add extra unit-test-specific initialization here

    def tearDown(self):
        """
        The tearDown method is called at the end of running each test,
        generally used to clean up any objects created in setUp
        """
        CadnanoGuiTestCase.tearDown(self)
        # Add unit-test-specific cleanup here

    def testUnit1(self):
        """docstring for testUnit1"""
        pass

if __name__ == '__main__':
    tc = UnitTests()
    tc.setUp()
    # tc.testRangeSet_addRange_removeRange()
    tests.cadnanoguitestcase.main()
