.. currentmodule:: lsst.validate.base

.. _validate-base-measurement-class: 

############################
Creating Measurement Classes
############################

The `MeasurementBase` abstract base class defines a standard interface for writing classes that make measurements of :doc:`metrics <metric-dev>`.
`MeasurementBase` ensures that measurements, along with metadata about the measurement, can be serialized and submitted to the SQUASH_ metric monitoring service.

This page covers the usage of `MeasurementBase` for creating measurement classes.

A Minimal Measurement Class
===========================

At a minimum, measurement classes must subclass `MeasurementBase` and provide some metadata as instance attributes, such as the name of metric being measured and units of the measurement.
This is a basic template for a measurement class:

.. code-block:: python

   import os
   from lsst.utils import getPackageDir
   from lsst.validate.base import MeasurementBase


   class PA1Measurement(MeasurementBase):

       label = 'PA1'
       metric = None
       value = None
       units = 'mmag'
       
       def __init__(self, yaml_path):
           MeasurementBase.__init__(self)
           
           self.metric = Metric.from_yaml(self.label, yaml_path=yaml_path)
           
           # measurement code
           # ...
           
           self.value = 0  # Scalar value from measurement code


   yaml_path = os.path.join(getPackageDir('validate_drp'),
                            'metrics.yaml')
   pa1_measurement = PA1Measurement(yaml_path)

In a measurement class, the following metadata attributes must be specified (their presence is required by the :class:`~lsst.validate.base.MeasurementBase` abstract base class):

`MeasurementBase.label`
   The name of the metric.

`MeasurementBase.metric`
   A `Metric` object. In this example, the `Metric.from_yaml` class method constructs a `Metric` instance for PA1 from the :file:`metrics.yaml` file built into ``validate_drp``.

`MeasurementBase.units`
   Units of the measurement value. As in `Datum`\ s, `MeasurementBase.units` should be an `astropy.units.Unit`-compatible string.

Storing a Measurement Value
===========================

The purpose of a measurement class is to make a make a measurement; those calculations should occur in a measurement instance's ``__init__`` method.
Any data required for a measurement should be provided through the measurement class's ``__init__`` method.

The measurement result is stored in a `MeasurementBase.value` attribute.
`MeasurementBase.value` must be a scalar (`float` or `int`), in the same physical units indicated by the ``units`` attribute.
If a measurement class is unable to make a measurement, ``value`` should be ``None``.

Registering Measurement Parameters
==================================

Often a measurement code is customized with parameters.
As a means of lightweight provenance, the measurement API provides a way to declare these parameters so that they're persisted to the database using the `MeasurementBase.register_parameter` method:

.. code-block:: python

   class PA1Measurement(MeasurementBase):

       metric = None
       value = None
       units = 'mmag'
       label = 'PA1'

       def __init__(self, yaml_path, num_random_shuffles=50):
           MeasurementBase.__init__(self)
           
           self.metric = Metric.from_yaml(self.label, yaml_path)

           self.register_parameter('num_random_shuffles',
                                   value=num_random_shuffles,
                                   units='',
                                   description='Number of random shuffles')
           
           # ... measurement code
                              
In this example, the ``PA1Measurement`` class registers a parameter named ``num_random_shuffles``.

Accessing parameter values as object attributes
-----------------------------------------------

Once registered, the values of parameters are available as instance attributes.
Continuing the ``PA1Measurement`` example:

.. code-block:: python

   pa1 = PA1Measurment(num_random_shuffles=50)
   pa1.num_random_shuffles  # == 50
   
Through attribute access, a parameter's value can be both *read* and *updated*.

Accessing parameters as Datum objects
-------------------------------------

Although the values of parameters can be accessed through object attributes, they are stored internally as `Datum` objects.
You can access these `Datum`\ s as items of the :attr:`~lsst.validate.base.MeasurementBase.parameters` attribute:

