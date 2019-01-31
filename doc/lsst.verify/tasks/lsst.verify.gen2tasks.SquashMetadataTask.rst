.. lsst-task-topic:: lsst.verify.gen2tasks.metadataTask.SquashMetadataTask

##################
SquashMetadataTask
##################

``SquashMetadataTask`` modifies a `~lsst.verify.Job` object to contain metadata that is required for SQuaSH upload.
It is both the default for the :lsst-config-field:`lsst.verify.gen2tasks.MetricsControllerConfig.metadataAdder` subtask and its reference implementation.

.. _lsst.verify.gen2tasks.SquashMetadataTask-summary:

Processing summary
==================

``SquashMetadataTask`` currently adds the following metadata:

* ``"instrument"``: the name of the instrument that took the data
* the individual keys of the provided data ID (each `~lsst.verify.Job` produced by :lsst-task:`~lsst.verify.gen2tasks.MetricsControllerTask` is associated with one data ID, which may be partial)

.. _lsst.verify.gen2tasks.SquashMetadataTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.gen2tasks.SquashMetadataTask

.. _lsst.verify.gen2tasks.SquashMetadataTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.gen2tasks.SquashMetadataTask

.. _lsst.verify.gen2tasks.SquashMetadataTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.gen2tasks.SquashMetadataTask
