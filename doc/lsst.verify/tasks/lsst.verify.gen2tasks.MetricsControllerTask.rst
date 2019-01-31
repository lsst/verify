.. lsst-task-topic:: lsst.verify.gen2tasks.MetricsControllerTask

.. currentmodule:: lsst.verify.gen2tasks

#####################
MetricsControllerTask
#####################

``MetricsControllerTask`` runs collections of :lsst-task:`lsst.verify.gen2tasks.MetricTask`, and stores the resulting `~lsst.verify.Measurement` objects using the `~lsst.verify.Job` persistence framework.
It is a stand-in for functionality provided by the Gen 3 Tasks framework.
The datasets that ``MetricsControllerTask`` consumes depend on the :lsst-task:`~lsst.verify.gen2tasks.MetricTask`\ s to be run, and are handled automatically.

``MetricsControllerTask`` is not a command-line task, but may be called from within both task- and non-task pipelines.

.. _lsst.verify.gen2tasks.MetricsControllerTask-summary:

Processing summary
==================

Unlike most tasks, ``MetricsControllerTask`` has a `~MetricsControllerTask.runDataRefs` method that takes a list of data references.
``MetricsControllerTask`` calls every :lsst-task:`~lsst.verify.gen2tasks.MetricTask` in :lsst-config-field:`~lsst.verify.gen2tasks.MetricsControllerConfig.measurers` on every data reference, loading any datasets necessary.
It produces one `~lsst.verify.Job` object for each input data reference, and writes them to disk.

.. _lsst.verify.gen2tasks.MetricsControllerTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.gen2tasks.MetricsControllerTask

.. _lsst.verify.gen2tasks.MetricsControllerTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.gen2tasks.MetricsControllerTask

.. _lsst.verify.gen2tasks.MetricsControllerTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.gen2tasks.MetricsControllerTask

.. _lsst.verify.gen2tasks.MetricsControllerTask-indepth:

In Depth
========

Because ``MetricsControllerTask`` applies every :lsst-task:`~lsst.verify.gen2tasks.MetricTask` to every input data reference indiscriminately, it may not give good results with metrics or data references having a mixture of granularities (e.g., CCD-level, visit-level, dataset-level).
The recommended way around this limitation is to create multiple ``MetricsControllerTask`` objects, and configure each one for metrics of a single granularity.

Each :lsst-task:`~lsst.verify.gen2tasks.MetricTask` in a ``MetricsControllerTask`` must measure a different metric, or they will overwrite each others' values.

.. _lsst.verify.gen2tasks.MetricsControllerTask-examples:

Examples
========

Typically, a user of ``MetricsControllerTask`` will configure it with tasks that have `register` decorator:

.. code-block:: py

   from lsst.verify.gen2tasks import register, \
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

A :lsst-task:`~lsst.verify.gen2tasks.MetricTask` must have the `registerMultiple` decorator to be used multiple times:

.. code-block:: py

   from lsst.verify.gen2tasks import registerMultiple, MetricTask, MetricsControllerTask

   @registerMultiple("common")
   class CommonMetric(MetricTask):
       ...

   config = MetricsControllerTask.ConfigClass()
   config.measurers = ["common"]
   config.measurers["common"].configs["case1"] = CommonMetric.ConfigClass()
   config.measurers["common"].configs["case1"].metric = "misc_tasks.Case1Metric"
   config.measurers["common"].configs["case2"] = CommonMetric.ConfigClass()
   config.measurers["common"].configs["case2"].metric = "misc_tasks.Case2Metric"
   task = MetricsControllerTask(config)

``MetricsControllerTask`` will create and run two different ``CommonMetric`` objects, one configured with ``metric = "misc_tasks.Case1Metric"`` and one with ``metric = "misc_tasks.Case2Metric"``.
The names ``"case1"`` and ``"case2"`` can be anything, so long as they are unique.
