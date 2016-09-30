#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import unittest

from lsst.validate.base import Specification, Datum


class SpecificationTestCase(unittest.TestCase):
    """Test Specification class functionality."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_dependency_access(self):
        deps = {'a': Datum(5, 'mag')}
        s = Specification('design', 0., '', dependencies=deps)
        self.assertEqual(s.a.value, 5)


if __name__ == "__main__":
    unittest.main()
