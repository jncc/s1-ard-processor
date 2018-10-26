import luigi
import json
import os
import logging

from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.AddMergedOverviews import AddMergedOverviews
from process_s1_scene.GetInputFileInfo import GetInputFileInfo
from process_s1_scene.GenerateMetadata import GenerateMetadata
from process_s1_scene.ReprojectToOSGB import ReprojectToOSGB

@requires(GetInputFileInfo, AddMergedOverviews, GenerateMetadata)
class RenameOutputFiles(luigi.Task):
    paths = luigi.DictParameter()

    def generateName(self):


    def run(self):
        inputFileInfo = {}
        with self.input()[0].open('r') as getInputFileInfo:
            inputFileInfo = json.load(getInputFileInfo)

        addMergedOverviewsInfo = {}
        with self.input()[1].open('r') as addMergedOverviews:
            addMergedOverviewsInfo = json.load(addMergedOverviews)

        generateMetadataInfo = {}
        with self.input()[2].open('r') as generateMetadata:
            generateMetadataInfo = json.load(generateMetadata)

        productName = self.generateName()

    def output(self):
        outputFile = os.path.join(self.paths["state"], "RenameOutputFiles.json")
        return LocalTarget(outputFile)


