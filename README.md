A set of utilities to run the processCcd task on some 
CFHT data and DECam data
and validate the astrometry of the results.

Pre-requisites: install and declare the following  
1. `pipe_tasks` from the LSST DM stack (note that pipe_tasks is included with lsst_apps, which is the usual thing to install)  
2. `obs_decam` from https://github.com/lsst/obs_decam   
3. `obs_cfht` from https://github.com/lsst/obs_cfht   
4. `validation_data_cfht` from https://github.com/lsst/validation_data_cfht  
5. `validation_data_decam` from https://github.com/lsst/validation_data_decam  

The `obs_decam` and `obs_cfht` products are also buildable by the standard LSST DM stack tools: `lsstsw` or `eups distrib`.  But they (intentionally) aren't in the dependency tree of `lsst_apps`.  If you have a stack already installed with `lsst_apps`, you can install `obs_decam` and `obs_cfht` in the same manner.  E.g.,

```
eups distrib obs_decam obs_cfht
```

XOR

```
rebuild obs_decam obs_cfht
```

------
To setup for a run with CFHT:
```
setup obs_cfht 
setup validation_data_cfht
```
If you did not declare `obs_cfht` and `validation_data_cfht` current then also specify the version name you used

`validation_data_cfht` contains both the test CFHT data and selected SDSS reference catalogs in astrometry.net format.

Run the measurement algorithm processing and astrometry test with
```
cd validate_drp
sh examples/runCfhtTest.sh
```

------
To setup for a run with DECam:
```
setup obs_decam
setup validation_data_decam
```
If you did not declare `obs_decam` and `validation_data_decam` current then also specify the version name you used

`validation_data_decam` contains both the test DECam data and selected SDSS reference catalogs in astrometry.net format.

Run the measurement algorithm processing and astrometry test with
```
cd validate_drp
sh examples/runDecamTest.sh
```

The last line of the output will give the median astrometric scatter (in milliarcseconds) for stars with mag < 21.

------
While `examples/runCfhtTest.sh` does everything, here is some examples of running the processing/measurement steps individually.  While these examples are from  the CFHT validation example, analogous commands would work for DECam.

1. Make sure the astrometry.net environment variable is pointed to the right place for this validation set:
    ```
    export ASTROMETRY_NET_DATA_DIR=${VALIDATION_DATA_CFHT_DIR}/astrometry_net_data
    ```

2. Ingest the files into the repository
    ```
    ingestImages.py CFHT/input "${VALIDATION_DATA_CFHT_DIR}"/raw/*.fz --mode link
    ```

Once these basic steps are completed, then you can run any of the following:

* To process all CCDs with the new (now default) AstrometryTask use newAstrometryConfig.py:
    ```
    processCcd.py CFHT/input @runCfht.list --configfile newAstrometryConfig.py --clobber-config -j 6 --output junk
    ```

* To process all CCDs with the old ANetAstrometryTask:
    ```
    processCcd.py CFHT/input @runCfht.list --configfile anetAstrometryConfig.py --clobber-config -j 6 --output CFHT/output
    ./validateCfht.py CFHT/output
    ```

* To process one CCD with the new AstrometryTask:
    ```
    processCcd.py CFHT/input  --id visit=850587 ccd=21 --configfile newAstrometryConfig.py --clobber-config --output junk
    ```

* Or process one CCD with the ANetAstrometryTask:  
    ```
    processCcd.py CFHT/input --id visit=850587 ccd=21 --configfile anetAstrometryConfig.py --clobber-config --output junk
    ```

* Run the validation test
    ```
    validateCfht.py CFHT/output
    ```

Note that the example validation test selects several of the CCDs and will fail if you just pass it a repository with 1 visit or just 1 CCD.

Files :
-------
* `examples/runCfhtTest.sh`  : CFHT Run initialization, ingest, measurement, and astrometry validation.
* `examples/runDecamTest.sh` : DECam Run initialization, ingest, measurement, and astrometry validation.
* `examples/validateCfht.py`    : CFHT run some analysis on the output data produced by processCcd.py
* `examples/validateDecam.py`   : DECam run some analysis on the output data produced by processCcd.py
* `examples/runCfht.list`    : CRHT list of vistits / ccd to be processed by processCcd
* `examples/runDecam.list`   : DECam list of vistits / ccd to be processed by processCcd
* `config/newAstrometryConfig.py`  : configuration for running processCcd with the new AstrometryTask
* `config/anetAstrometryConfig.py` : configuration for running processCcd ANetAstrometryTask
* `README.md` : THIS FILE.  Guide and examples.
