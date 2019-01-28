.. lsst-task-topic:: lsst.verify.compatibility.metadataTask.SquashMetadataTask

##################
SquashMetadataTask
##################

``SquashMetadataTask`` modifies a `~lsst.verify.Job` object to contain metadata that is required for SQuaSH upload.
It is both the default for the :lsst-config-field:`lsst.verify.compatibility.MetricsControllerConfig.metadataAdder` subtask and its reference implementation.

.. _lsst.verify.compatibility.SquashMetadataTask-summary:

Processing summary
==================

``SquashMetadataTask`` currently adds the following metadata:

* ``"instrument"``: the name of the instrument that took the data
* the individual keys of the provided data ID (each `~lsst.verify.Job` produced by :lsst-task:`~lsst.verify.compatibility.MetricsControllerTask` is associated with one data ID, which may be partial)

.. _lsst.verify.compatibility.SquashMetadataTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.compatibility.SquashMetadataTask

.. _lsst.verify.compatibility.SquashMetadataTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.compatibility.SquashMetadataTask

.. _lsst.verify.compatibility.SquashMetadataTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.compatibility.SquashMetadataTask
