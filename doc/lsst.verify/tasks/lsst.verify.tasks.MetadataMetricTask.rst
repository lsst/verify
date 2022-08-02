.. lsst-task-topic:: lsst.verify.tasks.MetadataMetricTask

##################
MetadataMetricTask
##################

``MetadataMetricTask`` is a base class for generating `~lsst.verify.Measurement`\ s from task metadata of the same granularity.
The class handles loading metadata and extracting the keys of interest, while subclasses are responsible for creating the `~lsst.verify.Measurement` from the extracted values.

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

`metadata``
    The metadata of the top-level command-line task (e.g., ``ProcessCcdTask``, ``ApPipeTask``) being instrumented.

Output datasets
---------------

``measurement``
    The value of the metric.
    The dataset type should not be configured directly, but should be set
    changing the ``package`` and ``metric`` template variables to the metric's
    namespace (package, by convention) and in-package name, respectively.
    Subclasses that only support one metric should set these variables
    automatically.

.. _lsst.verify.tasks.MetadataMetricTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.MetadataMetricTask

.. _lsst.verify.tasks.MetadataMetricTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.MetadataMetricTask
