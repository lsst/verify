#!/bin/bash

print_error() {
    >&2 echo $@
}

# cleanup and create directories
echo "Ingesting Raw data"
if [ -d input ]; then
   rm -rf input
fi
mkdir input
if [ -d output ]; then
   rm -rf output
fi
echo "lsst.obs.cfht.MegacamMapper" > input/_mapper

# ingest CFHT raw data
RAWDATA=/lsst8/boutigny/valid_cfht
ingestImages.py input ${RAWDATA}/rawDownload/*.fz --mode link

# Create calexps and src
echo "running processCcd"
NUMPROC=`grep -c processor /proc/cpuinfo`
NUMPROC=$(($NUMPROC<4?$NUMPROC:4))
processCcd.py input --output output @run.list --configfile anetAstrometryConfig.py --clobber-config -j $NUMPROC

# Run astrometry check on src
echo "validating"
./valid_cfht.py output

if [ $? != 0 ]; then
   print_error "Validation failed"
   exit 99
fi


