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
    #For state copy options in the docker container
    noStateCopy = luigi.BoolParameter()

    def getOutputPathFromProductId(self, root, productId):
        year = productId[4:8]
        month = productId[8:10]
        day = productId[10:12]

        return os.path.join(os.path.join(os.path.join(os.path.join(root, year), month), day), productId)

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
                "outputPath" : self.getOutputPathFromProductId(self.paths['output'], productId),
                "sourceSrs" : self.sourceSrs,
                "targetSrs" : self.targetSrs,
                "finalSrsName" : self.finalSrsName
            }))

    def output(self):
        outFile = os.path.join(self.paths['state'], 'GetConfiguration.json')
        return LocalTarget(outFile)