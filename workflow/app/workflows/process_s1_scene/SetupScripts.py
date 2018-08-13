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
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter()
    testProcessing = luigi.BoolParameter()
    processToS3 = luigi.BoolParameter(default=False)

    def copyScripts(self, filepath):
        log.info('Copying scripts: %s', filepath)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        distutils.copy_tree(self.pathRoots["scriptRoot"], filepath)


    def populateConfig(self, scriptDir):
        log.info('Populating configfile params')
        
        configFilePath = os.path.join(scriptDir, "JNCC_S1_GRD_configfile_v.1.1.sh")

        with open(configFilePath, 'r') as configFile:
            contents = configFile.read()
        
        contents = contents.replace("{{ s1_ard_main_dir }}", self.pathRoots["fileRoot"])
        contents = contents.replace("{{ s1_ard_basket_dir }}", os.path.join(self.pathRoots["fileRoot"], 'raw'))
        contents = contents.replace("{{ s1_ard_ext_dem }}", os.path.join(self.pathRoots["fileRoot"], 'dem/cut_dem.tif'))
        contents = contents.replace("{{ s1_ard_script_dir }}", scriptDir)
        contents = contents.replace("{{ snap_bin_path }}", self.pathRoots["snapPath"])

        with open(configFilePath, 'w') as configFile:
            configFile.write(contents)


    def run(self):
        scriptDir = os.path.join(self.pathRoots["fileRoot"], "scripts")
        self.copyScripts(scriptDir)
        self.populateConfig(scriptDir)

        with self.input().open('r') as inFile:
            downloadedOutput = json.load(inFile)
            with self.output().open("w") as outFile:
                outFile.write(json.dumps({
                    'sourceFile': downloadedOutput["sourceFile"],
                    'productId': downloadedOutput["productId"],
                    'productPattern': downloadedOutput["productPattern"],
                    'cutDEM': os.path.join(self.pathRoots["fileRoot"], "dem/cut_dem.tif"),
                    'tempFile': downloadedOutput["tempFile"]
                }))
                
    def output(self):
        if self.processToS3:
            outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
            return wc.getS3StateTarget(outputFolder, 'setupScripts.json')
        else:
            outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
            return wc.getLocalStateTarget(outputFolder, 'setupScripts.json')
