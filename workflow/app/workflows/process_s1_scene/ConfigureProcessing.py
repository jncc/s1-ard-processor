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
from process_s1_scene.CopyInputFile import CopyInputFile

log = logging.getLogger('luigi-interface')

@requires(CutDEM, CopyInputFile)
class ConfigureProcessing(luigi.Task):
    paths = luigi.DictParameter()
    memoryLimit = luigi.IntParameter()

    def run(self):
        cutDemInfo = {}
        with self.input()[0].open('r') as cutDEM:
            cutDemInfo = json.load(cutDEM)

        copyInputFileInfo = {}
        with self.input()[1].open('r') as copyInputFile:
            copyInputFileInfo = json.load(copyInputFile)

        tempOutputPath = wc.createWorkingnewPath(self.paths["working"], "output")

        log.info('Populating configfile params')

        configFilePath = "/app/toolchain/scripts/JNCC_S1_GRD_configfile_v.1.1.sh"
        vmOptionsFilePath = "/app/snap/bin/gpt.vmoptions"

        configuration = {
                "scriptConfigFilePath" : configFilePath,
                "vmOptionsFilePath" : vmOptionsFilePath,
                "parameters" : {
                    "s1_ard_main_dir" : self.paths['working'],
                    "s1_ard_basket_dir" : copyInputFileInfo["tempInputPath"],
                    "s1_ard_ext_dem" : cutDemInfo["cutDemPath"],
                    "s1_ard_temp_output_dir" : tempOutputPath,
                    "s1_ard_snap_memory" : self.memoryLimit
                }
            }
        
        configFileContents = ""

        with open(configFilePath, 'r') as configFile:
            configFileContents = configFile.read()
        
            configFileContents = configFileContents.replace("{{ s1_ard_main_dir }}", configuration["parameters"]["s1_ard_main_dir"])
            configFileContents = configFileContents.replace("{{ s1_ard_basket_dir }}", configuration["parameters"]["s1_ard_basket_dir"])
            configFileContents = configFileContents.replace("{{ s1_ard_ext_dem }}", configuration["parameters"]["s1_ard_ext_dem"])
            configFileContents = configFileContents.replace("{{ s1_ard_temp_output_dir }}", configuration["parameters"]["s1_ard_temp_output_dir"])
            configFileContents = configFileContents.replace("{{ s1_ard_snap_memory }}", configuration["parameters"]["s1_ard_snap_memory"])

        with open(configFilePath, 'w') as configFile:
            configFile.write(configFileContents)

        vmOptionsFileContents = ""
        with open(vmOptionsFilePath, "r") as vmOptionsFile:
            vmOptionsFileContents = vmOptionsFile.read()

            vmOptionsFileContents = vmOptionsFileContents.replace("{{ s1_ard_snap_memory }}", configuration["parameters"]["s1_ard_snap_memory"])

        with open(vmOptionsFilePath, "w") as vmOptionsFile:
            vmOptionsFile.write(vmOptionsFileContents)

        with self.output().open("w") as outFile:
            outFile.write(json.dumps(configuration))
                
    def output(self):
        outFile = os.path.join(self.paths["state"], 'ConfigureProcessing.json')
        return LocalTarget(outFile)