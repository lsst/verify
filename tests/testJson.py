import numpy as np

import lsst.pipe.base as pipeBase
from lsst.validate.drp.io import saveAmxToJson

ps = pipeBase.Struct(foo=2, bar=[10, 20], hard=np.array([5,10]))
tmpfile = 'tmp.json'

saveAmxToJson(ps, tmpfile)

