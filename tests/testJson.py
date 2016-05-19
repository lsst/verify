#!/usr/bin/env python

#
# LSST Data Management System
# Copyright 2012-2016 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#

from __future__ import print_function

import json
import os
import tempfile
import unittest

import numpy as np

import lsst.utils.tests as utilsTests

import lsst.pipe.base as pipeBase
from lsst.validate.drp.io import (saveKpmToJson, loadKpmFromJson,
                                  DatumSerializer)


class JsonTestCase(unittest.TestCase):
    """Testing basic coordinate calculations."""

    def testSaveJson(self):
        ps = pipeBase.Struct(foo=2, bar=[10, 20], hard=np.array([5, 10]))
        _, tmpFilepath = tempfile.mkstemp(suffix='.json')
        saveKpmToJson(ps, tmpFilepath)
        self.assertTrue(os.path.exists(tmpFilepath))

        # Here we get a dict back.
        readBackData = json.load(open(tmpFilepath))
        self.assertEqual(readBackData['foo'], 2)

        os.unlink(tmpFilepath)

    def testLoadJson(self):
        ps = pipeBase.Struct(foo=2, bar=[10, 20], hard=np.array([5, 10]))
        _, tmpFilepath = tempfile.mkstemp(suffix='.json')
        saveKpmToJson(ps, tmpFilepath)

        # Here we get a pipeBase.Struct back.
        readBackData = loadKpmFromJson(tmpFilepath)
        self.assertEqual(readBackData.foo, 2)
        self.assertEqual(readBackData.bar, [10, 20])
        np.testing.assert_array_equal(readBackData.hard, np.array([5, 10]))

        os.unlink(tmpFilepath)


class DatumTestCase(unittest.TestCase):
    """Test DatumSerializer."""

    def testDatumSerialization(self):
        datum = DatumSerializer(1., 'arcsec', 'RMS',
                                'Star-to-star distance repeatability')
        d = datum.json
        self.assertEqual(d['value'], 1.)
        self.assertEqual(d['units'], 'arcsec')
        self.assertEqual(d['label'], 'RMS')
        self.assertEqual(d['description'],
                         'Star-to-star distance repeatability')


def suite():
    """Returns a suite containing all the test cases in this module."""

    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(JsonTestCase)
    suites += unittest.makeSuite(DatumTestCase)
    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)


if __name__ == "__main__":
    run(True)
