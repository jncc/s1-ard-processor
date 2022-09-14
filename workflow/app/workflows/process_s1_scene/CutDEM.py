import process_s1_scene.common as wc
import simplejson as json
import logging
import luigi
import os
import subprocess
import re
import decimal

from process_s1_scene.GetConfiguration import GetConfiguration
from process_s1_scene.GetManifest import GetManifest
from process_s1_scene.CheckFileExists import CheckFileExists
from luigi.util import requires
from luigi import LocalTarget

log = logging.getLogger('luigi-interface')

@requires(GetConfiguration, GetManifest)
class CutDEM(luigi.Task):
    paths = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()

    def getBoundingBoxCoords(self, manifestString):
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

        north = max(latValues)
        south = min(latValues)
        east = max(lonValues)
        west = min(lonValues)

        boundingBoxCoords = [[west, south], [west, north], [east, north], [east, south], [west, south]]

        return boundingBoxCoords

    def run(self):

        configuration = {}
        with self.input()[0].open('r') as getConfiguration:
            configuration = json.load(getConfiguration)

        getManifestInfo = {}
        with self.input()[1].open('r') as getManifest:
            getManifestInfo = json.load(getManifest)

        manifestLoader = CheckFileExists(filePath=getManifestInfo["manifestFile"])
        yield manifestLoader

        manifest = {}
        with manifestLoader.output().open('r') as manifestFile:
            manifest = manifestFile.read()

        cutLine = {}

        cutDemPathRoot = wc.createWorkingPath(configuration["workingRoot"], 'dem')
        cutDemPath = os.path.join(cutDemPathRoot, 'cutDem.tif')
        cutLinePath = os.path.join(cutDemPathRoot, "cutline.geojson") 
        demPath = os.path.join(self.paths["static"], configuration["demFilename"])
        boundingBoxCoords = self.getBoundingBoxCoords(manifest)
        
        inputFilePath = configuration["inputFilePath"]

        cutLine = {
            "type": "polygon",
            "coordinates": [boundingBoxCoords]
        }

        with open(cutLinePath, "w") as cutlineFile:
            cutlineFile.write(json.dumps(cutLine, use_decimal=True))

        if not self.testProcessing:
            try:
                subprocess.check_output(
                    "gdalwarp -of GTiff -crop_to_cutline -overwrite --config CHECK_DISK_FREE_SPACE NO -cutline {} {} {}".format(cutLinePath, demPath, cutDemPath), 
                    stderr=subprocess.STDOUT,
                    shell=True)
            except subprocess.CalledProcessError as e:
                errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                log.error(errStr)
                raise RuntimeError(errStr)

        else:
            wc.createTestFile(cutDemPath)

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                'cutDemPath' : cutDemPath,
                'cutLine' : cutLine
            }, use_decimal=True, indent=4))

    def output(self):
        outFile = os.path.join(self.paths['state'], 'CutDEM.json')
        return LocalTarget(outFile)