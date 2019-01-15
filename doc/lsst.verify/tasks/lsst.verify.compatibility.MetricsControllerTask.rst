.. lsst-task-topic:: lsst.verify.compatibility.MetricsControllerTask

.. currentmodule:: lsst.verify.compatibility

#####################
MetricsControllerTask
#####################

``MetricsControllerTask`` runs collections of :lsst-task:`lsst.verify.compatibility.MetricTask`, and stores the resulting `~lsst.verify.Measurement` objects using the `~lsst.verify.Job` persistence framework.
It is a stand-in for functionality provided by the Gen 3 Tasks framework.
The datasets that ``MetricsControllerTask`` consumes depend on the :lsst-task:`~lsst.verify.compatibility.MetricTask`\ s to be run, and are handled automatically.

``MetricsControllerTask`` is not a command-line task, but may be called from within both task- and non-task pipelines.

.. _lsst.verify.compatibility.MetricsControllerTask-summary:

Processing summary
==================

Unlike most tasks, ``MetricsControllerTask`` has a `~MetricsControllerTask.runDataRefs` method that takes a list of data references.
``MetricsControllerTask`` calls every :lsst-task:`~lsst.verify.compatibility.MetricTask` in :lsst-config-field:`~lsst.verify.compatibility.MetricsControllerConfig.measurers` on every data reference, loading any datasets necessary.
It produces one `~lsst.verify.Job` object for each input data reference, and writes them to disk.

.. _lsst.verify.compatibility.MetricsControllerTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.compatibility.MetricsControllerTask

.. _lsst.verify.compatibility.MetricsControllerTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.compatibility.MetricsControllerTask

.. _lsst.verify.compatibility.MetricsControllerTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.compatibility.MetricsControllerTask

.. _lsst.verify.compatibility.MetricsControllerTask-indepth:

In Depth
========

Because ``MetricsControllerTask`` applies every :lsst-task:`~lsst.verify.compatibility.MetricTask` to every input data reference indiscriminately, it may not give good results with metrics or data references having a mixture of granularities (e.g., CCD-level, visit-level, dataset-level).
The recommended way around this limitation is to create multiple ``MetricsControllerTask`` objects, and configure each one for metrics of a single granularity.

Each :lsst-task:`~lsst.verify.compatibility.MetricTask` in a ``MetricsControllerTask`` must measure a different metric, or they will overwrite each others' values.

.. _lsst.verify.compatibility.MetricsControllerTask-examples:

Examples
========

.. code-block:: py

   from lsst.verify.compatibility import register, \
       MetricTask, MetricsControllerTask


   @register("ultimate")
   class UltimateMetric(MetricTask):
       ...


   @register("second")
   class SecondaryMetric(MetricTask):
       ...


   config = MetricsControllerTask.ConfigClass()
   config.measurers = ["ultimate", "second"]
   config.measurers["ultimate"].answer = 42
   task = MetricsControllerTask(config)

   # CCD-level metrics need CCD-level datarefs
   # Exact dataset type doesn't matter
   datarefs = [butler.subset("calexp", visit=42, ccd=ccd)
               for ccd in range(1, 101)]
   struct = task.runDataRefs(datarefs)
   assert len(struct.jobs) == len(datarefs)
