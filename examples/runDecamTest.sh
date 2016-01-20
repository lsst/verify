#!/bin/bash

print_error() {
    >&2 echo "$@"
}

WORKSPACE=DECam
mkdir -p ${WORKSPACE}
if [ -d ${WORKSPACE} ]; then
   rm -rf ${WORKSPACE}
fi

# cleanup and create directories
echo "Ingesting Raw data"
INPUT=${WORKSPACE}/input
mkdir -p $INPUT
OUTPUT=${WORKSPACE}/output
mkdir -p $OUTPUT

echo "lsst.obs.decam.DecamMapper" > ${INPUT}/_mapper

RAWDATA=${VALIDATION_DATA_DECAM_DIR}
ingestImagesDecam.py ${INPUT} "${RAWDATA}/instcal/*.fz" --mode link

# Set up astrometry 
export ASTROMETRY_NET_DATA_DIR=${VALIDATION_DATA_DECAM_DIR}/astrometry_net_data

# Create calexps and src
echo "running processCcd"
MACH=$(uname -s)
if [ "$MACH" == Darwin ]; then
    NUMPROC=$(sysctl -a | grep machdep.cpu | grep core_count | cut -d ' ' -f 2)
else
    NUMPROC=$(grep -c processor /proc/cpuinfo)
fi
NUMPROC=$((NUMPROC<8?NUMPROC:8))

processCcdDecam.py ${INPUT} --output ${OUTPUT} @runDecam.list --configfile config/decamConfig.py --clobber-config -j $NUMPROC

# Run astrometry check on src
echo "validating"
./validateDecam.py ${OUTPUT}

if [ $? != 0 ]; then
   print_error "Validation failed"
   exit 99
fi


