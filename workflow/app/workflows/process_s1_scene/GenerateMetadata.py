import luigi
import os
import json
import logging
import process_s1_scene.common as wc
import datetime
import re
import zipfile
import decimal
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
            latValues.append(decimal.Decimal(splitValues[0]))
            lonValues.append(decimal.Decimal(splitValues[1]))

        boundingBox = {
            "north": str(max(latValues)),
            "south": str(min(latValues)),
            "east": str(max(lonValues)),
            "west": str(min(lonValues))
        }

        return boundingBox

    def getAcquisitionDate(self, manifestString):
        pattern = "<safe:startTime>(.+)<\/safe:startTime>"
        dateString = re.search(pattern, manifestString).group(1)
        date = datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S.%f")
        return self.getFormattedDateTime(date)

    def getStartDateTime(self, manifestString):
        pattern = "<safe:startTime>(.+)<\/safe:startTime>"
        dateString = re.search(pattern, manifestString).group(1)
        date = datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S.%f")
        return self.getFormattedDateTime(date)

    def getEndDateTime(self, manifestString):
        pattern = "<safe:stopTime>(.+)<\/safe:stopTime>"
        dateString = re.search(pattern, manifestString).group(1)
        date = datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S.%f")
        return self.getFormattedDateTime(date)

    def getFormattedDateTime(self, date):
        return str(date.strftime("%Y-%m-%dT%H:%M:%SZ"))

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
        dateToday = self.getFormattedDateTime(datetime.datetime.now())
        acquisitionDate = self.getAcquisitionDate(manifest)
        boundingBox = self.getBoundingBox(manifest)
        startDatetime = self.getStartDateTime(manifest)
        endDatetime = self.getEndDateTime(manifest)
        collectionMode = self.getCollectionMode(manifest)
        collectionTime = startDatetime.split("T")[1].split("Z")[0]
        projection = configuration["metadataProjection"]
        referenceSystemCodeSpace = configuration["targetSrs"].split(":")[0]
        referenceSystemCode = configuration["targetSrs"].split(":")[1]
        demTitle = configuration["demTitle"]
        placeName = configuration["placeName"]
        parentPlaceName = configuration["parentPlaceName"]
        snapVersion = buildConfig["snapVersion"]
        dockerImage = buildConfig["dockerImage"]
        gdalVersion = buildConfig["gdalVersion"]

        metadataParams = {
            "fileIdentifier": fileIdentifier,
            "title": fileIdentifier,
            "metadataDate": dateToday,
            "publishedDate": acquisitionDate,
            "extentWestBound": boundingBox["west"],
            "extentEastBound": boundingBox["east"],
            "extentSouthBound": boundingBox["south"],
            "extentNorthBound": boundingBox["north"],
            "extentStartDate": startDatetime,
            "extentEndDate": endDatetime,
            "projection": projection,
            "referenceSystemCodeSpace": referenceSystemCodeSpace,
            "referenceSystemCode": referenceSystemCode,
            "polarisation": "VV+VH",
            "collectionMode": collectionMode,
            "collectionTime": collectionTime,
            "demTitle": demTitle,
            "placeName": placeName,
            "parentPlaceName": parentPlaceName,
            "snapVersion": snapVersion,
            "dockerImage": dockerImage,
            "gdalVersion": gdalVersion
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