import luigi
import json
import os
import process_s1_scene.common as wc

from luigi import LocalTarget
from process_s1_scene.CheckFileExists import CheckFileExists

class GetConfiguration(luigi.Task):
    paths = luigi.DictParameter()
    inputFileName = luigi.Parameter()
    #For state copy options in the docker container
    noStateCopy = luigi.BoolParameter()

    def run(self):
        inputFilePath = os.path.join(self.paths["input"], self.inputFileName)

        check = CheckFileExists(inputFilePath)
        yield check

        productId = wc.getProductIdFromSourceFile(self.inputFileName)
        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "inputFilePath" : inputFilePath,
                "productPattern" : wc.getProductPatternFromSourceFile(self.inputFileName),
                "productId" : productId,
                "workingRoot" : os.path.join(self.paths['working'], productId),
                "noCopyState" : self.noStateCopy
            }))

    def output(self):
        outFile = os.path.join(self.paths['state'], 'GetConfiguration.json')
        return LocalTarget(outFile)