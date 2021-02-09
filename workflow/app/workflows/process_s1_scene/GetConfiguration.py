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
    spatialConfig = luigi.DictParameter()
    #For state copy options in the docker container
    noStateCopy = luigi.BoolParameter()

    def run(self):
        enforceZipInfo = {}
        with self.input().open('r') as enforceZip:
            enforceZipInfo = json.load(enforceZip)

        basketProductPath = enforceZipInfo["basketProductPath"]
        inputFilePath = enforceZipInfo["zipFilePath"]

        check = CheckFileExists(inputFilePath)
        yield check

        productId = wc.getProductIdFromSourceFile(inputFilePath)
        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "basketProductPath" : basketProductPath, # original product file or folder
                "inputFilePath" : inputFilePath,
                "productPattern" : wc.getProductPatternFromSourceFile(inputFilePath),
                "productId" : productId,
                "workingRoot" : os.path.join(self.paths['working'], productId),
                "noCopyState" : self.noStateCopy,
                "sourceSrs" : self.spatialConfig["sourceSrs"],
                "targetSrs" : self.spatialConfig["targetSrs"],
                "filenameDemData" : self.spatialConfig["filenameDemData"],
                "filenameSrs" : self.spatialConfig["filenameSrs"],
                "demFilename": self.spatialConfig["demFilename"],
                "demTitle" : self.spatialConfig["demTitle"],
                "metadataProjection" : self.spatialConfig["metadataProjection"],
                "placeName" : self.spatialConfig["metadataPlaceName"],
                "parentPlaceName" : self.spatialConfig["metadataParentPlaceName"]
            }, indent=4))

    def output(self):
        outFile = os.path.join(self.paths['state'], 'GetConfiguration.json')
        return LocalTarget(outFile)