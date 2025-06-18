import luigi
import os
import json
import logging
import process_s1_scene.common as wc
import subprocess
import glob

from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.ConfigureProcessing import ConfigureProcessing
from process_s1_scene.CutDEM import CutDEM
from process_s1_scene.GetConfiguration import GetConfiguration
from process_s1_scene.CheckFileExists import CheckFileExists

log = logging.getLogger('luigi-interface')

@requires(CutDEM, GetConfiguration, ConfigureProcessing)
class ProcessRawToArd(luigi.Task):
    paths = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()

    def checkFileExistsWithPattern(self, filePattern):
        matchingFiles = glob.glob(filePattern)

        if len(matchingFiles) < 1:
            raise Exception("Something went wrong, did not find any matching files for pattern {}".format(filePattern))
        elif len(matchingFiles) > 1:
            raise Exception("Something went wrong, found more than one file for pattern {}".format(filePattern))
        elif not os.path.isfile(matchingFiles[0]):
            raise Exception("Something went wrong, {} is not a file".format(matchingFiles[0]))
        elif not os.path.getsize(matchingFiles[0]) > 0:
            log.error("ARD processing error, file size is 0 for {} ".format(matchingFiles[0]))
            raise Exception("Something went wrong, file size is 0 for {}".format(matchingFiles[0]))

        return matchingFiles[0]

    def getExpectedOutput(self, productPattern, outputRoot):
        vv_path = os.path.join(os.path.join(outputRoot, productPattern), "VV/GEO")
        vh_path = os.path.join(os.path.join(outputRoot, productPattern), "VH/GEO")
        log_path = os.path.join(os.path.join(outputRoot, productPattern), "log_{}_PROCESSING_*.txt".format(productPattern))

        expectedOutput = {
            'files': {
                'VV': [
                    os.path.join(vv_path, '{}_VV_Gamma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Gamma0_APGB_UTMWGS84_RTC_SpkRL.dim'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Gamma0_APGB_UTMWGS84_RTC.dim'.format(productPattern)),
                    # os.path.join(vv_path, '{}_VV_Gamma0_APGB_UTMWGS84_TC.tif'.format(productPattern)),
                    # os.path.join(vv_path, '{}_VV_Sigma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif'.format(productPattern)),
                    # os.path.join(vv_path, '{}_VV_Sigma0_APGB_UTMWGS84_RTC_SpkRL.tif'.format(productPattern)),
                    # os.path.join(vv_path, '{}_VV_Sigma0_APGB_UTMWGS84_RTC.tif'.format(productPattern)),
                    # os.path.join(vv_path, '{}_VV_Sigma0_APGB_UTMWGS84_TC.tif'.format(productPattern))
                ],
                'VH': [
                    os.path.join(vh_path, '{}_VH_Gamma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Gamma0_APGB_UTMWGS84_RTC_SpkRL.dim'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Gamma0_APGB_UTMWGS84_RTC.dim'.format(productPattern)),
                    # os.path.join(vh_path, '{}_VH_Gamma0_APGB_UTMWGS84_TC.tif'.format(productPattern)),
                    # os.path.join(vh_path, '{}_VH_Sigma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif'.format(productPattern)),
                    # os.path.join(vh_path, '{}_VH_Sigma0_APGB_UTMWGS84_RTC_SpkRL.tif'.format(productPattern)),
                    # os.path.join(vh_path, '{}_VH_Sigma0_APGB_UTMWGS84_RTC.tif'.format(productPattern)),
                    # os.path.join(vh_path, '{}_VH_Sigma0_APGB_UTMWGS84_TC.tif'.format(productPattern))
                ],
                'log': log_path
            }
        }

        return expectedOutput

    def runShellScript(self, script, arguments, parameters, runAsShell=True):
        os.chdir(self.paths["scripts"])
        env = {
            "MAIN_DIR" : parameters["s1_ard_main_dir"],
            "BASKET_INDIR" : parameters["s1_ard_basket_dir"],
            "EXTDEMFILE" : parameters["s1_ard_ext_dem"],
            "MAIN_OUTDIR" : parameters["s1_ard_temp_output_dir"],
            "SNAP_OPTS" : "-J-Xmx{0}G -J-Xms4G -J-XX:-UseGCOverheadLimit".format(parameters["s1_ard_snap_memory"]),
            "UTMPROJ" : parameters["s1_ard_utm_proj"],
            "centralmeridian" : parameters["s1_ard_central_meridian"],
            "false_northing" : parameters["s1_ard_false_northing"]
        }

        return subprocess.run("sh {0} {1}".format(script, arguments), env=env, shell=runAsShell, check=True).returncode        

    def createTestFiles(self, expectedFiles):
        for filePath in expectedFiles:
            wc.createTestFile(filePath)
            
    def run(self):
        # copy input file to temp.
        cutDEMInfo = {}      
        with self.input()[0].open('r') as cutDEM:
            cutDEMInfo = json.load(cutDEM)

        dem = cutDEMInfo["cutDemPath"]
        yield CheckFileExists(filePath=dem)
        
        configuration = {}
        with self.input()[1].open('r') as getConfiguration:
            configuration = json.load(getConfiguration)

        configureProcessingInfo = {}
        with self.input()[2].open('r') as configureProcessing:
            configureProcessingInfo = json.load(configureProcessing)
       
        outputRoot = configureProcessingInfo["parameters"]["s1_ard_temp_output_dir"]
        productPattern = configuration["productPattern"]

        expectedOutput = self.getExpectedOutput(productPattern, outputRoot)
        
        # Runs shell process to create the ard products
        retcode = 0
        if not self.testProcessing:
            retcode = self.runShellScript('JNCC_S1_GRD_MAIN_v2.1.1.sh', configureProcessingInfo["arguments"], configureProcessingInfo["parameters"])
        else:
            expectedFiles = expectedOutput["files"]["VV"] + expectedOutput["files"]["VH"]
            expectedFiles.append(expectedOutput["files"]["log"])
            self.createTestFiles(expectedFiles)

        snapLogPath = self.checkFileExistsWithPattern(expectedOutput["files"]["log"])
    
        log.info("Contents of SNAP log {}".format(snapLogPath))
        with open(snapLogPath) as f:
            for line in f.readlines():
                log.info(line)

        if retcode != 0:
            raise "Return code from snap process not 0, code was: {0}".format(retcode)

        with self.output().open('w') as out:
            out.write(json.dumps(expectedOutput, indent=4))
                
    def output(self):
        outputFile = os.path.join(self.paths["state"], 'ProcessRawToArd.json')
        return LocalTarget(outputFile)
