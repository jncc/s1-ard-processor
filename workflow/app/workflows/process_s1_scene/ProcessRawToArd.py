import luigi
import os
import errno
import json
import logging
import process_s1_scene.common as wc
import subprocess

from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.ConfigureProcessing import ConfigureProcessing
from process_s1_scene.CutDEM import CutDEM
from process_s1_scene.GetConfiguration import GetConfiguration
from process_s1_scene.CheckFileExists import CheckFileExists
from process_s1_scene.CreateLocalFile import CreateLocalFile

log = logging.getLogger('luigi-interface')

@requires(CutDEM, GetConfiguration, ConfigureProcessing)
class ProcessRawToArd(luigi.Task):
    paths = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()

    def getExpectedOutput(self, productPattern, outputRoot): 
        vv_path = os.path.join(os.path.join(outputRoot, productPattern), "VV/GEO")
        vh_path = os.path.join(os.path.join(outputRoot, productPattern), "VH/GEO")

        # Write locations to S3 target
        expectedOutput = {
            'files': {
                'VV': [
                    os.path.join(vv_path, '{}_VV_Gamma0_APGB_UTMWGS84_FTC_SpkRL_dB.tif'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Gamma0_APGB_UTMWGS84_FTC_SpkRL.tif'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Gamma0_APGB_UTMWGS84_FTC.tif'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Gamma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Gamma0_APGB_UTMWGS84_RTC_SpkRL.tif'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Gamma0_APGB_UTMWGS84_RTC.tif'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Gamma0_APGB_UTMWGS84_TC.tif'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Sigma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Sigma0_APGB_UTMWGS84_RTC_SpkRL.tif'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Sigma0_APGB_UTMWGS84_RTC.tif'.format(productPattern)),
                    os.path.join(vv_path, '{}_VV_Sigma0_APGB_UTMWGS84_TC.tif'.format(productPattern))
                ],
                'VH': [
                    os.path.join(vh_path, '{}_VH_Gamma0_APGB_UTMWGS84_FTC_SpkRL_dB.tif'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Gamma0_APGB_UTMWGS84_FTC_SpkRL.tif'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Gamma0_APGB_UTMWGS84_FTC.tif'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Gamma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Gamma0_APGB_UTMWGS84_RTC_SpkRL.tif'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Gamma0_APGB_UTMWGS84_RTC.tif'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Gamma0_APGB_UTMWGS84_TC.tif'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Sigma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Sigma0_APGB_UTMWGS84_RTC_SpkRL.tif'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Sigma0_APGB_UTMWGS84_RTC.tif'.format(productPattern)),
                    os.path.join(vh_path, '{}_VH_Sigma0_APGB_UTMWGS84_TC.tif'.format(productPattern))
                ]
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
            "SNAP_OPTS" : "-J-Xmx{0}G -J-Xms4G -J-XX:-UseGCOverheadLimit".format(parameters["s1_ard_snap_memory"])
        }

        return subprocess.run("sh {0} {1}".format(script, arguments), env=env, shell=runAsShell).returncode        

    def createTestFiles(expectedFiles):
        tasks = []
        for filePath in expectedFiles:
            tasks.append(CreateLocalFile(filePath = filePath, content='Test File'))

        yield tasks
            
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
            retcode = self.runShellScript('JNCC_S1_GRD_MAIN_v2.1.1.sh', '1 1 1 1 1 1 2 1 3 1', configureProcessingInfo["parameters"])
        else:
            expectedFiles = expectedOutput["files"]["VV"] + expectedOutput["files"]["VH"]
            self.createTestFiles(expectedFiles)

        if retcode != 0:
            raise "Return code from snap process not 0, code was: {0}".format(retcode)

        with self.output().open('w') as out:
            out.write(json.dumps(expectedOutput))
                
    def output(self):
        outputFile = os.path.join(self.paths["state"], 'ProcessRawToArd.json')
        return LocalTarget(outputFile)
