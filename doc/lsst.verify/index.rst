.. currentmodule:: lsst.verify

.. _lsst.verify:

###########
lsst.verify
###########

`lsst.verify` is a framework for packages that measure software and data quality metrics.
A metric can be any measurable scalar quantity; some examples are in the  LSST Science Requirements Document (:lpm:`17`), though packages can also define ad hoc metrics.
Measurements made through `lsst.verify` can be uploaded to LSST's SQUASH_ monitoring dashboard to help you see how code development affects performance.

Python API reference
====================

.. automodapi:: lsst.verify

.. automodapi:: lsst.verify.bin.dispatchverify

.. automodapi:: lsst.verify.jsonmixin
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.metadata.eupsmanifest
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.metadata.jenkinsci
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.metadata.lsstsw
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.squash
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.report
   :no-inheritance-diagram:

.. _SQUASH: https://squash.lsst.codes
