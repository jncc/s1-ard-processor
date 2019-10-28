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
from process_s1_scene.ReprojectToTargetSrs import ReprojectToTargetSrs
from process_s1_scene.ConfigureProcessing import ConfigureProcessing
from process_s1_scene.CheckArdFilesExist import CheckFileExists
from process_s1_scene.GetConfiguration import GetConfiguration
from process_s1_scene.GetManifest import GetManifest

log = logging.getLogger('luigi-interface')

@requires(ReprojectToTargetSrs, ConfigureProcessing, GetConfiguration, GetManifest)
class MergeBands(luigi.Task):
    paths = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()

    def run(self):
        reprojectToTargetSrsInfo = {}
        with self.input()[0].open('r') as reprojectToTargetSrs:
            reprojectToTargetSrsInfo = json.load(reprojectToTargetSrs)

        configureProcessingInfo = {}
        with self.input()[1].open('r') as configureProcessing:
            configureProcessingInfo = json.load(configureProcessing) 

        configuration = {}
        with self.input()[2].open('r') as getConfiguration:
            configuration = json.load(getConfiguration)

        getManifestInfo = {}
        with self.input()[3].open('r') as getManifest:
            getManifestInfo = json.load(getManifest)

        sourceFiles = reprojectToTargetSrsInfo['reprojectedFiles']['VV'] + reprojectToTargetSrsInfo['reprojectedFiles']['VH']
        
        checkTasks = []
        for sourceFile in sourceFiles:
            checkTasks.append(CheckFileExists(filePath=sourceFile))

        yield checkTasks

        manifestLoader = CheckFileExists(filePath=getManifestInfo["manifestFile"])
        yield manifestLoader

        manifest = ''
        with manifestLoader.output().open('r') as manifestFile:
            manifest = manifestFile.read()
        
        srcFilesArg = seq(sourceFiles).reduce(lambda x, f: x + ' ' + f)

        log.debug('merging files %s', srcFilesArg)

        inputFileName = os.path.basename(configuration["inputFilePath"])
        outputFileName = wc.getOutputFileName(inputFileName, "VVVH", manifest, configuration["finalSrsName"])

        outputFile = os.path.join(configureProcessingInfo["parameters"]["s1_ard_temp_output_dir"], outputFileName)

        cmdString = 'gdalbuildvrt -separate /vsistdout/ {}|gdal_translate -a_nodata nan -co BIGTIFF=YES -co TILED=YES -co COMPRESS=LZW --config CHECK_DISK_FREE_SPACE no /vsistdin/ {}' \
            .format(srcFilesArg, outputFile) 

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
