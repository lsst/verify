.. lsst-task-topic:: lsst.verify.tasks.MultiMetadataMetricTask

#######################
MultiMetadataMetricTask
#######################

``MultiMetadataMetricTask`` is a base class for generating `~lsst.verify.Measurement`\ s from task metadata of a higher granularity than the metric.
The class handles loading metadata and extracting the keys of interest, while subclasses are responsible for creating the `~lsst.verify.Measurement` from the extracted values.

See :lsst-task:`~lsst.verify.tasks.MetadataMetricTask` for when the metadata and metric have the same granularity.

``MultiMetadataMetricTask`` is currently a subclass of `lsst.verify.gen2tasks.MetricTask`.
It is expected that ``MultiMetadataMetricTask`` can be migrated to the Gen 3 framework without affecting its subclasses.

.. _lsst.verify.tasks.MultiMetadataMetricTask-summary:

Processing summary
==================

``MultiMetadataMetricTask`` runs this sequence of operations:

#. Find the metadata key(s) needed to compute the metric by calling the customizable `~lsst.verify.tasks.MultiMetadataMetricTask.getInputMetadataKeys` method.
#. Search all the metadata objects passed to `~lsst.verify.tasks.MultiMetadataMetricTask.run` for the keys, and extract the corresponding values.
#. Process the values by calling the customizable `~lsst.verify.tasks.MultiMetadataMetricTask.makeMeasurement` method, and return the `~lsst.verify.Measurement`.

.. _lsst.verify.tasks.MultiMetadataMetricTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.tasks.MultiMetadataMetricTask

.. _lsst.verify.tasks.MultiMetadataMetricTask-butler:

Butler datasets
===============

Input datasets
--------------

:lsst-config-field:`~lsst.verify.tasks.MultiMetadataMetricTask.MetadataMetricConfig.metadata`
    The metadata of the top-level command-line task (e.g., ``ProcessCcdTask``, ``ApPipeTask``) being instrumented.
    Because the metadata produced by each top-level task is a different Butler dataset type, this dataset **must** be explicitly configured when running ``MultiMetadataMetricTask`` or a :lsst-task:`~lsst.verify.gen2tasks.MetricsControllerTask` that contains it.

.. _lsst.verify.tasks.MultiMetadataMetricTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.MultiMetadataMetricTask

.. _lsst.verify.tasks.MultiMetadataMetricTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.MultiMetadataMetricTask
