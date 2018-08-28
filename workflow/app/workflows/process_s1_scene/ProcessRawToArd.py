import luigi
import os
import errno
import json
import logging
import process_s1_scene.common as wc
import subprocess

from luigi.util import requires
from process_s1_scene.SetupScripts import SetupScripts
from process_s1_scene.InitialiseDataFolder import InitialiseDataFolder
from process_s1_scene.CheckFileExists import CheckFileExists
from process_s1_scene.CreateLocalFile import CreateLocalFile

log = logging.getLogger('luigi-interface')

@requires(SetupScripts)
class ProcessRawToArd(luigi.Task):
    sourceFile = luigi.Parameter()
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter()
    testProcessing = luigi.BoolParameter()
    processToS3 = luigi.BoolParameter(default=False)

    def getTaskOutput(self, productPattern):
        vv_path = os.path.join(os.path.join(os.path.join(os.path.join(self.pathRoots["fileRoot"], 'output'), productPattern), 'VV'), 'GEO')
        vh_path = os.path.join(os.path.join(os.path.join(os.path.join(self.pathRoots["fileRoot"], 'output'), productPattern), 'VH'), 'GEO')

        # Write locations to S3 target
        processedOutput = {
            'sourceFile': spec['sourceFile'],
            'productId': self.productId,
            'productPattern': spec['productPattern'],
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

    def runShellScript(self, script, arguments, runAsShell=True):
        os.chdir(os.path.join(self.pathRoots["fileRoot"], 'scripts'))
        return subprocess.call("sh %s %s" % (script, arguments), shell=runAsShell)        

    def createTestFiles(self, productPattern):
        fileList = getTaskOutput(productPattern)

        expectedFiles = processedOutput["files"]["VV"] + processedOutput["files"]["VH"] 

        tasks = []
        for file in expectedFiles:
            tasks.append(CreateLocalFile(filePath = file, content='Test File'))

        yield tasks
            

    def run(self):
        # copy input file to temp.
        spec = {}
        with self.input().open('r') as downloaded:
            spec = json.loads(downloaded.read())
            
        dem = spec['cutDEM']
        t = CheckFileExists(filePath=dem)
        yield t

        productPattern = spec['productPattern']
        
        # Runs shell process to create the ard products
        retcode = 0
        if not self.testProcessing:
            retcode = self.runShellScript('JNCC_S1_GRD_MAIN_v2.1.1.sh', '1 1 1 1 1 1 2 1 3 1')
        else:
            self.createTestFiles(productPattern)
        
        # If process has OK return code then check outputs exist
        if retcode != 0:
            log.warning("Return code from snap process not 0, code was: %d", retcode)

        with self.output().open('w') as out:
            out.write(json.dumps(self.getTaskOutput(productPattern)))
                
    def output(self):
        if self.processToS3:
            outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
            return wc.getS3StateTarget(outputFolder, 'processRawToArd.json')
        else:
            outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
            return wc.getLocalStateTarget(outputFolder, 'processRawToArd.json')
