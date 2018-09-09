import luigi
import os
import errno
import json
import logging
import process_s1_scene.common as wc
import distutils.dir_util as distutils
from luigi.util import requires
from process_s1_scene.CutDEM import CutDEM

log = logging.getLogger('luigi-interface')

@requires(CutDEM)
class SetupScripts(luigi.Task):
    sourceFile = luigi.Parameter()
    paths = luigi.DictParameter()
    productId = luigi.Parameter()
    testProcessing = luigi.BoolParameter()
    processToS3 = luigi.BoolParameter(default=False)

    def populateConfig(self):
        log.info('Populating configfile params')
        
        configFilePath = "/app/toolchain/scripts/JNCC_S1_GRD_configfile_v.1.1.sh")

        with open(configFilePath, 'r') as configFile:
            contents = configFile.read()
        
            contents = contents.replace("{{ s1_ard_main_dir }}", self.paths['workingDir'])
            contents = contents.replace("{{ s1_ard_basket_dir }}", os.path.join(self.paths["input"]))
            contents = contents.replace("{{ s1_ard_ext_dem }}", self.paths["cutDemPath"])

        with open(configFilePath, 'w') as configFile:
            configFile.write(contents)


    def run(self):
        self.copyScripts(scriptDir)
        self.populateConfig(scriptDir)

        with self.input().open('r') as inFile:
            cutDemOutput = json.load(inFile)
            with self.output().open("w") as outFile:
                outFile.write(json.dumps({
                    'inputFilePath': cutDemOutput['inputFilePath'], 
                    'cutDemPath' : self.paths["cutDemPath"],
                }))
                
    def output(self):
        if self.processToS3:
            outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
            return wc.getS3StateTarget(outputFolder, 'setupScripts.json')
        else:
            outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
            return wc.getLocalStateTarget(outputFolder, 'setupScripts.json')
