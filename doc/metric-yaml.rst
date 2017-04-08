.. currentmodule:: lsst.verify

.. _verify-metric-yaml:

###########################################
Defining metrics and specifications in YAML
###########################################

*Metrics* are scalar quantities that can be measured and monitored.
For example, ``validate_drp`` is designed to measure photometric and astrometric accuracy metrics defined in :lpm:`17`, the LSST Science Requirements document.

Each metric can be accompanied by several *specification* levels.
Specifications are thresholds of a metric that define success or give some indication of algorithm development progress.
:lpm:`17`, for example, defines 'minimum,' 'design,' and 'stretch' specifications for each metric.

Defining metrics and specifications in a YAML_ file allows you to separate science configuration from code, while still keeping metrics accessible from the code and versioned in Git.

This page describes the schema describing for metrics and specifications in YAML_.

.. seealso::

   :ref:`verify-using-metrics`.

.. _verify-metric-objects-yaml:

Metric objects in YAML
======================

Each metric is a separate key-value object in a YAML file.
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
     parameters:
       D: {value: 5.0, unit: arcmin}
     specs:
       - level: design
         value: 10.0
         unit: mmag
         filter_names: [r, i]
       - level: minimum
         value: 20.0
         unit: mmag
         filter_names: [r, i]
       - level: stretch
         value: 5.0
         unit: mmag
         filter_names: [r, i]

Note that the key for this object is the name of the metric itself, 'AM1.'

.. note::

   The ``description``\ ’s field begins with a ``>`` character.
   This is a way of including a multi-line paragraph in YAML.
   See the `YAML documentation <http://www.yaml.org/spec/1.2/spec.html>`__ for more information.

The following sections describe fields in a metric object.

description field
-----------------

The ``description`` field is intended to provide a short summary that defines the metric.
Details can be left to the referenced document.

operator field
--------------

The ``operator`` field specifies what binary comparison operator should be used to check that a measurement of a metric fulfills a specification level.
Comparisons are always done such that the measurement appears on the **left hand side** of the operator, while the specification level appears on the **right hand side**.
If the comparison evaluates as true, the measurement *passes* the specification.
The following operators are allowed:

- ``>=``
- ``>``
- ``<``
- ``<=``
- ``==``
- ``!=``

reference field (optional)
--------------------------

The ``reference`` field contains a dictionary of key-value pairs that document where this metric is formally defined.

Allowed fields are:

- ``doc``: Handle of the document that formally defines the metric. For example, ``doc: LPM-17``.
- ``page``: Page number in ``doc`` where the metric is defined. For example, ``page: 23``. This should be specified if ``doc`` is not an HTML document and ``url`` does not deeply link to the metric's definition.
- ``url``: Web URL to the documentation where the metric is defined. If possible, this should be a deep link directly to the metric's definition.

parameters field (optional)
---------------------------

Some metrics have specific quantities that measurement code must use.
*Parameters* are a way of specifying these quantities in a way that measurement classes can easily use.
Declaring these *parameters* with the metric in YAML helps to centralize a metric's definition.

The ``parameters`` field contains key-value pairs.
The **keys** are names of the parameters.
These **keys** are the same as in the `Metric.parameters` attribute, and are also attribute names of the `Metric` object itself.
**Values** are also key-value pairs with the following fields:.

- ``value``: the scalar value of the dependency (typically a float, int or list/array).
- ``unit``: an `astropy.units-compatible string <http://docs.astropy.org/en/stable/units/format.html>`_ describing the units of ``value``.
- ``label``: the short label for this parameter (optional).
- ``description``: a sentence or two describing this parameter (optional).

Example:

.. code-block:: yaml

   parameters:
     D: {value: 5.0, unit: arcmin}
     mag_max: {value: 22.0, unit: mag}

specs field
-----------

This field contains a list of *specification* objects, keyed by the name of the specification.
In the ``AM1`` example above, specifications are defined for 'design,' 'minimum' and 'stretch' specification levels.
The next section describes the schema for these specification YAML objects.

.. _verify-specifications-yaml:

Defining specifications in YAML
===============================

This section describes the schema for specification objects, which are embedded in the ``specs`` field of metric objects, described above.
Required fields are described first, followed by optional fields to deal with special circumstances.

level field
-----------

The ``level`` field provides the name of the specification.
In the :lpm:`17` Science Requirements Document, levels are one of ``design``, ``minimum`` and ``stretch``.
You can define a different system of levels, or even add a new set of specifications to existing metrics.

value field
-----------

The ``value`` field is the scalar value (float or int) that defines the metric's threshold level.
The specification's value placed on the *right hand side* of the metric's comparison operator when being compared to a measurement.

unit field
-----------

The ``unit`` field annotates the level with physical units, such as ``'mag'`` or ``'arcsec'``.
Units are described by `astropy.units.Unit`-compatible strings.
See the `astropy.units` documentation for what units are available.

If a value is *unitless*, such as a fraction or percent, the unit should be an empty string, ``''``.

.. _verify-filter-specific-specs:

filter\_names field (optional)
------------------------------

In some cases, a specification might be different depending on the optical filter used.
For example, in :lpm:`17`, the PA1 metric has different specification levels for *g*, *r* and *i* filters than *u*, *z* and *y* filters.
This situation is accommodated by creating two separate specification objects for each set of filters.
Then each specification object defines what filters it applies to through a ``filter_names`` field.
``filter_names`` should be an array (list) type, where each value is a string with the filter's name.

.. _verify-metric-spec-dependencies:

dependencies field (optional)
-----------------------------

In :lpm:`17`, some specification levels are dependent on the specification levels of other metrics.
For example, PF1 is defined as:

   The maximum fraction of magnitudes deviating by more than PA2 from the mean.

To measure PF1, the measurement code must use the specification levels of PA2 as a parameter.
In YAML, we can describe this relationship by including the name of the other metric as a list item in the specification's ``dependencies`` field.

For example, the PF1 metric is written as:

.. code-block:: yaml

    PF1:
      # ...
      specs:
        - level: design
          value: 10.0
          unit: ''
          dependencies:
            - PA2

This dependency means that a measurement being compared against the 'design' specification of PF1 must use the PA2 'design' specification level as a parameter.

Note that we only need to name the metric itself, the measurement framework will automatically find the equivalent specification in the dependent metric based on matching the level and filter.

.. _YAML: http://yaml.org
