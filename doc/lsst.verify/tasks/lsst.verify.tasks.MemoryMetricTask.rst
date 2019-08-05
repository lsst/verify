.. lsst-task-topic:: lsst.verify.tasks.commonMetrics.MemoryMetricTask

################
MemoryMetricTask
################

``MemoryMetricTask`` creates a resident set size `~lsst.verify.Measurement` based on data collected by @\ `~lsst.pipe.base.timeMethod`.
It reads the raw timing data from the top-level `~lsst.pipe.base.CmdLineTask`'s metadata, which is identified by the task configuration.

.. _lsst.verify.tasks.MemoryMetricTask-summary:

Processing summary
==================

``MemoryMetricTask`` searches the metadata for @\ `~lsst.pipe.base.timeMethod`-generated keys corresponding to the method of interest.
If it finds matching keys, it stores the maximum memory usage as a `~lsst.verify.Measurement`.

.. _lsst.verify.tasks.MemoryMetricTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.tasks.commonMetrics.MemoryMetricTask

.. _lsst.verify.tasks.MemoryMetricTask-butler:

Butler datasets
===============

Input datasets
--------------

:lsst-config-field:`~lsst.verify.tasks.commonMetrics.MemoryMetricConfig.metadata`
    The metadata of the top-level command-line task (e.g., ``ProcessCcdTask``, ``ApPipeTask``) being instrumented.
    Because the metadata produced by each top-level task is a different Butler dataset type, this dataset **must** be explicitly configured when running ``MemoryMetricTask`` or a :lsst-task:`~lsst.verify.gen2tasks.MetricsControllerTask` that contains it.

.. _lsst.verify.tasks.MemoryMetricTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.commonMetrics.MemoryMetricTask

.. _lsst.verify.tasks.MemoryMetricTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.commonMetrics.MemoryMetricTask

.. _lsst.verify.tasks.MemoryMetricTask-examples:

Examples
========

.. code-block:: py

   from lsst.verify.tasks import MemoryMetricTask

   config = MemoryMetricTask.ConfigClass()
   config.metadata.name = "apPipe_metadata"
   config.target = "apPipe:ccdProcessor.runDataRef"
   config.metric = "pipe_tasks.ProcessCcdMemory"
   task = MemoryMetricTask(config=config)

   # config.metadata provided for benefit of MetricsControllerTask/Pipeline
   # but since we've defined it we might as well use it
   metadata = butler.get(config.metadata.name)
   processCcdTime = task.run(metadata).measurement
