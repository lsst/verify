.. _lsst.verify.inspect_job:

###########################################################################
Reviewing verification JSON outputs on the command line with inspect_job.py
###########################################################################

|inspect_job| is a command-line tool that lets you quickly see what information is stored in the ``*verify.json`` files generated whenever you run code that integrates with LSST's verification framework (:doc:`lsst.verify <index>`).
It's particularly useful when you want to see measurement values and don't need a full report comparing measurements to metric specifications.

.. seealso::

   See :doc:`scripts/inspect_job.py` for a complete reference of that script's command-line interface.

.. _SQR-019: https://sqr-019.lsst.io

Running inspect_job.py
======================

|inspect_job| takes one or more verification framework JSON files as command-line arguments.
Since JSON files output by the verification framework generally have names that end with :file:`verify.json`, you can quickly inspect all available outputs by using a ``*verify.json`` wildcard:

.. prompt:: bash

   inspect_job.py *.verify.json

Interpreting the results
========================

|inspect_job| prints a report for each file passed to it.
An example report looks like this:

.. code-block:: none

   Common metadata:
                                       ccdnum = 42
                                        visit = 411657
                                       object = Blind15A_26
                                         date = 2015-02-19
                                   instrument = DECAM
                                       filter = g

   Measurements:
                      ip_diffim.numSciSources =  1326.0 ct
         ip_diffim.fracDiaSourcesToSciSources =     0.0385
   ap_association.totalUnassociatedDiaObjects =   540.0 ct
                           ap_pipe.ApPipeTime =  63.1475 s ({'estimator': 'pipe.base.timeMethod'})
                    pipe_tasks.ProcessCcdTime =  24.3298 s ({'estimator': 'pipe.base.timeMethod'})
                               ip_isr.IsrTime =   0.9623 s ({'estimator': 'pipe.base.timeMethod'})
             pipe_tasks.CharacterizeImageTime =   7.5473 s ({'estimator': 'pipe.base.timeMethod'})
                     pipe_tasks.CalibrateTime =  11.0519 s ({'estimator': 'pipe.base.timeMethod'})
               pipe_tasks.ImageDifferenceTime =  37.5217 s ({'estimator': 'pipe.base.timeMethod'})
          meas_algorithms.SourceDetectionTime =   1.0205 s ({'estimator': 'pipe.base.timeMethod'})
                      ip_diffim.DipoleFitTime =   1.9112 s ({'estimator': 'pipe.base.timeMethod'})
               ap_association.AssociationTime =   0.6594 s ({'estimator': 'pipe.base.timeMethod'})
              ap_association.numNewDiaObjects =    51.0 ct
         ap_association.fracUpdatedDiaObjects =        0.0
     ap_association.numUnassociatedDiaObjects =     0.0 ct

Each report starts with the job-level metadata in the file, formatted as one key-value pair per line.

Next, the report lists each measurement in the JSON file, including:

- The metric's fully-qualified name.
- The measurement, including units if applicable.
- Any additional metadata associated specifically with that measurement.

Going further
=============

|inspect_job| provides easy access to measurements and metadata in the verification framework's JSON output files.
If you're developing tasks that generic metric measurements, |inspect_job| is often enough.

However, if you need to generate a report that compares measurements against specifications, you can directly use the `~lsst.verify.Job` and `~lsst.verify.report.Report` Python APIs.
The :sqr:`019` technical note includes a demo of this method.

.. |inspect_job| replace:: :doc:`inspect_job.py <scripts/inspect_job.py>`
