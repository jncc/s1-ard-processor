import luigi
import os
import json
import logging
import process_s1_scene.common as wc
import uuid
import datetime
import re
import zipfile
from luigi.util import requires
from process_s1_scene.AddMergedOverviews import AddMergedOverviews
from string import Template

log = logging.getLogger('luigi-interface')

@requires(AddMergedOverviews)
class GenerateMetadata(luigi.Task):
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter()
    sourceFile = luigi.Parameter()

    def run(self):
        with self.input().open('r') as addMergedOverviewsFile:
            addMergedOverviews = json.loads(addMergedOverviewsFile.read())

        manifest = self.getManifest()

        dateToday = str(datetime.date.today())
        boundingBox = self.getBoundingBox(manifest)
        startDate = self.getStartDate(manifest)
        endDate = self.getEndDate(manifest)
        collectionMode = self.getCollectionMode(manifest)
        projection = self.getProjectionFromOutputFile(addMergedOverviews["files"]["VV"][0])

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
            "projection": projection,
            "polarisation": "VV+VH",
            "collectionMode": collectionMode
        }

        with open("process_s1_scene/metadata_template/s1_metadata_template.xml", "r") as templateFile:
            template = Template(templateFile.read())
            metadataString = template.substitute(metadataParams)

        metadataFilename = os.path.splitext(os.path.basename(addMergedOverviews["files"]["merged"]))[0] + ".xml"
        metadataFilepath = os.path.join(os.path.join(os.path.join(self.pathRoots["fileRoot"], "output"), addMergedOverviews["productPattern"]), metadataFilename)
        
        with open(metadataFilepath, 'w') as out:
            out.write(metadataString)

        addMergedOverviews["files"]["metadata"] = metadataFilepath

        with self.output().open('w') as out:
            out.write(json.dumps(addMergedOverviews))

    def getManifest(self):
        rawZip = zipfile.ZipFile(self.sourceFile, 'r')
        manifestPath = os.path.join(os.path.splitext(os.path.basename(self.sourceFile))[0]+".SAFE", "manifest.safe")
        manifest = rawZip.read(manifestPath).decode("utf-8")
        return manifest

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

    def getProjectionFromOutputFile(self, outputFile):
        productFilename = os.path.basename(outputFile)
        return '%s' % (productFilename[43:51])

    def output(self):
        outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
        return wc.getLocalStateTarget(outputFolder, 'generateMetadata.json')