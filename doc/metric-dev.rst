##########################
Creating and Using Metrics
##########################

*Metrics* are scalar quantities that can be measured and monitored.
``validate_drp`` is designed to measure metrics from :lpm:`17`, the LSST Science Requirements document.
:lpm:`17`, for example, defines metrics that quantify photometric and astrometric measurement accuracy in the LSST Science Pipelines.

Each metric can be accompanied by several *specification* levels.
Specifications are thresholds of a metric that define success or give some indication of algorithm development progress.
:lpm:`17`, for example, defines 'minimum,' 'design,' and 'stretch' specifications for each metric.

This page describes the schema and API for defining and using both metrics and specifications in ``validate_drp``.
This API can also be adopted by other validation and integration test packages.
A key feature of this API is that metrics and measurements can be submitted directly to the LSST DM quality assurance database and dashboard: SQUASH.

Defining Metrics and Specifications in YAML
===========================================

The best way to define new metrics and specifications is in a :file:`metrics.yaml` file embedded in an EUPS package (Git repository).
:file:`metrics.yaml` in ``validate_drp`` is a useful example for such a YAML file.

Metric objects in YAML
----------------------

In :file:`metrics.yaml`, each metric is a separate key-value object.
For example, here's the AM1 metric's definition:

.. code-block:: yaml

   AM1:
     reference:
       doc: LPM-17
       url: http://ls.st/lpm-17
       page: 23
     description: >
       The maximum rms of the astrometric distance distribution for stellar pairs
       with separations of D=5 arcmin (repeatability) (milliarcsec).
     operator: "<="
     dependencies:
       - D: {value: 5.0, units: arcmin}
     specs:
       - level: design
         value: 10.0
         units: mmag
         filters: [r, i]
       - level: minimum
         value: 20.0
         units: mmag
         filters: [r, i]
       - level: stretch
         value: 5.0
         units: mmag
         filters: [r, i]

Note that the key for this object is the name of the metric itself, 'AM1.`
Within the object are the following fields:

``reference``
   This field contains a dictionary of key-value pairs that document where this metric is formally defined.
   In the AM1 example, the metric is defined in the ``doc`` 'LPM-17' on ``page`` 23.
   The URL of that document is also provided.
   This metadata is optional, and subsets of the ``doc``, ``page`` and ``url`` fields are allowed.

``description``
   The description field is intended to provide a short summary that defines the metric.
   Details can be left for the referenced document.

``operator``
   The operator field specifies what binary comparison operator should be used to check that a measurement of a metric fulfills a specification level.
   Comparisons are always done such that the measurement appears on the **left hand side** of the operator, while the specification level appears on the **right hand side**.
   If the comparison evaluates as true, the measurement *passes* the specification.
   The following operators are allowed:
   
   - ``>=``
   - ``>``
   - ``<``
   - ``<=``
   - ``==``
   - ``!=``

``dependencies``
   Some metrics have specific quantities that measurement code must use.
   *Dependencies* are a way of specifying these quantities in a way that measurement classes can easily use.
   The ``dependencies`` field is a list of items.
   Each list item should be a one-item ``dict``.
   The key specifies the name of the dependency (made available as an attribute of the :class:`~lsst.validate.drp.base.Metric`), while the value is a :class:`~lsst.validate.drp.base.Datum` with the following possible fields:
   
   - ``value``: the scalar value of the dependency (typically a `float`, `int` or list/array).
   - ``units``: an ``astropy.units``-compatible string describing the units of ``value``.
   - ``label``: the short label for this parameter (optional).
   - ``description``: a sentence or two describing this parameter (optional).

``specs``
   This field contains a list of *specification* objects, keyed by the name of the specification.
   In the ``AM1`` example above, specifications are defined for 'design,' 'minimum' and 'stretch' specification levels.
   The next section describes the schema for these specification YAML objects.

Defining specifications in YAML
-------------------------------

This section describes the schema for specification objects, which are embedded in the ``specs`` field of metric objects, described above.
First we describe required fields, followed by optional fields to deal with special circumstances.

``level``
   This field provides the name of the specification.
   In the :lpm:`17` Science Requirements Document, levels are one of `design`, `minimum` and `stretch`, which describe a set of algorithmic performance goals.
   One can define different a different system of levels, or even add a new set of specifications to existing metrics.

