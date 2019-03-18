.. lsst-task-topic:: lsst.verify.tasks.ppdbMetricTask.ConfigPpdbLoader

################
ConfigPpdbLoader
################

``ConfigPpdbLoader`` creates a `lsst.dax.ppdb.Ppdb` object from a science task config that contains a `~lsst.dax.ppdb.PpdbConfig`.
This provides users with a `~lsst.dax.ppdb.Ppdb` object that accesses the same database as the original science task.

This task is intended for use as a subtask of :lsst-task:`lsst.verify.tasks.ppdbMetricTask.PpdbMetricTask`.

.. _lsst.verify.tasks.ConfigPpdbLoader-summary:

Processing summary
==================

``ConfigPpdbLoader`` takes a config as input, and searches it and all sub-configs for a `lsst.dax.ppdb.PpdbConfig`.
If it finds one, it constructs a `~lsst.dax.ppdb.Ppdb` object based on that config and returns it.
If the input config has multiple `~lsst.dax.ppdb.PpdbConfig` sub-configs, ``ConfigPpdbLoader`` does not make any guarantees about which one will be used.

.. _lsst.verify.tasks.ConfigPpdbLoader-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.tasks.ConfigPpdbLoader

.. _lsst.verify.tasks.ConfigPpdbLoader-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.ConfigPpdbLoader

.. _lsst.verify.tasks.ConfigPpdbLoader-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.ConfigPpdbLoader
