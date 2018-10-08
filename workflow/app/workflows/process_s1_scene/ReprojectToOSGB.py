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

    def runReprojection(self):
        processRawToArdInfo = {}
        with self.input()[0].open('r') as processRawToArd:
            processRawToArdInfo = json.load(processRawToArd)

        p = re.compile(self.reprojectionFilePattern)

        sourceFiles = (seq(processRawToArdInfo['files']['VV'])
            .union(seq(processRawToArdInfo['files']['VH']))
            .filter(lambda f: p.match(f)))

        if sourceFiles.len() < 1:
            errorMsg = "Found no files to reproject"
            log.error(errorMsg)
            raise RuntimeError(errorMsg)
        
        outputFiles = []
        for sourceFile in sourceFiles:
            outputFile = self.changeFileName(sourceFile)
            if not self.testProcessing:
                try:
                    subprocess.check_output(
                        "gdalwarp -overwrite -s_srs EPSG:32630 -t_srs EPSG:27700 -r bilinear -dstnodata 0 -of GTiff -tr 10 10 --config CHECK_DISK_FREE_SPACE NO %s %s" % (sourceFile, outputFile), 
                        stderr=subprocess.STDOUT,
                        shell=True)
                    outputFiles.append(outputFile)
                    
                except subprocess.CalledProcessError as e:
                    errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                    log.error(errStr)
                    raise RuntimeError(errStr)
            else:
                wc.createTestFile(outputFile)
                outputFiles.append(outputFile)
        
        return outputFiles

    
    def changeFileName(self, fileName):
        return fileName.replace("UTMWGS84", "OSGB1936")

    def run(self):
        outputFiles = self.runReprojection()

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "reprojectedFiles": outputFiles
            }))
                
    def output(self):
        outputFile = os.path.join(self.paths["state"], 'reprojectToOSGB.json')
        return LocalTarget(outputFile)
