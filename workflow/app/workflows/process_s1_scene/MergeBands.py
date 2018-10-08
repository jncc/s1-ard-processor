import luigi
import json
import re
import logging
import os
import process_s1_scene.common as wc
import luigi
import subprocess
from luigi import LocalTarget
from luigi.util import requires
from functional import seq
from process_s1_scene.ReprojectToOSGB import ReprojectToOSGB
from process_s1_scene.ConfigureProcessing import ConfigureProcessing
from process_s1_scene.CheckArdFilesExist import CheckFileExists

log = logging.getLogger('luigi-interface')

@requires(ReprojectToOSGB, ConfigureProcessing)
class MergeBands(luigi.Task):
    paths = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()
    productId = luigi.Parameter()

    def run(self):
        reprojectToOSGBInfo = {}
        with self.input()[0].open('r') as reprojectToOSGB:
            reprojectToOSGBInfo = json.load(reprojectToOSGB)

        configureProcessingInfo = {}
        with self.input()[1].open('r') as configureProcessing:
            configureProcessingInfo = json.load(configureProcessing) 
        
        checkTasks = []
        for sourceFile in reprojectToOSGBInfo["reprojectedFiles"]:
            checkTasks.append(CheckFileExists(filePath=sourceFile))

        yield checkTasks
        
        srcFiles = seq(reprojectToOSGBInfo["reprojectedFiles"]).reduce(lambda x, f: x + ' ' + f)

        log.debug('merging files %s', srcFiles)

        outputFile = os.path.join(configureProcessingInfo["parameters"]["s1_ard_temp_output_dir"], "{}_APGB_OSGB1936_RTC_SpkRL_dB.tif".format(self.productId))

        cmdString = 'gdalbuildvrt -separate /vsistdout/ {}|gdal_translate -a_nodata nan -co BIGTIFF=YES -co TILED=YES -co COMPRESS=LZW --config CHECK_DISK_FREE_SPACE no /vsistdin/ {}' \
            .format(srcFiles, outputFile) 

        if not self.testProcessing:
            log.info('Creating merged product from Gamma VH & VV bands')
            try:
                subprocess.check_output(cmdString, shell=True) 
            except subprocess.CalledProcessError as e:
                errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                log.error(errStr)
                raise RuntimeError(errStr)
        else:
            wc.createTestFile(outputFile)
        
        with self.output().open('w') as out:
            out.write(json.dumps({
                "mergedOutputFile" : outputFile
            }))

    def output(self):
        outputFile = os.path.join(self.paths["state"], "MergeBands.json")
        return LocalTarget(outputFile)
