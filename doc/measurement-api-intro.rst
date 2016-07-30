################################################
Introduction to the validate_drp Measurement API
################################################

``validate_drp`` provides a framework for making and reporting measurements of metrics.
This framework is used internally by ``validate_drp`` and can also be used by other packages that monitor algorithmic performance.

The measurement API is focused on making metric measurements and metadata available to the SQUASH dashboard.
All API objects can serialize themselves into a JSON format that can be submitted to the SQUASH dashboard's web API.
Datasets are also designed to be self-documenting, from both Python and JSON contexts.
Values are annotated with units (``astropy.units``-compatible) and readable descriptions.

The measurement API also features a YAML format for defining metrics and specification levels.
Metric objects are constructed from YAML definitions so that measurements can be validated against specifications (such as :lpm:`17`).

Main Classes in the Measurement API
===================================

The measurement API consists of classes that can be used directly, as well as base classes.
API classes provide a consistent pattern for defining and measuring metrics.
These API classes also provide JSON serialization and methods for validating measurements against specification levels.

These are the key API classes, along with links to further documentation:

- :class:`~lsst.validate.drp.base.Datum` objects wrap numerical data, whether it is a specification level, parameter, measurement value, or member of a 'blob' data object. :class:`~lsst.validate.drp.base.Datum` objects contain the following fields:

  - A :attr:`~lsst.validate.drp.base.Datum.value` field, which can be a scalar (int or float) or a sequence (`list` or ``numpy.ndarray``)
  - A :attr:`~lsst.validate.drp.base.Datum.units` field, that annotates the physical units of the :attr:`~lsst.validate.drp.base.Datum.value`. Units must be ``astropy.units``-compatible strings. For unitless quantities, units should be an empty string.
  - A :attr:`~lsst.validate.drp.base.Datum.label` field, which can be used to decorate a plot axis or legend. The :attr:`~lsst.validate.drp.base.Datum.label` should exclude reference of units. This :attr:`~lsst.validate.drp.base.Datum.label` field is optional.
  - A :attr:`~lsst.validate.drp.base.Datum.description` field that can include free form text that documents the Datum. The :attr:`~lsst.validate.drp.base.Datum.description` field is also optional.
  
- :class:`~lsst.validate.drp.base.Metric` is a class containing metadata about a metric, along with specification levels. Typically, :class:`~lsst.validate.drp.base.Metric` objects are constructed from a YAML definition file, though they can also be arbitrarily constructed in Python. See :doc:`metric-dev` for more information.
- :class:`~lsst.validate.drp.base.Specification` objects are contained inside :class:`~lsst.validate.drp.base.Metric` objects, and define levels of expected measurement performance. Metrics can have multiple specifications indicating different performance goals (e.g., 'minimum', 'design' and 'stretch). Specifications can also be associated with certain observational bandpasses. Typically, :class:`~lsst.validate.drp.base.Specification` objects are built automatically by the :class:`~lsst.validate.drp.base.Metric` class from a YAML definition. Specifications can also be added manually to :class:`~lsst.validate.drp.base.Metric` classes. See :doc:`metric-dev` for more information.
- :class:`~lsst.validate.drp.base.MeasurementBase` is a base class for making measurements of a metric. All code needed for making a measurement can be contained by a subclass of :class:`~lsst.validate.drp.base.MeasurementBase`. At a minimum, :class:`~lsst.validate.drp.base.MeasurementBase` subclasses store a scalar value, but can also register additional :class:`~lsst.validate.drp.base.Datum` objects that can be persisted to JSON. See :doc:`measurement-dev` for more information.
- :class:`~lsst.validate.drp.base.BlobBase` is a base class for making blobs, which are a way of storing datasets in an object that is both convenient for measurement classes and serializable for JSON. Measurement classes can share a common blob without storing duplicate data in the SQUASH database. Blobs are linked to the measurements that use them, allowing blobs to power plots that provide context to measurements. See :doc:`blob-dev` for more information.
- :class:`~lsst.validate.drp.base.Job` is a container for :class:`~lsst.validate.drp.base.Metric`, :class:`~lsst.validate.drp.base.MeasurementBase`-type and :class:`~lsst.validate.drp.base.BlobBase`-type objects. Through a :class:`~lsst.validate.drp.base.Job` instance, users can generate a single JSON object that can be submitted directly to the SQUASH dashboard API.
