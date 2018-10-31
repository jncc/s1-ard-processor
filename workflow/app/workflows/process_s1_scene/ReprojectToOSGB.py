import luigi
import os
import re
import errno
import json
import logging
import process_s1_scene.common as wc
import subprocess
import distutils.dir_util as distutils
import re
from luigi import LocalTarget
from luigi.util import requires
from functional import seq
from process_s1_scene.ProcessRawToArd import ProcessRawToArd 
from process_s1_scene.GetManifest import GetManifest
from process_s1_scene.GetInputFileInfo import GetInputFileInfo
from process_s1_scene.CheckArdFilesExist import CheckArdFilesExist 
from process_s1_scene.CheckFileExists import CheckFileExists

log = logging.getLogger('luigi-interface')

@requires(ProcessRawToArd, 
    GetManifest, 
    GetInputFileInfo, 
    CheckArdFilesExist)
class ReprojectToOSGB(luigi.Task):
    paths = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()

    reprojectionFilePattern = "^[\w\/-]+_Gamma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif"

    def getOutputFileName(inputFileName, polarisation, manifest):
        # sourceFile S1A_04Jan2018_062254_062319_VH_Gamma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif
        # inputFile S1A_IW_GRDH_1SDV_20180104T062254_20180104T062319_020001_02211F_A294.zip

        inputFileSegemnts = inputFileName.split('_')

        a = inputFileSegemnts[0]
        b = inputFileSegemnts[4].split('T')[0] #date part

        c = ''
        absOrbitNo = float(inputFileSegments[6])
        if a == "S1A":
            c = str((absOrbitNo - 73 % 175) + 1)
        elif a == "S1B":
            c = str((absOrbitNo - 27 % 175) + 1)
        else:
            msg = "Invalid input file name, should begin S1A or S1B not {0}".format(a)
            raise Exception(msg)

        pattern = "<s1:pass>(.+)<\/s1:pass>"
        orbitDirectionRaw = re.search(pattern, manifest).group(1)

        d = ''
        if orbitDirectionRaw == "ASCENDING":
            d = "asc"
        elif orbitDirectionRaw == "DESCENDING":
            d = "desc"
        else:
            msg = "Invalid orbit direction in manifest, must be ASCENDING or DESCENDING but is {0}".format(orbitDirectionRaw)
            raise Exception(msg)

        e = inputFileSegemnts[4].split('T')[1]
        f = inputFileSegemnts[5].split('T')[1]
        g = polarisation

        return "{0}_{1}_{2}_{3}_{4}_{5}_{6}_Gamma-0_GB_OSGB_RCTK_SpkRL".format(a,b,c,d,e,f,g)

    def reprojectPolorisation(self, polarisation, sourceFile, state, manifest, inputFileName):
        outputFile = self.changeFileName(inputFileName, polarisation, manifest)
        
        if not self.testProcessing:
            try:
                subprocess.check_output(
                    "gdalwarp -overwrite -s_srs EPSG:32630 -t_srs EPSG:27700 -r bilinear -dstnodata 0 -of GTiff -tr 10 10 --config CHECK_DISK_FREE_SPACE NO {} {}".format(sourceFile, outputFile), 
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
        processRawToArdInfo = {}
        with self.input()[0].open('r') as processRawToArd:
            processRawToArdInfo = json.load(processRawToArd)

        getManifestInfo = {}
        with self.input()[1].open('r') as getManifest:
            getManifestInfo = json.load(getManifest)

        inputFileInfo = {}
        with self.input()[2].open('r') as getInputFileInfo:
            inputFileInfo = json.load(getInputFileInfo)

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

        inputFileName = os.path.basename(inputFileInfo["inputFilePath"])

        for polarisation in polarisations:
            src = (seq(processRawToArdInfo['files'][polarisation])
                .filter(lambda f: p.match(f))
                .first())

            if src.len() < 1:
                errorMsg = "Found no {0} polarisation files to reproject".format(polarisation)
                log.error(errorMsg)
                raise RuntimeError(errorMsg)
        
            self.reprojectPolorisation(polarisation, src, state, manifest, inputFileName)

        with self.output().open("w") as outFile:
            outFile.write(json.dumps(state))
                
    def output(self):
        outputFile = os.path.join(self.paths["state"], 'ReprojectToOSGB.json')
        return LocalTarget(outputFile)
