.. currentmodule:: lsst.validate.base

.. _validate-base-jobs:

################################################
Using Jobs to collect and serialize measurements
################################################

The `lsst.validate.base` framework works in tandem with the SQUASH_ metric monitoring service.
This page describes how to use the `lsst.validate.base.Job` class to collect :doc:`measurements <measurements>` and :doc:`blobs <blobs>`, and build a JSON document that is accepted by SQUASH's RESTful API.

Collecting measurements in a Job
================================

A `Job` is a container for measurements and their referenced data, including blobs.

You can add multiple measurements to a `Job` when you create it:

.. code-block:: python

   from lsst.validate.base import Job

   # ...create measurements meas1, meas2, ...

   job = Job(measurements=[meas1, meas2])

Alternatively, you can add measurements one at a time with the `Job.register_measurement` method:

.. code-block:: python

   from lsst.validate.base import Job

   # ...create measurements meas1, meas2, ...

   job = Job()
   job.register_measurement(meas1)
   job.register_measurement(meas2)

A convenient way of adding measurements to a `Job` is in a measurement's ``__init__`` method, like this:

.. code-block:: python

   import os
   import astropy.units as u
   from lsst.utils import getPackageDir
   from lsst.validate.base import MeasurementBase, Job


   class PA1Measurement(MeasurementBase):
       
       def __init__(self, yaml_path, job=None):
           MeasurementBase.__init__(self)
           
           self.metric = Metric.from_yaml('PA1', yaml_path=yaml_path)
           
           # measurement code
           # ...
           
           # This is the scalar measurement value; always as an astropy.unit.Quantity
           self.quantity = 2. * u.mmag

           if job is not None:
               job.register_measurement(self)

   job = Job()
   yaml_path = os.path.join(getPackageDir('validate_drp'),
                            'metrics.yaml')
   PA1Measurement(yaml_path, job=job)

Getting measurements from a Job
===============================

Not only can you put measurements *into* a `Job`, you can also get measurements *out of* a `Job`.
Your application might use this functionality to get measurements to pass as parameters of other measurements, or to provide a pass/fail printout of all measured metrics.

If a job contains a measurement of the ``'PA1'`` metric, you can get that measurement using the `~Job.get_measurement` method:

.. code-block:: python

   job.get_measurement('PA1')

Some measurements correspond to a particular specification level or filter.
You can pass this information to `~Job.get_measurement` to disambiguate several measurements of a given metric:

.. code-block:: python

   pa2_design = job.get_measurement('PA2', spec_name='design')
   pa2_min = job.get_measurement('PA2', spec_name='minimum')

A :py:obj:`RuntimeError` is raised if `Job.get_measurement` does not have sufficient information (like ``spec_name`` or ``filter_name``) to retrieve a single measurement.

Serializing to JSON
===================

JSON objects
------------

Once all :doc:`measurements <measurements>` and :doc:`blobs <blobs>` are registered in a `Job`, you can generate a JSON serialization of that dataset:

.. code-block:: python

   from lsst.validate.base import Job

   job = Job()
   # .. register measurements and blobs
   json_doc = job.json

``json_doc`` is a `dict` wrapping :py:mod:`json`-serializable objects.

.. note::

   All `lsst.validate.base` classes (`Datum`, `MeasurementBase`, `BlobBase`, `Metric`, `Specification` and `Job`) have a ``json`` property.
   That property lets you get a :py:mod:`json`-serializable object for a specific object.
   `Job.json` simply calls the ``json`` properties of every object it contains.

Writing a JSON file
-------------------

`Job` also provides a convenience method, `~Job.write_json`, for writing the JSON document directly to the filesystem:

.. code-block:: python

   from lsst.validate.base import Job

   job = Job()
   # .. register measurements and blobs
   job.write_json('measurements.json')


Uploading lsst.validate.base's JSON to SQUASH
=============================================

At the moment the SQUASH_ API does not directly accept the JSON produced `Job.json`.
Instead, it's shimmed with a package called `post-qa`_.
We expect to standardize the process for uploading measurements to SQUASH_ in the near future.
In the meantime, please contact the DM SQuaRE team on community.lsst.org_ or the `#dm-square`_ Slack channel and we'll help integrate your package with SQUASH_.

.. _SQUASH: https://squash.lsst.codes
.. _post-qa: https://github.com/lsst-sqre/post-qa
.. _`#dm-square`: https://lsstc.slack.com/messages/dm-square/
.. _`community.lsst.org`: https://community.lsst.org/c/dm
