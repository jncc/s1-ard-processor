import luigi
import os
import re
import json
import logging
import shutil
import process_s1_scene.common as wc
from shutil import copyfile
from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.GetConfiguration import GetConfiguration
from process_s1_scene.ModifyNoDataTif import ModifyNoDataTif
from process_s1_scene.GenerateMetadata import GenerateMetadata

from shutil import copy

log = logging.getLogger('luigi-interface')

@requires(GetConfiguration,
    ModifyNoDataTif,
    GenerateMetadata)
class TransferFinalOutput(luigi.Task):
    paths = luigi.DictParameter()

    def copyMergedProduct(self, mergedProduct, generatedProductPath, current_progress):
        targetPath = os.path.join(generatedProductPath, os.path.basename(mergedProduct)) 
        copy(mergedProduct, targetPath)
        current_progress["merged"] = targetPath

    def copyMetadata(self, metadata, generatedProductPath, current_progress):
        targetPath = os.path.join(generatedProductPath, os.path.basename(metadata))
        copy(metadata, targetPath)
        current_progress["metadata"] = targetPath

    def getOutputPath(self, root, productId, productName):
        year = productId[4:8]
        month = productId[8:10]
        day = productId[10:12]

        return os.path.join(root, year, month, day, productName)

    def run(self):
        configuration = {}
        with self.input()[0].open('r') as getConfiguration:
            configuration = json.load(getConfiguration)

        modifyNoDataTifInfo = {}
        with self.input()[1].open('r') as modifyNoDataTif:
            modifyNoDataTifInfo = json.load(modifyNoDataTif)

        generateMetadataInfo = {}
        with self.input()[2].open('r') as generateMetadata:
            generateMetadataInfo = json.load(generateMetadata)

        productName = os.path.splitext(os.path.basename(modifyNoDataTifInfo["modifyNoDataTif"]))[0]
        outputPath = self.getOutputPath(self.paths["output"], configuration["productId"], productName)

        if os.path.exists(outputPath):
            log.info("Removing product path {} from output folder".format(outputPath))
            shutil.rmtree(outputPath)

        os.makedirs(outputPath)

        current_progress = {
            "outputPath" : outputPath,
            'merged' : '',
            'metadata' : ''
        }

        self.copyMergedProduct(modifyNoDataTifInfo["modifyNoDataTif"], outputPath, current_progress)

        self.copyMetadata(generateMetadataInfo["ardMetadataFile"], outputPath, current_progress)
        
        with self.output().open("w") as outFile:
            outFile.write(json.dumps(current_progress, indent=4))

    def output(self):
        outFile = os.path.join(self.paths['state'], 'TransferFinalOutput.json')
        return LocalTarget(outFile)