.. code-block:: python

   pa1.parameters['num_random_shuffles'].value  # 50
   pa1.parameters['num_random_shuffles'].units  # ''
   pa1.parameters['num_random_shuffles'].label  # 'num_random_shuffles'
   pa1.parameters['num_random_shuffles'].description  # 'Number of random shuffles'

Alternative ways of registering parameters
------------------------------------------

The :meth:`~lsst.validate.base.MeasurementBase.register_parameter` method is flexible in terms of its arguments.
For example, it's possible to first register a parameter and set its value later:

.. code-block:: python

   self.register_parameter('num_random_shuffles', units='',
                           description='Number of random shuffles')
   # ...
   self.num_random_shuffles = 50

Here, a label is not set; in this case the ``label`` defaults to the name of the parameter itself.

It's also possible to provide a `Datum` to `MeasurementBase.register_parameter`:

.. code-block:: python

   self.registerParameter('num_random_shuffles',
                          datum=Datum(50, '', label='shuffles',
                                      description='Number of random shuffles'))

This can be useful when copying a parameter already available as a :class:`~lsst.validate.base.Datum`.

.. _validate-base-measurement-extras:

Storing Extra Measurement Outputs
=================================

Although metric measurements are strictly scalar values, your measurement might yield additional data that you want make available through the SQUASH dashboard.
This additional data are called *extras*.

Registering extras is similar to registering parameters, except that the `MeasurementBase.register_extra` method is used.
As an example, the PA1 measurement code (``~lsst.validate.drp.calcsrd.PA1Measurement``) stores the inter-quartile range, RMS and magnitude difference of pairs of stars multiple random samples, along with mean magnitude of each pair of observed stars:

.. code-block:: python

   class PA1Measurement(MeasurementBase):
   
          metric = None
          value = None
          units = 'mmag'
          label = 'PA1'

          def __init__(self, yaml_path, num_random_shuffles=50):
              MeasurementBase.__init__(self)
              
              self.metric = Metric.from_yaml(self.label, yaml_path=yaml_path)
              
              # register extras
              self.register_extra('rms', units='mmag',
                                  description='Photometric repeatability RMS of '
                                              'stellar pairs for each random sampling')
              self.register_extra('iqr', units='mmag',
                                  description='Photometric repeatability IQR of '
                                              'stellar pairs for each random sample')
              self.register_extra('mag_diff', units='mmag',
                                  description='Difference magnitudes of stellar source pairs'
                                              'for each random sample')
              self.register_extra('mag_mean', units='mag',
                                  description='Mean magnitude of pairs of stellar '
                                              'sources matched across visits, for '
                                              'each random sample.')

              # ... make measurements
              
              # Set values of extras
              self.rms = np.array([pa1.rms for pa1 in pa1Samples])
              self.iqr = np.array([pa1.iqr for pa1 in pa1Samples])
              self.mag_diff = np.array([pa1.mag_diffs for pa1 in pa1Samples])
              self.mag_mean = np.array([pa1.mag_mean for pa1 in pa1Samples])
       
              # The scalar metric measurement
              self.value = np.mean(self.iqr)

`MeasurementBase.register_extra` method works just like :meth:`MeasurementBase.register_parameter` method.
Specifically, the value of the extra can be set at registration time, or afterwards by setting an instance attribute (shown above).
An extra can also be registered with a pre-made :class:`~lsst.validate.base.Datum` object.

Accessing and updating the values and Datum objects of measurement extras
-------------------------------------------------------------------------

Extras are stored internally as `Datum` objects.
You can access these `Datum`\ s as key values of the `MeasurementBase.extras` attribute.
Following the PA1 measurement example:

.. code-block:: python

   pa1 = PA1Measurement()
   pa1.extras['rms'].value  # == pa1.rms
   pa1.extras['rms'].units  # 'mmag'
   pa1.extras['rms'].label  # 'rms'
   pa1.extras['rms'].decription  # 'Photometric repeatability RMS ...'


.. _SQUASH: https://squash.lsst.codes
