import luigi
import json
import os
import process_s1_scene.common as wc

from luigi import LocalTarget
from process_s1_scene.CheckFileExists import CheckFileExists
from process_s1_scene.EnforceZip import EnforceZip
from luigi.util import requires

@requires(EnforceZip)
class GetConfiguration(luigi.Task):
    paths = luigi.DictParameter()
    sourceSrs = luigi.Parameter()
    targetSrs = luigi.Parameter()
    finalSrsName = luigi.Parameter()
    metadataProjection = luigi.Parameter()
    #For state copy options in the docker container
    noStateCopy = luigi.BoolParameter()

    def run(self):
        enforceZipInfo = {}
        with self.input().open('r') as enforceZip:
            enforceZipInfo = json.load(enforceZip)

        inputFilePath = os.path.join(self.paths["input"], enforceZipInfo["zippedFileName"])

        check = CheckFileExists(inputFilePath)
        yield check

        productId = wc.getProductIdFromSourceFile(inputFilePath)
        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "inputFilePath" : inputFilePath,
                "productPattern" : wc.getProductPatternFromSourceFile(inputFilePath),
                "productId" : productId,
                "workingRoot" : os.path.join(self.paths['working'], productId),
                "noCopyState" : self.noStateCopy,
                "sourceSrs" : self.sourceSrs,
                "targetSrs" : self.targetSrs,
                "finalSrsName" : self.finalSrsName,
                "metadataProjection" : self.metadataProjection
            }))

    def output(self):
        outFile = os.path.join(self.paths['state'], 'GetConfiguration.json')
        return LocalTarget(outFile)