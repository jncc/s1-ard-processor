import luigi
import os
import re
import errno
import json
import logging
import process_s1_scene.common as wc
import subprocess
import distutils.dir_util as distutils
from luigi import LocalTarget
from luigi.util import requires
from functional import seq
from process_s1_scene.ProcessRawToArd import ProcessRawToArd 
from process_s1_scene.CheckArdFilesExist import CheckArdFilesExist 

log = logging.getLogger('luigi-interface')

@requires(ProcessRawToArd, CheckArdFilesExist)
class ReprojectToOSGB(luigi.Task):
    paths = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()

    reprojectionFilePattern = "^[\w\/-]+_Gamma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif"

    def reprojectPolorisation(self, polarisation, sourceFiles, state):
        for sourceFile in sourceFiles:
            outputFile = self.changeFileName(sourceFile)
            if not self.testProcessing:
                try:
                    subprocess.check_output(
                        "gdalwarp -overwrite -s_srs EPSG:32630 -t_srs EPSG:27700 -r bilinear -dstnodata 0 -of GTiff -tr 10 10 --config CHECK_DISK_FREE_SPACE NO %s %s" % (sourceFile, outputFile), 
                        stderr=subprocess.STDOUT,
                        shell=True)
                    
                except subprocess.CalledProcessError as e:
                    errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                    log.error(errStr)
                    raise RuntimeError(errStr)
            else:
                wc.createTestFile(outputFile)
            
            state["reprojectedFiles"][polarisation].append(outputFile)

    
    def changeFileName(self, fileName):
        return fileName.replace("UTMWGS84", "OSGB1936")

    def run(self):
        with self.input()[0].open('r') as processRawToArd:
            processRawToArdInfo = json.load(processRawToArd)

        p = re.compile(self.reprojectionFilePattern)

        vvSource = (seq(processRawToArdInfo['files']['VV'])
            .filter(lambda f: p.match(f)))

        vhSource = (seq(processRawToArdInfo['files']['VV'])
            .filter(lambda f: p.match(f)))

        if vvSource.len() < 1:
            errorMsg = "Found no VV polarisation files to reproject"
            log.error(errorMsg)
            raise RuntimeError(errorMsg)

        if vhSource.len() < 1:
            errorMsg = "Found no VH polarisation files to reproject"
            log.error(errorMsg)
            raise RuntimeError(errorMsg)

        state = {
            "reprojectedFiles": {
                "VV" : [],
                "VH" : []
            }
        }
        
        self.reprojectPolorisation("VV", vvSource, state)
        self.reprojectPolorisation("VH", vvSource, state)

        with self.output().open("w") as outFile:
            outFile.write(json.dumps(state))
                
    def output(self):
        outputFile = os.path.join(self.paths["state"], 'ReprojectToOSGB.json')
        return LocalTarget(outputFile)
