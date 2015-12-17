This directory contains a set of utilities to run the processCcd task on some CFHT data
and validate the astrometry of the results.

Pre-requisites: install and declare the following
- pipe_tasks version 10.1 from the LSST DM stack (note that pipe_tasks is included with lsst_apps,
    which is the usual thing to install)
- obs_cfht from https://github.com/lsst/obs_cfht (this package is not included with lsst_apps);
    declare this with tag "current"

To initialize the input repository:
./init_input.sh

To setup for a run:
setup pipe_tasks
setup display_ds9 -k
setup obs_cfht -k  # if you did not declare obs_cfht current then also specify the version name you used
# The following installs the specialied astrometry_net_data directory that contains only the SDSS catalogs for the test data fields of CFHT data.
setup -r astrometry_net_data -j

To process all CCDs with the new (now default) AstrometryTask use newAstrometryConfig.py:
processCcd.py input @run.list --configfile newAstrometryConfig.py --clobber-config -j 6 --output junk

To process all CCDs with the old ANetAstrometryTask:
processCcd.py input @run.list --configfile anetAstrometryConfig.py --clobber-config -j 6 --output <outputPath>
./valid_cfht.py <outputPath>

To process one CCD with the new AstrometryTask:
processCcd.py input  --id visit=850587 ccd=21 --configfile newAstrometryConfig.py --clobber-config --output junk

Or process one CCD with the ANetAstrometryTask:
processCcd.py input --id visit=850587 ccd=21 --configfile anetAstrometryConfig.py --clobber-config --output junk

Directories :
-------------
rawDownload     : contain raw CFHT images (flat, dark, bias, fringe,... corrected)
reference_plots : contain reference plots corresponding to the best results obtain so far.

Files :
-------
init_input.sh    : script to initialize the input directory
valid_cfht.py    : run some analysis on the output data produced by processCcd.py
newAstrometryConfig.py  : configuration for running processCcd with the new AstrometryTask
anetAstrometryConfig.py : configuration for running processCcd ANetAstrometryTask
run.list         : list of vistits / ccd to be processed by processCcd
