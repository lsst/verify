.. lsst-task-topic:: lsst.verify.tasks.MetadataMetricTask

##################
MetadataMetricTask
##################

``MetadataMetricTask`` is a base class for generating `~lsst.verify.Measurement`\ s from task metadata of the same granularity.
The class handles loading metadata and extracting the keys of interest, while subclasses are responsible for creating the `~lsst.verify.Measurement` from the extracted values.

See :lsst-task:`~lsst.verify.tasks.MultiMetadataMetricTask` for metrics computed from several finer-grained metadata.

``MetadataMetricTask`` is currently a subclass of `lsst.verify.gen2tasks.MetricTask`.
It is expected that ``MetadataMetricTask`` can be migrated to the Gen 3 framework without affecting its subclasses.

.. _lsst.verify.tasks.MetadataMetricTask-summary:

Processing summary
==================

``MetadataMetricTask`` runs this sequence of operations:

#. Find the metadata key(s) needed to compute the metric by calling the customizable `~lsst.verify.tasks.MetadataMetricTask.getInputMetadataKeys` method.
#. Search the metadata object passed to `~lsst.verify.tasks.MetadataMetricTask.run` for the keys, and extract the corresponding values.
#. Process the values by calling the customizable `~lsst.verify.tasks.MetadataMetricTask.makeMeasurement` method, and return the `~lsst.verify.Measurement`.

.. _lsst.verify.tasks.MetadataMetricTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.tasks.MetadataMetricTask

.. _lsst.verify.tasks.MetadataMetricTask-butler:

Butler datasets
===============

Input datasets
--------------

:lsst-config-field:`~lsst.verify.tasks.MetadataMetricTask.MetadataMetricConfig.metadata`
    The metadata of the top-level command-line task (e.g., ``ProcessCcdTask``, ``ApPipeTask``) being instrumented.
    Because the metadata produced by each top-level task is a different Butler dataset type, this dataset **must** be explicitly configured when running ``MetadataMetricTask`` or a :lsst-task:`~lsst.verify.gen2tasks.MetricsControllerTask` that contains it.

.. _lsst.verify.tasks.MetadataMetricTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.MetadataMetricTask

.. _lsst.verify.tasks.MetadataMetricTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.MetadataMetricTask
