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
from process_s1_scene.GetInputFileInfo import GetInputFileInfo

log = logging.getLogger('luigi-interface')

@requires(CutDEM, CopyInputFile, GetInputFileInfo)
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

        inputFileInfo = {}
        with self.input()[2].open('r') as getInputFileInfo:
            inputFileInfo = json.load(getInputFileInfo)

        tempOutputPath = wc.createWorkingPath(inputFileInfo["workingRoot"], "output")

        log.info('Populating configfile params')

# todo these two options are probabably no longer needed and can be removed after code checks
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
                    "s1_ard_snap_memory" : str(self.memoryLimit)
                }
            }

        if not os.path.isdir(configuration["parameters"]["s1_ard_main_dir"]):
            raise Exception("Invalid working path: Check working path in paths parameter")

        with self.output().open("w") as outFile:
            outFile.write(json.dumps(configuration))
                
    def output(self):
        outFile = os.path.join(self.paths["state"], 'ConfigureProcessing.json')
        return LocalTarget(outFile)