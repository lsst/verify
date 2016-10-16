.. currentmodule:: lsst.validate.base

.. _validate_base:

#################################################
lsst.validate.base — Metric Measurement Framework
#################################################

`lsst.validate.base` is a framework for building packages that make measurements of software and data quality metrics.
Though `lsst.validate.base`, developers can build validation pipelines that upload semantically-rich measurements to LSST's SQUASH_ monitoring dashboard.

In this framework, metrics can be any measurable scalar quantity.
For example, the LSST Science Requirements Document (:lpm:`17`) lists metrics related to astrometric and photometric performance.
The ``validate_drp`` package, in fact, uses the `lsst.validate.base` framework to measure :lpm:`17` metrics.

Metrics typically have *specification levels*, which act as development milestones or success criteria.
Using `lsst.validate.base` with the SQUASH_ dashboard lets you see at a glance how your code is performing relative to metric specifications from one commit to another.

Features
========

`lsst.validate.base` gives developers all the tools needed to make and report measurements to SQUASH_:

- Define metrics and their specifications :ref:`in YAML <validate-base-metric-yaml>`.
- Work with metrics and specifications :ref:`in Python <validate-base-using-metrics>` with `Metric` and `Specification` classes.
- Have different specifications apply to data from :ref:`different optical filters <validate-base-filter-specific-specs>`.
- :ref:`Annotate metrics <validate-base-metric-yaml>` with configuration parameters needed by measurement code---even :ref:`specification levels of other metrics <validate-base-metric-spec-dependencies>`.
- Create semantically-rich :ref:`measurement classes <validate-base-measurement-class>` that record not only a value but also metadata like input parameters and measurement by-products using the `MeasurementBase` base class.
- :ref:`Package input datasets as blobs <validate-base-creating-blobs>` that can power drill-down visualizations of measurements on the SQUASH_ dashboard.
- Give numbers meaning with with Astropy :py:obj:`~astropy.units.Quantity`, plot labels, and descriptions using the `Datum` class.
- Build a self-describing JSON document of measurements and blobs that's ready to submit to the SQUASH_ web API using the `Job` class.

Using lsst.validate.base
========================

.. toctree::
   :maxdepth: 2

   metric-yaml
   metric-dev
   measurement-dev
   blob-dev

Python API Reference
====================

.. automodapi:: lsst.validate.base

.. automodapi:: lsst.validate.base.jsonmixin
   :no-inheritance-diagram:

.. automodapi:: lsst.validate.base.datummixin
   :no-inheritance-diagram:

.. _SQUASH: https://squash.lsst.codes
