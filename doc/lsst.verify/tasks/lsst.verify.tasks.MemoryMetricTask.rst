.. lsst-task-topic:: lsst.verify.tasks.commonMetrics.MemoryMetricTask

################
MemoryMetricTask
################

``MemoryMetricTask`` creates a resident set size `~lsst.verify.Measurement` based on data collected by @\ `~lsst.utils.timer.timeMethod`.
It reads the raw timing data from the top-level `~lsst.pipe.base.PipelineTask`'s metadata, which is identified by the task configuration.

@\ `~lsst.utils.timer.timeMethod` measures the peak memory usage from process start, so the results can be contaminated by previous quanta (different tasks, data IDs, or both) run on the same process.
Interpret the results with care.

Because @\ `~lsst.utils.timer.timeMethod` gives platform-dependent results, this task may give incorrect results (e.g., units) when run in a distributed system with heterogeneous nodes.

.. _lsst.verify.tasks.MemoryMetricTask-summary:

Processing summary
==================

``MemoryMetricTask`` searches the metadata for @\ `~lsst.utils.timer.timeMethod`-generated keys corresponding to the method of interest.
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

``metadata``
    The metadata of the top-level pipeline task (e.g., ``CharacterizeImageTask``, ``DiaPipeTask``) being instrumented.

Output datasets
---------------

``measurement``
    The value of the metric.
    The dataset type should not be configured directly, but should be set
    changing the ``package`` and ``metric`` template variables to the metric's
    namespace (package, by convention) and in-package name, respectively.
    Subclasses that only support one metric should set these variables
    automatically.

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
   config.connections.metadata = "apPipe_metadata"
   config.connections.package = "pipe_tasks"
   cofig.connections.metric = "ProcessCcdMemory"
   config.target = "apPipe:ccdProcessor.runDataRef"
   task = MemoryMetricTask(config=config)

   # config.connections provided for benefit of Pipeline
   # but since we've defined it we might as well use it
   metadata = butler.get(config.connections.metadata)
   processCcdTime = task.run(metadata).measurement
