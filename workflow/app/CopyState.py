import logging
import os
import sys
import json
import shutil
from functional import seq
from shutil import copy

# Coppies the luigi state files to an output folder - requires default configuration of file paths

log = logging.getLogger('CopyState')
log.setLevel(logging.INFO)

defaultStateFolder = "/state"
configFile = "/state/GetConfiguration.json"

if not os.listdir(defaultStateFolder):
    log.warning("No luigi state files detected in default /state folder")
    sys.exit()

if not (os.path.exists(configFile) and os.path.isfile(configFile)):
    log.warning("Workflow GetConfiguration has not run")
    sys.exit()

configuration = {}
with open(configFile, 'r') as getConfiguration:
    configuration = json.load(getConfiguration)

if configuration["noCopyState"]:
    log.warning("noCopySate flag set")
    sys.exit()
    
targetStatePath = os.path.join("/output", "state", configuration["productId"])

if os.path.exists(targetStatePath):
    log.info("Removing state path {} from output folder".format(targetStatePath))
    shutil.rmtree(targetStatePath)

os.makedirs(targetStatePath)

for stateFile in os.listdir(defaultStateFolder):
    source = os.path.join(defaultStateFolder, stateFile)
    target = os.path.join(targetStatePath, os.path.basename(stateFile))
    copy(source, target)
    log.info("coppied %s to %s", stateFile, target)










