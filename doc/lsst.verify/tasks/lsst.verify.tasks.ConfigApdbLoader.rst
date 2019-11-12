.. lsst-task-topic:: lsst.verify.tasks.apdbMetricTask.ConfigApdbLoader

################
ConfigApdbLoader
################

``ConfigApdbLoader`` creates a `lsst.dax.apdb.Apdb` object from a science task config that contains a `~lsst.dax.apdb.ApdbConfig`.
This provides users with a `~lsst.dax.apdb.Apdb` object that accesses the same database as the original science task.

This task is intended for use as a subtask of :lsst-task:`lsst.verify.tasks.apdbMetricTask.ApdbMetricTask`.

.. _lsst.verify.tasks.ConfigApdbLoader-summary:

Processing summary
==================

``ConfigApdbLoader`` takes a config as input, and searches it and all sub-configs for a `lsst.dax.apdb.ApdbConfig`.
If it finds one, it constructs a `~lsst.dax.apdb.Apdb` object based on that config and returns it.
If the input config has multiple `~lsst.dax.apdb.ApdbConfig` sub-configs, ``ConfigApdbLoader`` does not make any guarantees about which one will be used.

.. _lsst.verify.tasks.ConfigApdbLoader-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.tasks.ConfigApdbLoader

.. _lsst.verify.tasks.ConfigApdbLoader-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.ConfigApdbLoader

.. _lsst.verify.tasks.ConfigApdbLoader-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.ConfigApdbLoader
