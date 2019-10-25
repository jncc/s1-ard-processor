import luigi
import os
import re
import json
import logging
import process_s1_scene.common as wc
import subprocess
import distutils.dir_util as distutils
from luigi import LocalTarget
from luigi.util import requires
from functional import seq
from process_s1_scene.ProcessRawToArd import ProcessRawToArd 
from process_s1_scene.GetManifest import GetManifest
from process_s1_scene.GetConfiguration import GetConfiguration
from process_s1_scene.CheckArdFilesExist import CheckArdFilesExist 
from process_s1_scene.CheckFileExists import CheckFileExists
from process_s1_scene.ConfigureProcessing import ConfigureProcessing
from os.path import join as joinPath

log = logging.getLogger('luigi-interface')

@requires(ProcessRawToArd, 
    GetManifest, 
    GetConfiguration,
    ConfigureProcessing, 
    CheckArdFilesExist)
class ReprojectToOSGB(luigi.Task):
    paths = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()

    reprojectionFilePattern = "^[\w\/-]+_Gamma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif"

    def reprojectPolorisation(self, polarisation, sourceFile, state, manifest, configuration, inputFileName, outputRoot):
        outputPath = joinPath(outputRoot, polarisation)

        if not os.path.exists(outputPath):
            os.makedirs(outputPath)

        outputFile = joinPath(outputPath, wc.getOutputFileName(inputFileName, polarisation, manifest, configuration["finalSrsName"]))

        if not self.testProcessing:
            try:
                env = {
                    "GDAL_DATA" : "/usr/share/gdal/2.2"
                }

                subprocess.run("gdalwarp -overwrite -s_srs {} -t_srs {} -r bilinear -dstnodata 0 -of GTiff -tr 10 10 --config CHECK_DISK_FREE_SPACE NO {} {}"
                    .format(configuration["sourceSrs"], configuration["targetSrs"], sourceFile, outputFile),
                    env=env, 
                    check=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    shell=True).stdout
                
            except subprocess.CalledProcessError as e:
                errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                log.error(errStr)
                raise RuntimeError(errStr)
        else:
            wc.createTestFile(outputFile)
        
        state["reprojectedFiles"][polarisation].append(outputFile)


    def run(self):
        processRawToArdInfo = {}
        with self.input()[0].open('r') as processRawToArd:
            processRawToArdInfo = json.load(processRawToArd)

        getManifestInfo = {}
        with self.input()[1].open('r') as getManifest:
            getManifestInfo = json.load(getManifest)

        configuration = {}
        with self.input()[2].open('r') as getConfiguration:
            configuration = json.load(getConfiguration)

        configureProcessingInfo = {}
        with self.input()[3].open('r') as configureProcessing:
            configureProcessingInfo = json.load(configureProcessing) 

        manifestLoader = CheckFileExists(filePath=getManifestInfo["manifestFile"])
        yield manifestLoader

        manifest = ''
        with manifestLoader.output().open('r') as manifestFile:
            manifest = manifestFile.read()

        p = re.compile(self.reprojectionFilePattern)

        state = {
            "reprojectedFiles": {
                "VV" : [],
                "VH" : []
            }
        }

        polarisations = ["VV","VH"]

        inputFileName = os.path.basename(configuration["inputFilePath"])

        outputRoot = configureProcessingInfo["parameters"]["s1_ard_temp_output_dir"]

        for polarisation in polarisations:
            src = (seq(processRawToArdInfo['files'][polarisation])
                .filter(lambda f: p.match(f))
                .first())

            if src == '':
                errorMsg = "Found no {0} polarisation files to reproject".format(polarisation)
                log.error(errorMsg)
                raise RuntimeError(errorMsg)
        
            self.reprojectPolorisation(polarisation, src, state, manifest, configuration, inputFileName, outputRoot)

        with self.output().open("w") as outFile:
            outFile.write(json.dumps(state))
                
    def output(self):
        outputFile = os.path.join(self.paths["state"], 'ReprojectToOSGB.json')
        return LocalTarget(outputFile)
