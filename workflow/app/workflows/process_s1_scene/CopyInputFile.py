import luigi
import os
import shutil
import logging
import json
import process_s1_scene.common as wc

from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.GetConfiguration import GetConfiguration

log = logging.getLogger('luigi-interface')

@requires(GetConfiguration)
class CopyInputFile(luigi.Task):
    paths = luigi.DictParameter()

    def run(self):
        configuration = {}
        with self.input().open('r') as getConfiguration:
            configuration = json.load(getConfiguration)
        
        tempInputPath = wc.createWorkingPath(configuration["workingRoot"], "input")

        inputSource = configuration["inputFilePath"]
        tempTatget = os.path.join(tempInputPath, os.path.basename(inputSource))

        try:
            shutil.copy(inputSource, tempTatget)
            log.info("Coppied input file to {}".format(tempTatget))
        except IOError as e:
            raise("Unable to copy file. {}".format(e))
        except:
            raise("Unexpected error:", sys.exc_info())

        with self.output().open('w') as out:
            out.write(json.dumps({
                "tempInputPath" : tempInputPath,
                "tempInputFile" : tempTatget
            }))

    def output(self):
        outputFile = os.path.join(self.paths["state"], 'CopyInputFile.json')
        return LocalTarget(outputFile)
