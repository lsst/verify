############################
Creating Measurement Classes
############################


The :class:`lsst.validate.drp.base.MeasurmentBase` abstract base class defines a standard interface for writing classes that make measurements of metrics.
The :class:`~lsst.validate.drp.base.MeasurementBase` base class ensures that measurements, along with metadata about the measurement, can be serialized and submitted to the QA database and SQUASH dashboard.
This page covers the usage of :class:`~lsst.validate.drp.base.MeasurementBase` for creating measurement classes.

A Minimal Measurement Class
===========================

At a minimum, measurement classes must subclass :class:`~lsst.validate.drp.MeasurementBase` and provide some metadata as instance attributes, such as the name of metric being measured and units of the measurement.
This example is a basic template for a measurement:

.. code-block:: python

   class PA1Measurement(MeasurementBase):

       metric = None
       value = None
       units = 'mmag'
       label = 'PA1'
       
       def __init__(self):
           MeasurementBase.__init__(self)
           
           self.metric = Metric.fromYaml(self.label)
           
           # measurement code
           # ...
           
           self.value = 0  # Scalar value from measurement code

In a measurement class, the following metadata attributes must be specified (their presence is required by the :class:`~lsst.validate.drp.base.MeasurementBase` abstract base class):

:attr:`~lsst.validate.drp.base.MeasurementBase.label`
   The name of the metric.

:attr:`~lsst.validate.drp.base.MeasurementBase.metric`
   A :class:`~lsst.validate.drp.base.Metric` object. In this example, the :meth:`~lsst.validate.drp.Metric.fromYaml` class method constructs a :class:`~lsst.validate.drp.base.Metric` instance for PA1 from the :file:`metrics.yaml` file built into ``validate_drp``.

:attr:`~lsst.validate.drp.base.MeasurementBase.units`
   Units of the metric measurement. As in the :class:`~lsst.validate.drp.base.Datum` class, ``units`` should be an ``astropy.units``-compatible string.

The purpose of a measurement class is to make a make a measurement; those calculations should occur in a measurement instance's ``__init__`` method.
Any data required for a measurement should be provided through the measurement class's ``__init__`` method.

The measurement result is stored in a :attr:`~lsst.validate.drp.base.MeasurementBase.value` attribute:

:attr:`~lsst.validate.drp.base.MeasurementBase.value`
   The value attribute should be a scalar (`float` or `int`), in the same physical units indicated by the ``units`` attribute.
   If a Measurement class is unable to make a measurement, ``value`` should be ``None``.

Storing Measurement Parameters
==============================

Often a measurement code is customized with parameters.
As a means of lightweight provenance, the measurement API provides a way to declare these parameters so that they're persisted to the database using the :meth:`~lsst.validate.drp.base.MeasurementBase.registerParameter` method:

.. code-block:: python

   class PA1Measurement(MeasurementBase):

       metric = None
       value = None
       units = 'mmag'
       label = 'PA1'
       schema = 'pa1-1.0.0'
       
       def __init__(self, numRandomShuffles=50):
           MeasurementBase.__init__(self)
           
           self.metric = Metric.fromYaml(self.label)

           self.registerParameter('numRandomShuffles',
                                  value=numRandomShuffles,
                                  units='',
                                  description='Number of random shuffles')
           
           # ... measurement code
                              
In this example, the ``PA1Measurement`` class registers a parameter named ``numRandomShuffles``.

Accessing parameter values as object attributes
-----------------------------------------------

In addition to registering a parameter for serialization, the :meth:`~lsst.validate.drp.base.MeasurementBase.registerParameter` method makes the values of parameters available as instance attributes.
Continuing the ``PA1Measurement`` example:

.. code-block:: python

   pa1 = PA1Measurment(numRandomShuffles=50)
   pa1.numRandomShuffles # == 50
   
Through attribute access, a parameter's value can be both *read* and *updated*.

Accessing parameters as ``Datum`` objects
-----------------------------------------

Although the values of parameters can be accessed through object attributes, they are stored internally as :class:`~lsst.validate.drp.base.Datum` objects.
These full :class:`~lsst.validate.drp.base.Datum` objects can be accessed as items of the :attr:`~lsst.validate.drp.base.MeasurementBase.parameters` attribute:

