import process_s1_scene.common as wc
import json
import logging
import luigi
import os
import subprocess
import xml.etree.ElementTree
import zipfile

from process_s1_scene.PerpareWorkingFolder import PrepareWorkingFolder
from process_s1_scene.CreateLocalFile import CreateLocalFile
from luigi.util import requires
from luigi import LocalTarget

log = logging.getLogger('luigi-interface')
@requires(PrepareWorkingFolder)
class CutDEM(luigi.Task):
    paths = luigi.DictParameter()
    inputFileName = luigi.Parameter()
    productId = luigi.Parameter()
    testProcessing = luigi.BoolParameter()
    demFile = luigi.Parameter()

    def run(self):

        inputFilePath = os.path.join(self.paths["input"], self.inputFileName)
        cutLine = {}

        if not self.testProcessing:
            cutLinePath = os.path.join(self.paths["workingPath"], "/dem/cutline.geojson") 

            with zipfile.ZipFile(inputFilePath) as productZipFile:
                with productZipFile.open("%s.SAFE/preview/map-overlay.kml" % os.path.basename(inputFilePath).replace(".zip", "")) as overlay:
                    # Grab first latlong element as there should only be one
                    coordinatesXMLElement = xml.etree.ElementTree.fromstring(overlay.read().decode("utf-8")).findall(".//Document/Folder/GroundOverlay/gx:LatLonQuad/coordinates", {"gx": "http://www.google.com/kml/ext/2.2"})[0]
                    coordinates = []
                    # Push coordinates from XML into array, converting to floats
                    for coord in coordinatesXMLElement.text.split(' '):
                        coordinates.append(list(map(lambda x: float(x), coord.split(','))))
                    # Copy first coordinate to end of list to complete polygon
                    coordinates.append(coordinates[0])

                    cutLine = {
                            "type": "polygon",
                            "coordinates": [coordinates]
                        }

                    with open(cutLinePath, "w") as cutlineFile:
                        cutlineFile.write(json.dumps(cutLine))

            try:
                demPath = os.path.join(self.paths["static"], self.demFile)

                subprocess.check_output(
                    "gdalwarp -of GTiff -crop_to_cutline -overwrite --config CHECK_DISK_FREE_SPACE NO -cutline %s %s %s" % (cutLinePath ,demPath, self.paths["cutDemPath"]), 
                    stderr=subprocess.STDOUT,
                    shell=True)
            except subprocess.CalledProcessError as e:
                errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                log.error(errStr)
                raise RuntimeError(errStr)

        else:
            yield CreateLocalFile(filePath=self.paths["cutDemPath"], content="TEST_FILE")

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                'inputFilePath': inputPath, 
                'cutDemPath' : self.paths["cutDemPath"],
                'cutLine' : cutLine
            })

    def output(self):
        outFile = os.path.join(self.pathRoots['state'], 'CutDEM.json')
        return LocalTarget(outFile)