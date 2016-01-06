#!/bin/bash

print_error() {
    >&2 echo $@
}

# cleanup and create directories
echo "Ingesting Raw data"
INPUT=input
if [ -d $INPUT ]; then
   rm -rf $INPUT
fi
mkdir $INPUT
OUTPUT=output
if [ -d $OUTPUT ]; then
   rm -rf $OUTPUT
fi
mkdir $OUTPUT

echo "lsst.obs.cfht.MegacamMapper" > ${INPUT}/_mapper

# ingest CFHT raw data
RAWDATA=${VALIDATION_DATA_CFHT_DIR}
ingestImages.py input ${RAWDATA}/raw/*.fz --mode link

# Set up astrometry 
export ASTROMETRY_NET_DATA_DIR=${VALIDATION_DATA_CFHT_DIR}/astrometry_net_data

# Create calexps and src
echo "running processCcd"
MACH=`uname -s`
if [ $MACH == Darwin ]; then
    NUMPROC=`sysctl -a | grep machdep.cpu | grep core_count | cut -d ' ' -f 2`
    NUMPROC=$(($NUMPROC<4?$NUMPROC:4))
else
    NUMPROC=`grep -c processor /proc/cpuinfo`
    NUMPROC=$(($NUMPROC<4?$NUMPROC:4))
fi

processCcd.py input --output output @run.list --configfile anetAstrometryConfig.py --clobber-config -j $NUMPROC

# Run astrometry check on src
echo "validating"
./valid_cfht.py output

if [ $? != 0 ]; then
   print_error "Validation failed"
   exit 99
fi


