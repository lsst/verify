# This file is part of verify.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import unittest

import astropy.units as u

import lsst.daf.butler as dafButler
import lsst.daf.butler.tests as butlerTests
import lsst.daf.butler.tests.utils as testUtils

from lsst.verify import Measurement
from lsst.verify.bin.jobReporter import JobReporter


class JobReporterTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = testUtils.makeTestTempDir(
            os.path.abspath(os.path.dirname(__file__)))
        cls.addClassCleanup(testUtils.removeTestTempDir, cls.root)

        # Can't use in-memory datastore because JobReporter creates a
        # new Butler from scratch.
        cls.repo = dafButler.Butler(dafButler.Butler.makeRepo(cls.root),
                                    writeable=True)

        # White-box testing: must use real metrics, and provide datasets of
        # type metricvalue_*_*.
        butlerTests.addDataIdValue(cls.repo, "instrument", "NotACam")
        butlerTests.addDataIdValue(cls.repo, "detector", 101)
        # physical_filter needed for well-behaved visits
        butlerTests.addDataIdValue(cls.repo, "physical_filter",
                                   "k2021", band="k")
        butlerTests.addDataIdValue(cls.repo, "visit", 42)

        # Dependency on verify_metrics, but not on the code for computing
        # these metrics.
        butlerTests.addDatasetType(
            cls.repo,
            "metricvalue_pipe_tasks_CharacterizeImageTime",
            {"instrument", "visit", "detector"},
            "MetricValue")

    # No shared setUp(); each test case is responsible for its own collections

    def test_chain(self):
        """Test that running JobReporter on a chained collection retrieves the
        metric value closest to the head of the chain.
        """
        metricName = "pipe_tasks.CharacterizeImageTime"
        id = {"instrument": "NotACam", "visit": 42, "detector": 101}
        chainName = "test_chain"
        # Note: relies on dict being ordered
        chain = {"test_chain_run2": Measurement(metricName, 13.5 * u.s),
                 "test_chain_run1": Measurement(metricName, 5.0 * u.s),
                 }

        for collection, result in chain.items():
            self.repo.registry.registerCollection(
                collection, dafButler.CollectionType.RUN)
            self.repo.put(result,
                          "metricvalue_pipe_tasks_CharacterizeImageTime",
                          id,
                          run=collection)
        self.repo.registry.registerCollection(
            chainName, dafButler.CollectionType.CHAINED)
        self.repo.registry.setCollectionChain(chainName, chain.keys())

        reporter = JobReporter(repository=self.root,
                               collection=chainName,
                               metrics_package="pipe_tasks",
                               spec=None,
                               dataset_name="_tests")
        jobs = reporter.run()
        self.assertEqual(len(jobs), 1)  # Only one data ID
        values = list(jobs.values())[0].measurements
        self.assertEqual(len(values), 1)  # Only one metric
        self.assertEqual(values[metricName], chain["test_chain_run2"])


if __name__ == "__main__":
    unittest.main()
