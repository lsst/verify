#!/bin/bash

PRODUCT_DIR=${VALIDATE_DRP_DIR}

CAMERA=DecamQuick
CONFIG_FILE="${PRODUCT_DIR}"/config/decamConfig.py
MAPPER=lsst.obs.decam.DecamMapper

"${PRODUCT_DIR}"/examples/runExample.sh $CAMERA $MAPPER \
    ${VALIDATION_DATA_DECAM_DIR}/instcal "${CONFIG_FILE}" \
    ingestImagesDecam.py processCcdDecam.py
