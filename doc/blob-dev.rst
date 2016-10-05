.. currentmodule:: lsst.validate.base

.. _creating-blobs:

################################################
Providing Datasets to Measurements through Blobs
################################################

A common pattern is to reduce a raw dataset, and share that dataset between several measurements.
`lsst.validate.base` expresses such datasets as **blobs.**
In the context of the `lsst.validate.base` framework, a blob is an object that contains `Datum` objects.

There are several advantages of storing input datasets in blob objects:

- Any pre-reduction of a raw dataset can be done in the blob object, keeping a codebase organized.
- Blobs can be passed to measurement objects, which simplifies the construction of measurements.
- Blobs are automatically serialized alongside measurements and are available to the SQUASH dashboard. Blobs can be shared among several measurements, with the blob data only be stored once.

Template for a Blob Class
=========================

Blobs are subclasses of `BlobBase` that register one or more `Datum` objects.

.. code-block:: python

   from lsst.validate.base import BlobBase


   class SimpleBlob(BlobBase):

       def __init__(self, g_mags, i_mags):
           BlobBase.__init__(self)

           self.register_datum('g', value=g_mags, units='mag',
                               description='g-band magnitudes')
           self.register_datum('i', value=i_mags, units='mag',
                               description='i-band magnitudes')
           self.register_datum('gi', units='mag',
                               description='g-i colour')

           self.gi = self.g - self.i

In this example, the ``g`` and ``i`` attributes are initially registered with values.
A third blob attribute, ``gi``, is also declared and its value is computed afterwards.

Notice that, like `MeasurementBase.parameters` and `MeasurementBase.extras` attributes of measurement classes, values contained in `BlobBase`-type objects can be accessed and updated directly through instance attributes.

Accessing datum objects
-----------------------

Internally, blob attributes are stored as `Datum` objects, which can be accessed as items of the `BlobBase.datums` attribute.

.. code-block:: python

   blob = SimpleBlob(g, i)
   blob.datums['gi'].value  # == blob.gi
   blob.datums['gi'].units  # 'mag'
   blob.datums['gi'].label  # 'gi', this was automatically set from the name
   blob.datums['gi'].description  # 'g-i colour'

Linking measurements to blobs
-----------------------------

When a blob is used by a measurement, the measurement class should declare that usage so that the SQUASH dashboard can provide rich context to measurements.
Measurement classes can accomplish this simply by making the blob an instance attribute.
For example:

.. code-block:: python

   class MeanColor(MeasurementBase):
   
       label = 'MeanColour'
       units = 'mag'
       
       def __init__(self, simple_blob):
           self.metric = Metric.from_yaml(self.label)
           self.simple_blob = simple_blob
           self.value = np.mean(self.simple_blob.gi)

Accessing blobs in measurements
-------------------------------

In addition to simply accessing blobs associated with a measurement through the instance attribute, blobs are also available as items of the measurement's `MeasurementBase.blobs` attribute:

.. code-block:: python

   color = SimpleBlob(g, i)
   mean_color = MeanColor(color)
   mean_color.blobs['simple_blob'].gi  # array of g-i colours