``value``
   This field is the scalar value (`float` or `int`) that defines the metric's threshold level.
   The specification's value placed on the *right hand side* of the metric's comparison operator when being compared to a measurement.

``units``
   This field annotates the level with units, such as ``'mag'`` or ``'arcsec'``.
   Units are described by astropy.units-compatible strings.
   See the astropy.units documentation for what units are available.
   
   If a value is *unitless*, such as a fraction or percent, the unit should be an empty string, ``''``.

Defining filter-specific specifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In some cases, a specification might be different depending on the optical filter used.
For example, in :lpm:`17`, the PA1 metric has different specification levels for g, r and i filters than u, z and y filters.
This situation is accommodated by creating two separate specification objects for each set of filters.
Then each specification object defines what filters it applies to through a ``filters`` field.
``filters`` should be an array (list) type, where each value is a string with the filter's name.

Defining metrics that are dependent on the specification levels of other metrics
----------------------------------------------------------------------------------

In :lpm:`17`, some specification levels are dependent on the specification levels of other metrics.
For example, PF1 is defined as:

   The maximum fraction of magnitudes deviating by more than PA2 from the mean.

In order to measure PF1, we must use the specification levels of PA2 as a parameter of the measurement.
In YAML, we can describe this relationship by including the name of the other metric as a list item in the specification's ``dependencies`` field.

For example, the PF1 metric is written as:

.. code-block:: yaml

    PF1:
      # ...
      specs:
        - level: design
          value: 10.0
          units: ''
          dependencies:
            - PA2

This dependency means that a measurement being compared against the 'design' specification of PF1 must use the PA2 'design' specification level as a parameter.

Note that we only need to name the metric itself, the measurement framework will automatically find the equivalent specification in the dependent metric based on matching the level and filter.

Creating Metric Objects in Python
=================================

Within Python, metrics are represented by instances of the :class:`lsst.validate.drp.base.Metric` class.

A metric object is built from a YAML definition with the :meth:`lsst.validate.drp.base.Metric.fromYaml` class method.
:meth:`~lsst.validate.drp.base.Metric.fromYaml` takes the metric name and either the path of a metric YAML file (``yamlPath`` keyword argument) or a pre-parsed YAML object (``yamlDoc`` keyword argument).

For example:

.. code-block:: python

   import os
   from lsst.utils import getPackageDir
   from lsst.validate.drp.base import Metric
   yamlPath = os.path.join(getPackageDir('validate_drp'),
                           'metrics.yaml')
   am1 = Metric.fromYaml('AM1', yamlPath=yamlPath)

Checking a Measurement Against a Specification
==============================================

Ultimately, a metric object is most valuable in validating a measurement against a specification.
For this, use the :meth:`lsst.validate.drp.base.Metric.checkSpec` method:


.. code-block:: python

   measuredValue = 2.  # hypothetical measured value
   am1.checkSpec(measuredValue, 'design')

The last statement will return ``True`` if the measured value fulfills the 'design' specification.
If a specification is bandpass dependent, the bandpass needs to be passed to the ``bandpass`` keyword argument of :meth:`~lsst.validate.drp.base.Metric.checkSpec`.

In :doc:`measurement-dev` we describe how to make measurements with the ``validate_drp`` API.

Accessing Specification Objects of a Metric
===========================================

Since some measurements need to know about the specification levels of a metric, metrics provide a :meth:`~lsst.validate.drp.base.Metric.getSpec` method to resolve and retrieve a specification level.
For example:

.. code-block:: python

   designSpec = am1.getSpec('design')

If specification levels are bandpass-dependent, the bandpass can be provided with the ``bandpass`` keyword argument.

The properties of a specification are retrieved through attributes:

.. code-block:: python

   designSpec.value
   designSpec.units
   designSpec.label
   designSpec.bandpasses
   designSpec.latex_units  # units marked up as LaTeX math
   designSpec.astropy_quanity  # value and unit as an Astropy quantity

Dependencies of specification levels can be obtained as attributes corresponding to their labels.
Dependencies themselves are :class:`~lsst.validate.drp.base.Datum` objects, with a value and units.
For example,

.. code-block:: python

   designSpec.d  # the distance parameter
   designSpec.d.value  # value of distance parameter
   designSpec.d.units  # units of the distance parameter

In :doc:`measurement-dev` we provide examples of measurements that retrieve dependencies of metrics and their specification levels.
