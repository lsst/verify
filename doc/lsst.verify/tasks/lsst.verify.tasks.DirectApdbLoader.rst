.. lsst-task-topic:: lsst.verify.tasks.apdbMetricTask.DirectApdbLoader

################
DirectApdbLoader
################

``DirectApdbLoader`` creates a `lsst.dax.apdb.Apdb` object from a `~lsst.dax.apdb.ApdbConfig`.
This provides users with a `~lsst.dax.apdb.Apdb` object that accesses the indicated database.

This task is intended for use as a subtask of :lsst-task:`lsst.verify.tasks.apdbMetricTask.ApdbMetricTask`.

.. _lsst.verify.tasks.DirectApdbLoader-summary:

Processing summary
==================

``DirectApdbLoader`` takes a config as input.
It then constructs a `~lsst.dax.apdb.Apdb` object based on that config and returns it.

.. _lsst.verify.tasks.DirectApdbLoader-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.tasks.DirectApdbLoader

.. _lsst.verify.tasks.DirectApdbLoader-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.DirectApdbLoader

.. _lsst.verify.tasks.DirectApdbLoader-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.DirectApdbLoader
