.. currentmodule:: lsst.validate.base

.. _validate-base-using-metrics:

##########################################
Using metrics and specifications in Python
##########################################

Metrics and their specifications are typically :ref:`defined in YAML files <validate-base-metric-yaml>`.
This page describes how to work with those metrics and specifications within Python using the `lsst.validate.base.Metric` and `lsst.validate.base.Specification` classes.

.. seealso::

   :ref:`validate-base-metric-yaml`.

Creating Metric objects in Python
=================================

A `Metric` object is typically built from a YAML definition with the `Metric.from_yaml` class method.
`Metric.from_yaml` takes the metric name and either the path of a metric YAML file (``yaml_path`` keyword argument) or a pre-parsed YAML object (``yaml_doc`` keyword argument).

For example:

.. code-block:: python

   import os
   import astropy.units as u
   from lsst.utils import getPackageDir
   from lsst.validate.base import Metric
   yaml_path = os.path.join(getPackageDir('validate_drp'),
                            'metrics.yaml')
   am1 = Metric.from_yaml('AM1', yaml_path=yaml_path)

.. seealso::

   To create `Metric` instances from all metrics in a YAML file, use the `~load_metrics` function.

Checking a measurement against a Specification
==============================================

A `Metric` object is useful for validating a measurement against a specification.
For this, use the `Metric.check_spec` method:

.. code-block:: python

   measured_value = 2. * u.arcmin  # hypothetical measured value
   am1.check_spec(measured_value, 'design')

The last statement returns `True` if the measured value fulfills the 'design' specification.
If a specification is filter-dependent, the filter's name needs to be passed to the ``filter_name`` keyword argument of `Metric.check_spec`.

See :doc:`measurement-dev` for details on how to make measurements with the ``lsst.validate.base`` API.

Accessing Specification objects of a Metric
===========================================

Since some measurements need to know about the specification levels of a `Metric`, `Metric`\ s provide a `Metric.get_spec` method to resolve and retrieve a `Specification`.
For example:

.. code-block:: python

   design_spec = pf1.get_spec('design')

If specification levels are filter-dependent, the filter's name can be provided with the ``filter_name`` keyword argument.

The properties of a specification are retrieved through attributes:

.. code-block:: python

   design_spec.quantity  # an astropy.units.Quantity
   design_spec.unit  # an astropy.units.Unit
   design_spec.label
   design_spec.filter_names
   design_spec.latex_unit  # units marked up as LaTeX math

:ref:`Dependencies of specification levels <validate-base-metric-spec-dependencies>` can be obtained as attributes corresponding to their labels.
Dependencies themselves are `Datum` objects, with a value and units.
For example,

.. code-block:: python

   design_spec.PA2  # the PA2 dependency as a Datum
   design_spec.PA2.quantity  # value of distance parameter
   design_spec.PA2.unit  # units of the distance parameter

See :doc:`measurement-dev` for examples of measurements that retrieve dependencies of metrics and their specification levels.
