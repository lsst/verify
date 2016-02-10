A set of utilities to run the processCcd task on some 
CFHT data and DECam data
and validate the astrometric and photometric repeatability of the results.

Pre-requisites: install and declare the following

1. `pipe_tasks` from the LSST DM stack (note that pipe_tasks is included with lsst_apps, which is the usual thing to install)
2. `obs_decam` from https://github.com/lsst/obs_decam
3. `obs_cfht` from https://github.com/lsst/obs_cfht
4. `validation_data_cfht` from https://github.com/lsst/validation_data_cfht
5. `validation_data_decam` from https://github.com/lsst/validation_data_decam

The `obs_decam`, `obs_cfht`, `validation_data_cfht`, `validation_data_decam`, `validate_drp` products are also buildable by the standard LSST DM stack tools: `lsstsw` or `eups distrib`.  But they (intentionally) aren't in the dependency tree of `lsst_apps`.  If you have a stack already installed with `lsst_apps`, you can install these in the same manner.  E.g.,

```
eups distrib install obs_decam obs_cfht validation_data_decam validation_data_cfht validate_drp
```

XOR

```
rebuild -u obs_decam obs_cfht validation_data_decam validation_data_cfht validate_drp
```

------
To setup for a run with CFHT:
```
setup obs_cfht 
setup validation_data_cfht
setup validate_drp
```
As usual, if any of these packages are not declared current you will also need to specify a version or tag.

`validation_data_cfht` contains both the test CFHT data and selected SDSS reference catalogs in astrometry.net format.

Run the measurement algorithm processing and astrometry test with
```
cd $VALIDATE_DRP_DIR
sh examples/runCfhtTest.sh
```

------
To setup for a run with DECam:
```
setup obs_decam
setup validation_data_decam
setup validate_drp
```
As usual, if any of these packages are not declared current you will also need to specify a version or tag.

`validation_data_decam` contains both the test DECam data and selected SDSS reference catalogs in astrometry.net format.

Run the measurement algorithm processing and astrometry test with
```
cd $VALIDATE_DRP_DIR
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

* To process all CCDs with the standard AstrometryTask and 6 threads use newAstrometryConfig.py:
    ```
    processCcd.py CFHT/input @examples/runCfht.list --configfile config/newAstrometryConfig.py --clobber-config -j 6 --output CFHT/output
    ```

* To process all CCDs with the old ANetAstrometryTask and 6 threads:
    ```
    processCcd.py CFHT/input @examples/runCfht.list --configfile config/anetAstrometryConfig.py --clobber-config -j 6 --output CFHT/output
    ./validateCfht.py CFHT/output
    ```

* To process one CCD with the new AstrometryTask:
    ```
    processCcd.py CFHT/input  --id visit=850587 ccd=21 --configfile config/newAstrometryConfig.py --clobber-config --output tempout
    ```

* Or process one CCD with the ANetAstrometryTask:
    ```
    processCcd.py CFHT/input --id visit=850587 ccd=21 --configfile config/anetAstrometryConfig.py --clobber-config --output tempout
    ```

* Run the validation test
    ```
    validateCfht.py CFHT/output
    ```

Note that the example validation test selects several of the CCDs and will fail if you just pass it a repository with 1 visit or just 1 CCD.

Files of Interest:
------------------
* `examples/runCfhtTest.sh`  : CFHT Run initialization, ingest, measurement, and astrometry validation.
* `examples/runDecamTest.sh` : DECam Run initialization, ingest, measurement, and astrometry validation.
* `examples/validateCfht.py`    : CFHT run some analysis on the output data produced by processCcd.py
* `examples/validateDecam.py`   : DECam run some analysis on the output data produced by processCcd.py
* `examples/runCfht.list`    : CRHT list of vistits / ccd to be processed by processCcd
* `examples/runDecam.list`   : DECam list of vistits / ccd to be processed by processCcd
* `config/newAstrometryConfig.py`  : configuration for running processCcd with the new AstrometryTask
* `config/anetAstrometryConfig.py` : configuration for running processCcd ANetAstrometryTask
* `bin.src/validateCfht.py` : Wrapper script to analyze CFHT data in validation_data_cfht
* `bin.src/validateDecam.py` : Wrapper script to analyze DECam data in validation_data_decam
* `bin.src/validateDecamCosmos.py` : Wrapper script to analyze larger set of DECam data taken in the COSMOS field.
* `bin.src/validateCfht.py` : Wrapper script to analyze CFHT data in validation_data_cfht
* `python/lsst/validate/drp/calcSrd.py` : calculate metrics defined by the LSST SRC.
* `python/lsst/validate/drp/plotAstrometryPhotometry.py` : plotting routines
* `python/lsst/validate/drp/checkAstrometryPhotometry.py` : coordination and calculation routines.
* `README.md` : THIS FILE.  Guide and examples.
