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
            cutDemInfo = json.load(cutDEM)

        tempOutputPath = wc.createWorkingnewPath(self.paths["working"], "output")

        log.info('Populating configfile params')

        configFilePath = "/app/toolchain/scripts/JNCC_S1_GRD_configfile_v.1.1.sh"

        configuration = {
                "scriptConfigFilePath" : configFilePath,
                "parameters" : {
                    "s1_ard_main_dir" : self.paths['working'],
                    "s1_ard_basket_dir" : self.paths["input"],
                    "s1_ard_ext_dem" : cutDemInfo["cutDemPath"],
                    "s1_ard_temp_output_dir" : tempOutputPath
                }
            }
        
        configFileContents = ""

        with open(configFilePath, 'r') as configFile:
            configFileContents = configFile.read()
        
            configFileContents = configFileContents.replace("{{ s1_ard_main_dir }}", configuration["parameters"]["s1_ard_main_dir"])
            configFileContents = configFileContents.replace("{{ s1_ard_basket_dir }}", configuration["parameters"]["s1_ard_basket_dir"])
            configFileContents = configFileContents.replace("{{ s1_ard_ext_dem }}", configuration["parameters"]["s1_ard_ext_dem"])
            configFileContents = configFileContents.replace("{{ s1_ard_temp_output_dir }}", configuration["parameters"]["s1_ard_temp_output_dir"])


        with open(configFilePath, 'w') as configFile:
            configFile.write(configFileContents)

        with self.output().open("w") as outFile:
            outFile.write(json.dumps(configuration))
                
    def output(self):
        outFile = os.path.join(self.paths["state"], 'ConfigureProcessing.json')
        return LocalTarget(outFile)