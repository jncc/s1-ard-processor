import luigi
import os
import json
import logging
import process_s1_scene.common as wc
import datetime
import re
import zipfile
from string import Template
from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.GetConfiguration import GetConfiguration
from process_s1_scene.GetManifest import GetManifest
from process_s1_scene.ConfigureProcessing import ConfigureProcessing
from process_s1_scene.CheckFileExists import CheckFileExists

log = logging.getLogger('luigi-interface')

@requires(GetConfiguration, GetManifest, ConfigureProcessing)
class GenerateMetadata(luigi.Task):
    paths = luigi.DictParameter()
    metadataTemplate = luigi.Parameter()
    buildConfigFile = luigi.Parameter()

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

    def run(self):
        configuration = {}
        with self.input()[0].open('r') as getConfiguration:
            configuration = json.load(getConfiguration)

        getManifestInfo = ''
        with self.input()[1].open('r') as getManifest:
            getManifestInfo = json.load(getManifest)

        configureProcessingInfo = {}
        with self.input()[2].open('r') as configureProcessing:
            configureProcessingInfo = json.load(configureProcessing)

        manifestLoader = CheckFileExists(filePath=getManifestInfo["manifestFile"])
        yield manifestLoader

        manifest = ''
        with manifestLoader.output().open('r') as manifestFile:
            manifest = manifestFile.read()

        getBuildConfigTask = CheckFileExists(filePath=self.buildConfigFile)
        buildConfig = {}
        with getBuildConfigTask.output().open('r') as b:
            buildConfig = json.load(b)

        inputFileName = os.path.basename(configuration["inputFilePath"])

        fileIdentifier = os.path.splitext(wc.getOutputFileName(inputFileName, "VVVH", manifest, configuration["filenameDemData"], configuration["filenameSrs"]))[0]
        dateToday = str(datetime.date.today())
        boundingBox = self.getBoundingBox(manifest)
        startDate = self.getStartDate(manifest)
        endDate = self.getEndDate(manifest)
        collectionMode = self.getCollectionMode(manifest)
        projection = configuration["metadataProjection"]
        referenceSystemCodeSpace = configuration["targetSrs"].split(":")[0]
        referenceSystemCode = configuration["targetSrs"].split(":")[1]
        demTitle = configuration["demTitle"]
        placeName = configuration["placeName"]
        parentPlaceName = configuration["parentPlaceName"]
        snapVersion = buildConfig["snapVersion"]
        dockerImage = buildConfig["dockerImage"]

        metadataParams = {
            "fileIdentifier": fileIdentifier,
            "metadataDate": dateToday,
            "publishedDate": dateToday,
            "extentWestBound": boundingBox["west"],
            "extentEastBound": boundingBox["east"],
            "extentSouthBound": boundingBox["south"],
            "extentNorthBound": boundingBox["north"],
            "extentStartDate": startDate,
            "extentEndDate": endDate,
            "projection": projection,
            "referenceSystemCodeSpace": referenceSystemCodeSpace,
            "referenceSystemCode": referenceSystemCode,
            "polarisation": "VV+VH",
            "collectionMode": collectionMode,
            "demTitle": demTitle,
            "placeName": placeName,
            "parentPlaceName": parentPlaceName,
            "snapVersion": snapVersion,
            "dockerImage": dockerImage
        }

        template = ''
        ardMetadata = ''

        with open(self.metadataTemplate, "r") as templateFile:
            template = Template(templateFile.read())
            ardMetadata = template.substitute(metadataParams)

        inputFileName = os.path.basename(configuration["inputFilePath"])
        filename = fileIdentifier + "_meta.xml"
        ardMetadataFile = os.path.join(configureProcessingInfo["parameters"]["s1_ard_temp_output_dir"], filename)

        with open(ardMetadataFile, 'w') as out:
            out.write(ardMetadata)

        with self.output().open('w') as out:
            out.write(json.dumps({
                "ardMetadataFile" : ardMetadataFile
            }))



    def output(self):
        outputFile = os.path.join(self.paths["state"], 'GenerateMetadata.json')
        return LocalTarget(outputFile)