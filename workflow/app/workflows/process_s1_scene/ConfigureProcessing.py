import luigi
import os
import errno
import json
import logging
import process_s1_scene.common as wc
import distutils.dir_util as distutils
from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.CutDEM import CutDEM

log = logging.getLogger('luigi-interface')

@requires(CutDEM)
class ConfigureProcessing(luigi.Task):
    paths = luigi.DictParameter()

    def run(self):
        cutDemInfo = {}
        with self.input().open('r') as cutDEM:
            cutDEMinfo = json.load(cutDEM)

        tempOutputPath = wc.createWorkingnewPath(self.paths["working"], "output")

        log.info('Populating configfile params')

        cofigFilePath = "/app/toolchain/scripts/JNCC_S1_GRD_configfile_v.1.1.sh"

        configuration = {
                "scriptConfigFilePath" : configFilePath,
                "parameters" : {
                    "s1_ard_main_dir" : self.paths['workingDir'],
                    "s1_ard_basket_dir" : self.paths["input"],
                    "s1_ard_ext_dem" : cutDEMInfo["cutDemPath"],
                    "s1_ard_temp_output_dir" : tempOutputPath
                }
            }

        with open(cofigFilePath, 'rw') as configFile:
            contents = configFile.read()
        
            contents = contents.replace("{{ s1_ard_main_dir }}", cofiguration["parameters"]["s1_ard_main_dir"]),
            contents = contents.replace("{{ s1_ard_basket_dir }}", cofiguration["parameters"]["s1_ard_basket_dir"]),
            contents = contents.replace("{{ s1_ard_ext_dem }}", cofiguration["parameters"]["s1_ard_ext_dem"]),
            contents = contents.replace("{{ s1_ard_temp_output_dir }}", cofiguration["parameters"]["s1_ard_temp_output_dir"])

            configFile.write(contents)

        with self.output().open("w") as outFile:
            outFile.write(json.dumps(configuration))
                
    def output(self):
        outputFolder = os.path.join(self.paths["state"], 'SetupScripts.json')
        return LocalTarget(outFile)