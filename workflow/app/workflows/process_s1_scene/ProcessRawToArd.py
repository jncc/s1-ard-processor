import luigi
import os
import errno
import json
import logging
import process_s1_scene.common as wc
import subprocess

from luigi import LocalTarget
from luigi.util import inherits
from process_s1_scene.ConfigureProcessing import ConfigureProcessing
from process_s1_scene.CutDEM import CutDEM
from process_s1_scene.GetInputFileInfo import GetIntputFileInfo
from process_s1_scene.CheckFileExists import CheckFileExists
from process_s1_scene.CreateLocalFile import CreateLocalFile

log = logging.getLogger('luigi-interface')

@inherits(CutDEM)
@inherits(GetIntputFileInfo)
@inherits(ConfigureProcessing)
class ProcessRawToArd(luigi.Task):
    paths = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()

    def requires(self):
        t = []
        t.append(self.clone(CutDEM))
        t.append(self.clone(GetIntputFileInfo))
        t.append(self.clone(ConfigureProcessing))
        return t

    def getExpectedOutput(self, productPattern, outputRoot): 
        vv_path = os.path.join(os.path.join(outputRoot, productPattern), "VV/GEO")
        vh_path = os.path.join(os.path.join(outputRoot, productPattern), "VH/GEO")

        # Write locations to S3 target
        expectedOutput = {
            'files': {
                'VV': [
                    os.path.join(vv_path, '%s_VV_Gamma0_APGB_UTMWGS84_FTC_SpkRL_dB.tif' % productPattern),
                    os.path.join(vv_path, '%s_VV_Gamma0_APGB_UTMWGS84_FTC_SpkRL.tif' % productPattern),
                    os.path.join(vv_path, '%s_VV_Gamma0_APGB_UTMWGS84_FTC.tif' % productPattern),
                    os.path.join(vv_path, '%s_VV_Gamma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif' % productPattern),
                    os.path.join(vv_path, '%s_VV_Gamma0_APGB_UTMWGS84_RTC_SpkRL.tif' % productPattern),
                    os.path.join(vv_path, '%s_VV_Gamma0_APGB_UTMWGS84_RTC.tif' % productPattern),
                    os.path.join(vv_path, '%s_VV_Gamma0_APGB_UTMWGS84_TC.tif' % productPattern),
                    os.path.join(vv_path, '%s_VV_Sigma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif' % productPattern),
                    os.path.join(vv_path, '%s_VV_Sigma0_APGB_UTMWGS84_RTC_SpkRL.tif' % productPattern),
                    os.path.join(vv_path, '%s_VV_Sigma0_APGB_UTMWGS84_RTC.tif' % productPattern),
                    os.path.join(vv_path, '%s_VV_Sigma0_APGB_UTMWGS84_TC.tif' % productPattern)
                ],
                'VH': [
                    os.path.join(vh_path, '%s_VH_Gamma0_APGB_UTMWGS84_FTC_SpkRL_dB.tif' % productPattern),
                    os.path.join(vh_path, '%s_VH_Gamma0_APGB_UTMWGS84_FTC_SpkRL.tif' % productPattern),
                    os.path.join(vh_path, '%s_VH_Gamma0_APGB_UTMWGS84_FTC.tif' % productPattern),
                    os.path.join(vh_path, '%s_VH_Gamma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif' % productPattern),
                    os.path.join(vh_path, '%s_VH_Gamma0_APGB_UTMWGS84_RTC_SpkRL.tif' % productPattern),
                    os.path.join(vh_path, '%s_VH_Gamma0_APGB_UTMWGS84_RTC.tif' % productPattern),
                    os.path.join(vh_path, '%s_VH_Gamma0_APGB_UTMWGS84_TC.tif' % productPattern),
                    os.path.join(vh_path, '%s_VH_Sigma0_APGB_UTMWGS84_RTC_SpkRL_dB.tif' % productPattern),
                    os.path.join(vh_path, '%s_VH_Sigma0_APGB_UTMWGS84_RTC_SpkRL.tif' % productPattern),
                    os.path.join(vh_path, '%s_VH_Sigma0_APGB_UTMWGS84_RTC.tif' % productPattern),
                    os.path.join(vh_path, '%s_VH_Sigma0_APGB_UTMWGS84_TC.tif' % productPattern)
                ]
            }
        }

        return expectedOutput

    def runShellScript(self, script, arguments, runAsShell=True):
        os.chdir(os.path.join(self.paths["fileRoot"], 'scripts'))
        return subprocess.call("sh %s %s" % (script, arguments), shell=runAsShell)        

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
        t = CheckFileExists(filePath=dem)
        yield 
        
        inputFileInfo = {}
        with self.input()[1].open('r') as getInputFileInfo:
            inputFileInfo = json.load(getInputFileInfo)

        configureProcessingInfo = {}
        with self.input()[2].open('r') as configureProcessing:
            configureProcessingInfo = json.load(configureProcessing)
       
        outputRoot = configureProcessingInfo["parameters"]["s1_ard_temp_output_dir"]
        productPattern = inputFileInfo["productPattern"]

        expectedOutput = self.getExpectedOutput(productPattern, outputRoot)
        
        # Runs shell process to create the ard products
        retcode = 0
        if not self.testProcessing:
            retcode = self.runShellScript('JNCC_S1_GRD_MAIN_v2.1.1.sh', '1 1 1 1 1 1 2 1 3 1')
        else:
            expectedFiles = expectedOutput["files"]["VV"] + expectedOutput["files"]["VH"]
            self.createTestFiles(expectedFiles)
        
        # If process has OK return code then check outputs exist
        if retcode != 0:
            log.warning("Return code from snap process not 0, code was: %d", retcode)

        with self.output().open('w') as out:
            out.write(json.dumps(expectedOutput))
                
    def output(self):
        outputFile = os.path.join(self.paths["state"], 'processRawToArd.json')
        return LocalTarget(outputFile)