.. code-block:: python

   pa1.parameters['numRandomShuffles'].value  # 50
   pa1.parameters['numRandomShuffles'].units  # ''
   pa1.parameters['numRandomShuffles'].label  # numRandomShuffles
   pa1.parameters['numRandomShuffles'].description  # 'Number of random shuffles'

Alternative ways of registering parameters
------------------------------------------

The :meth:`~lsst.validate.drp.MeasurementBase.registerParameter` method is flexible in terms of its arguments.
For example, it's possible to first register a parameter and set its value later:

.. code-block:: python

   self.registerParameter('numRandomShuffles', units='',
                          description='Number of random shuffles')
   # ...
   self.numRandomShuffles = 50

Here, a label is not set; in this case the ``label`` defaults to the name of the parameter itself.

It's also possible to provide a :class:`~lsst.validate.drp.base.Datum` to :meth:`~lsst.validate.drp.MeasurementBase.registerParameter`:

.. code-block:: python

   self.registerParameter('numRandomShuffles',
                          datum=Datum(50, '', label='shuffles',
                                      description='Number of random shuffles'))

This can be useful when copying a parameter already available as a :class:`~lsst.validate.drp.base.Datum`.

Storing Extra Measurement Outputs
=================================

Although metric measurements are strictly scalar values, it can be useful to store additional measurement by-products.
By registering them, these measurement by-products are automatically serialized with the measurement and available to the SQUASH dashboard application to make drive rich plots, such as histograms or scatter plots.
This additional metadata helps a user understand a scalar metric measurement.

Registering measurement outputs is similar to registering parameters, except that the :meth:`~lsst.validate.drp.base.MeasurementBase.registerExtra` method is used.

As an example, the PA1 measurement code (:class:`~lsst.validate.drp.calcsrd.PA1Measurement`) stores the inter-quartile range, RMS and magnitude difference of pairs of stars multiple random samples, along with mean magnitude of each pair of observed stars.

.. code-block:: python

   class PA1Measurement(MeasurementBase):
   
          metric = None
          value = None
          units = 'mmag'
          label = 'PA1'
          schema = 'pa1-1.0.0'
          
          def __init__(self, numRandomShuffles=50):
              MeasurementBase.__init__(self)
              
              self.metric = Metric.fromYaml(self.label)
              
              # register extras
              self.registerExtra('rms', units='mmag',
                                 description='Photometric repeatability RMS of '
                                             'stellar pairs for each random sampling')
              self.registerExtra('iqr', units='mmag',
                                 description='Photometric repeatability IQR of '
                                             'stellar pairsfor each random sample')
              self.registerExtra('magDiff', units='mmag',
                                 description='Difference magnitudes of stellar source pairs'
                                             'for each random sample')
              self.registerExtra('magMean', units='mag',
                                 description='Mean magnitude of pairs of stellar '
                                             'sources matched across visits, for '
                                             'each random sample.')

              # ... make measurements
              
              # Set values of extras
              self.rms = np.array([pa1.rms for pa1 in pa1Samples])
              self.iqr = np.array([pa1.iqr for pa1 in pa1Samples])
              self.magDiff = np.array([pa1.magDiffs for pa1 in pa1Samples])
              self.magMean = np.array([pa1.magMean for pa1 in pa1Samples])
       
              # The scalar metric measurement
              self.value = np.mean(self.iqr)

The :meth:`~lsst.validate.drp.base.MeasurementBase.registerExtra` method works just like the :meth:`~lsst.validate.drp.base.MeasurementBase.registerParameter` method.
Specifically, the value of the extra can be set at registration time.
An extra can also be registered with a pre-made ``Datum`` object.

Accessing and updating the values and Datum objects of measurement extras
-------------------------------------------------------------------------

As with parameters, registering an extra allows the value of the extra to be accessed or updated through a measurement object attribute named after the extra itself (see the above example).

Extras are stored internally as :class:`~lsst.validate.drp.base.Datum` objects, which can be accessed as items of the :attr:`~lsst.validate.drp.base.MeasurementBase.extras` attribute.
Following the PA1 measurement example:

.. code-block:: python

   pa1 = PA1Measurement()
   pa1.extras['rms'].value  # == pa1.rms
   pa1.extras['rms'].units  # 'mmag'
   pa1.extras['rms'].label  # 'rms'
   pa1.extras['rms'].decription  # 'Photometric repeatability RMS ...'
