import luigi
import os
import json
import logging
import process_s1_scene.common as wc
import uuid
import datetime
import re
import zipfile
from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.GetManifest import GetManifest
from process_s1_scene.ConfigureProcessing import ConfigureProcessing
from process_s1_scene.MergeBands import MergeBands
from string import Template

log = logging.getLogger('luigi-interface')

@requires(GetManifest, ConfigureProcessing, MergeBands)
class GenerateMetadata(luigi.Task):
    paths = luigi.DictParameter()

    def run(self):
        manifest = ''
        with self.input()[0].open('r') as getManifest:
            manifest = getManifest.read()

        configureProcessingInfo = {}
        with self.input()[1].open('r') as configureProcessing:
            configureProcessingInfo = json.load(configureProcessing)

        mergeBandsInfo = {}
        with self.input()[2].open('r') as mergeBands:
            mergeBandsInfo = json.load(mergeBands)

        dateToday = str(datetime.date.today())
        boundingBox = self.getBoundingBox(manifest)
        startDate = self.getStartDate(manifest)
        endDate = self.getEndDate(manifest)
        collectionMode = self.getCollectionMode(manifest)

        metadataParams = {
            "uuid": uuid.uuid4(),
            "metadataDate": dateToday,
            "publishedDate": dateToday,
            "extentWestBound": boundingBox["west"],
            "extentEastBound": boundingBox["east"],
            "extentSouthBound": boundingBox["south"],
            "extentNorthBound": boundingBox["north"],
            "extentStartDate": startDate,
            "extentEndDate": endDate,
            "datasetVersion": "v1.0",
            "projection": "OSGB1936",
            "polarisation": "VV+VH",
            "collectionMode": collectionMode
        }

        template = ''
        ardMetadata = ''

        with open("process_s1_scene/metadata_template/s1_metadata_template.xml", "r") as templateFile:
            template = Template(templateFile.read())
            ardMetadata = template.substitute(metadataParams)

        filename = os.path.splitext(os.path.basename(mergeBandsInfo["mergedOutputFile"]))[0] + ".xml"
        ardMetadataFile = os.path.join(configureProcessingInfo["parameters"]["s1_ard_temp_output_dir"], filename)

        with open(ardMetadataFile, 'w') as out:
            out.write(ardMetadata)

        with self.output().open('w') as out:
            out.write(json.dumps({
                "ardMetadataFile" : ardMetadataFile
            }))

    def getBoundingBox(self, manifestString):
        pattern = "<gml:coordinates>.+<\/gml:coordinates>"
        coordinatesString = re.search(pattern, manifestString).group(0)

        coordinatePattern = "-?\d+\.\d+,-?\d+\.\d+" # finds strings like 60.113426,-7.616333
        coordinateStringPairs = re.findall(coordinatePattern, coordinatesString)

        latValues = []
        lonValues = []
        for pair in coordinateStringPairs:
            splitValues = pair.split(",")
            latValues.append(splitValues[0])
            lonValues.append(splitValues[1])

        boundingBox = {
            "north": max(latValues),
            "south": min(latValues),
            "east": max(lonValues),
            "west": min(lonValues)
        }

        return boundingBox

    def getStartDate(self, manifestString):
        pattern = "<safe:startTime>(.+)<\/safe:startTime>"
        dateString = re.search(pattern, manifestString).group(1)
        date = datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S.%f")
        return date.strftime("%Y-%m-%d")

    def getEndDate(self, manifestString):
        pattern = "<safe:stopTime>(.+)<\/safe:stopTime>"
        dateString = re.search(pattern, manifestString).group(1)
        date = datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S.%f")
        return date.strftime("%Y-%m-%d")

    def getCollectionMode(self, manifestString):
        pattern = "<s1sarl1:mode>(.+)<\/s1sarl1:mode>"
        mode = re.search(pattern, manifestString).group(1)
        return mode

    def output(self):
        outputFile = os.path.join(self.paths["state"], 'GenerateMetadata.json')
        return LocalTarget(outputFile)