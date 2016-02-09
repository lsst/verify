#!/bin/bash

print_error() {
    >&2 echo "$@"
}

PRODUCT_DIR=${VALIDATE_DRP_DIR}
# OS X El Capitan SIP swallows DYLD_LIBRARY_PATH so export the duplicate in LSST_LIBRARY_PATH
if [[ -z "$DYLD_LIBRARY_PATH" ]]; then
    export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH
fi

CAMERA=CfhtQuick
CONFIG_FILE="${PRODUCT_DIR}"/config/anetAstrometryConfig.py
MAPPER=lsst.obs.cfht.MegacamMapper

"${PRODUCT_DIR}"/examples/runExample.sh $CAMERA $MAPPER ${VALIDATION_DATA_CFHT_DIR}/raw "${CONFIG_FILE}"
