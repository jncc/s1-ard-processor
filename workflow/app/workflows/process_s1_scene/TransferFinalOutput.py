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
from process_s1_scene.GetInputFileInfo import GetInputFileInfo
from process_s1_scene.ProcessRawToArd import ProcessRawToArd
from process_s1_scene.ReprojectToOSGB import ReprojectToOSGB
from process_s1_scene.AddMergedOverviews import AddMergedOverviews
from process_s1_scene.GenerateMetadata import GenerateMetadata

from shutil import copy

log = logging.getLogger('luigi-interface')

@requires(GetInputFileInfo, 
    ReprojectToOSGB, 
    AddMergedOverviews,
    GenerateMetadata)
class TransferFinalOutput(luigi.Task):
    paths = luigi.DictParameter()

    def getPathFromProductId(self, root, productId):
        year = productId[4:8]
        month = productId[8:10]
        day = productId[10:12]

        return os.path.join(os.path.join(os.path.join(os.path.join(root, year), month), day), productId)
    
    def copyPolarisationFiles(self, polarisation, generatedProductPath, reprojectToOSGBInfo, current_progress, productId):
        polarisationPath = os.path.join(generatedProductPath, polarisation)

        os.makedirs(polarisationPath)

        for product in reprojectToOSGBInfo["reprojectedFiles"][polarisation]:
            targetPath = os.path.join(polarisationPath, '{}{}'.format(productId, os.path.basename(product)[27:]))
            copy(product, targetPath)
            current_progress[polarisation].append(targetPath)

    def copyMergedProduct(self, mergedProduct, generatedProductPath, current_progress):
        targetPath = os.path.join(generatedProductPath, os.path.basename(mergedProduct)) 
        copy(mergedProduct, targetPath)
        current_progress["merged"] = targetPath

    def copyMetadata(self, metadata, generatedProductPath, current_progress):
        targetPath = os.path.join(generatedProductPath, os.path.basename(metadata))
        copy(metadata, targetPath)
        current_progress["metadata"] = targetPath

    def run(self):
        inputFileInfo = {}
        with self.input()[0].open('r') as getInputFileInfo:
            inputFileInfo = json.load(getInputFileInfo)

        reprojectToOSGBInfo = {}
        with self.input()[1].open('r') as reprojectToOSGB:
            reprojectToOSGBInfo = json.load(reprojectToOSGB)

        addMergedOverviewsInfo = {}
        with self.input()[2].open('r') as addMergedOverviews:
            addMergedOverviewsInfo = json.load(addMergedOverviews)

        generateMetadataInfo = {}
        with self.input()[3].open('r') as generateMetadata:
            generateMetadataInfo = json.load(generateMetadata)

        generatedProductPath = self.getPathFromProductId(self.paths["output"], inputFileInfo["productId"])

        if os.path.exists(generatedProductPath):
            log.info("Removing product path {} from output folder".format(generatedProductPath))
            shutil.rmtree(generatedProductPath)

        os.makedirs(generatedProductPath)

        current_progress = {
            "outputPath" : generatedProductPath,
            'VV': [],
            'VH': [],
            'merged' : '',
            'metadata' : ''
        }

        self.copyPolarisationFiles("VV", generatedProductPath, reprojectToOSGBInfo, current_progress, inputFileInfo["productId"])
        self.copyPolarisationFiles("VH", generatedProductPath, reprojectToOSGBInfo, current_progress, inputFileInfo["productId"])

        self.copyMergedProduct(addMergedOverviewsInfo["overviewsAddedTo"], generatedProductPath, current_progress)

        self.copyMetadata(generateMetadataInfo["ardMetadataFile"], generatedProductPath, current_progress)
        
        with self.output().open("w") as outFile:
            outFile.write(json.dumps(current_progress))

    def output(self):
        outFile = os.path.join(self.paths['state'], 'TransferFinalOutput.json')
        return LocalTarget(outFile)
