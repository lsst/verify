.. currentmodule:: lsst.validate.base

.. _validate_base:

#################################################
lsst.validate.base — Metric measurement framework
#################################################

`lsst.validate.base` is a framework for packages that measure software and data quality metrics.
A metric can be any measurable scalar quantity; some examples are in the  LSST Science Requirements Document (:lpm:`17`), though packages can also define ad hoc metrics.
Measurements made through `lsst.validate.base` can be uploaded to LSST's SQUASH_ monitoring dashboard to help you see how code development affects performance.

Features
========

`lsst.validate.base` helps you build packages that make and report measurements to SQUASH_:

- Define metrics and specifications (milestones) using a :ref:`YAML schema <validate-base-metric-yaml>`, and access those definitions through `Metric` and `Specification` classes.
- Create semantically-rich :ref:`measurement classes <validate-base-measurement-class>` that record not only a value but also metadata like input parameters and measurement by-products using the `MeasurementBase` base class.
- :ref:`Package input datasets as blobs <validate-base-creating-blobs>` that can power drill-down visualizations of measurements on the SQUASH_ dashboard.
- Record self-documenting datasets: values have units (though Astropy :py:obj:`~astropy.units.Quantity`) as well as plot labels and descriptions (see the `Datum` class).
- Build a :ref:`JSON document of measurements and blobs <validate-base-jobs>` that's ready to submit to the SQUASH_ web API using the `Job` class.

Using lsst.validate.base
========================

.. toctree::
   :maxdepth: 2

   metric-yaml
   metrics
   measurements
   blobs
   jobs

Python API reference
====================

.. automodapi:: lsst.validate.base

.. automodapi:: lsst.validate.base.jsonmixin
   :no-inheritance-diagram:

.. automodapi:: lsst.validate.base.datummixin
   :no-inheritance-diagram:

.. _SQUASH: https://squash.lsst.codes
