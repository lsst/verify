.. currentmodule:: lsst.verify

.. _lsst.verify:

###########
lsst.verify
###########

`lsst.verify` is a framework for packages that measure software and data quality metrics.
A metric can be any measurable scalar quantity; some examples are in the  LSST Science Requirements Document (:lpm:`17`), though packages can also define ad hoc metrics.
Measurements made through `lsst.verify` can be uploaded to LSST's SQUASH_ monitoring dashboard to help you see how code development affects performance.

.. seealso::

   `SQR-019: LSST Verification Framework API Demonstration <https://sqr-019.lsst.io>`_.

.. _lsst.verify-using:

Using lsst.verify
=================

.. toctree::
   :maxdepth: 1

   reviewing-verification-json-on-the-command-line

.. _lsst.verify-contributing:

Contributing
============

``lsst.verify`` is developed at https://github.com/lsst/verify.
You can find Jira issues for this module under the `verify <https://jira.lsstcorp.org/issues/?jql=project%20%3D%20DM%20AND%20component%20%3D%20verify>`_ component.

.. _lsst.verify-command-line-taskref:

Task reference
==============

.. _lsst.verify-pipeline-tasks:

Pipeline tasks
------------------

.. lsst-pipelinetasks::
   :root: lsst.verify
   :toctree: tasks

.. .. _lsst.verify-command-line-tasks:
..
.. Command-line tasks
.. ------------------
..
.. .. lsst-cmdlinetasks::
..    :root: lsst.verify

.. _lsst.verify-tasks:

Tasks
-----

.. lsst-tasks::
   :root: lsst.verify
   :toctree: tasks

.. .. _lsst.verify-configs:
..
.. Configurations
.. --------------
..
.. .. lsst-configs::
..    :root: lsst.verify
..    :toctree: configs

.. _lsst.verify-scripts:

Script reference
================

.. toctree::
   :maxdepth: 1

   scripts/dispatch_verify.py
   scripts/inspect_job.py
   scripts/lint_metrics.py

.. _lsst.verify-pyapi:

Python API reference
====================

.. automodapi:: lsst.verify
   :no-main-docstr:

.. automodapi:: lsst.verify.bin.dispatchverify
   :no-main-docstr:

.. automodapi:: lsst.verify.jsonmixin
   :no-main-docstr:
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.metadata.eupsmanifest
   :no-main-docstr:
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.metadata.jenkinsci
   :no-main-docstr:
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.metadata.lsstsw
   :no-main-docstr:
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.squash
   :no-main-docstr:
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.report
   :no-main-docstr:
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.gen2tasks
   :no-main-docstr:
   :no-inheritance-diagram:

.. automodapi:: lsst.verify.tasks
   :no-main-docstr:
   :no-inheritance-diagram:

.. _SQUASH: https://squash.lsst.codes
