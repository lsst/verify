#!/usr/bin/env python
"""Create two butler repos for tests of the metricvalue extract/print code.
"""

import astropy.units as u

import lsst.daf.butler
from lsst.daf.butler.tests import addDatasetType, addDataIdValue
from lsst.verify import Measurement

collection = "testrun"


def setup_butler(repo):
    """Create a butler at the given location, and register appropriate things
    in it to allow adding metricvalues.
    """
    lsst.daf.butler.Butler.makeRepo(repo)
    butler = lsst.daf.butler.Butler(repo, writeable=True)

    addDataIdValue(butler, "instrument", "TestCam")
    for x in range(189):
        addDataIdValue(butler, "detector", x)
    addDataIdValue(butler, "visit", 12345)
    addDataIdValue(butler, "visit", 54321)
    butler.registry.registerCollection(collection, lsst.daf.butler.CollectionType.RUN)

    return butler


def add_metricvalues(butler, plus):
    """Add Measurements as MetricValue datasets to a pre-configured butler,
    adding ``plus`` to the values that are stored (to allow different repos to
    have different Measurement values).
    """
    dimensions = {"instrument", "visit", "detector"}
    storageClass = "MetricValue"
    dataIds = [{"instrument": "TestCam", "visit": 12345, "detector": 12},
               {"instrument": "TestCam", "visit": 54321, "detector": 25},
               {"instrument": "TestCam", "visit": 54321, "detector": 12}]
    addDatasetType(butler, "metricvalue_verify_testing", dimensions, storageClass)
    value = Measurement("verify.testing", (12 + plus)*u.dimensionless_unscaled)
    butler.put(value, "metricvalue_verify_testing", dataIds[0], run=collection)
    value = Measurement("verify.testing", (42 + plus)*u.dimensionless_unscaled)
    butler.put(value, "metricvalue_verify_testing", dataIds[1], run=collection)
    value = Measurement("verify.testing", (5 + plus)*u.dimensionless_unscaled)
    butler.put(value, "metricvalue_verify_testing", dataIds[2], run=collection)

    addDatasetType(butler, "metricvalue_verify_other", dimensions, storageClass)
    value = Measurement("verify.other", (7 + plus)*u.ct)
    butler.put(value, "metricvalue_verify_other", dataIds[0], run=collection)
    value = Measurement("verify.other", (8 + plus)*u.ct)
    butler.put(value, "metricvalue_verify_other", dataIds[1], run=collection)

    addDatasetType(butler, "metricvalue_verify_another", dimensions, storageClass)
    value = Measurement("verify.another", (3 + plus)*u.mas)
    butler.put(value, "metricvalue_verify_another", dataIds[0], run=collection)

    addDatasetType(butler, "metricvalue_verify_testingTime", dimensions, storageClass)
    value = Measurement("verify.testingTime", (18 + plus)*u.second)
    butler.put(value, "metricvalue_verify_testingTime", dataIds[0], run=collection)
    value = Measurement("verify.testingTime", (19 + plus)*u.second)
    butler.put(value, "metricvalue_verify_testingTime", dataIds[1], run=collection)

    addDatasetType(butler, "metricvalue_verify_anotherTime", dimensions, storageClass)
    value = Measurement("verify.anotherTime", (100 + plus)*u.ms)
    butler.put(value, "metricvalue_verify_anotherTime", dataIds[0], run=collection)
    value = Measurement("verify.anotherTime", (200 + plus)*u.ms)
    butler.put(value, "metricvalue_verify_anotherTime", dataIds[1], run=collection)

    addDatasetType(butler, "metricvalue_verify_testingMemory", dimensions, storageClass)
    value = Measurement("verify.testingMemory", (100 + plus)*u.Mbyte)
    butler.put(value, "metricvalue_verify_testingMemory", dataIds[0], run=collection)
    value = Measurement("verify.testingMemory", (200 + plus)*u.Mbyte)
    butler.put(value, "metricvalue_verify_testingMemory", dataIds[1], run=collection)

    addDatasetType(butler, "metricvalue_verify_anotherTaskMemory", dimensions, storageClass)
    value = Measurement("verify.anotherTaskMemory", (5 + plus)*u.Gbyte)
    butler.put(value, "metricvalue_verify_anotherTaskMemory", dataIds[0], run=collection)
    value = Measurement("verify.anotherTaskMemory", (6 + plus)*u.Gbyte)
    butler.put(value, "metricvalue_verify_anotherTaskMemory", dataIds[1], run=collection)


if __name__ == "__main__":
    repo = "metricvalue_repo1"
    butler = setup_butler(repo)
    add_metricvalues(butler, 0)

    repo = "metricvalue_repo2"
    butler = setup_butler(repo)
    add_metricvalues(butler, 1)
