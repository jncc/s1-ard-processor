import process_s1_scene.common as wc
import json
import logging
import luigi
import os
import subprocess
import xml.etree.ElementTree
import zipfile

from process_s1_scene.CheckFileExists import CheckFileExists
from process_s1_scene.GetRawProduct import GetRawProduct
from process_s1_scene.FetchSourceDEM import FetchSourceDEM
from luigi.util import inherits

log = logging.getLogger('luigi-interface')

@inherits(FetchSourceDEM)
@inherits(GetRawProduct)
class CutDEM(luigi.Task):
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter()
    testProcessing = luigi.BoolParameter()
    processToS3 = luigi.BoolParameter(default=False)

    def requires(self):
        t = []
        t.append(self.clone(FetchSourceDEM))
        t.append(self.clone(GetRawProduct))
        return t

    def run(self):
        with self.input()[1].open('r') as inFile:
            downloadedOutput = json.load(inFile)

            if not self.testProcessing:
                with zipfile.ZipFile(downloadedOutput["tempFile"]) as productZipFile:
                    with productZipFile.open("%s.SAFE/preview/map-overlay.kml" % os.path.basename(downloadedOutput["tempFile"]).replace(".zip", "")) as overlay:
                        # Grab first latlong element as there should only be one
                        coordinatesXMLElement = xml.etree.ElementTree.fromstring(overlay.read().decode("utf-8")).findall(".//Document/Folder/GroundOverlay/gx:LatLonQuad/coordinates", {"gx": "http://www.google.com/kml/ext/2.2"})[0]
                        coordinates = []
                        # Push coordinates from XML into array, converting to floats
                        for coord in coordinatesXMLElement.text.split(' '):
                            coordinates.append(list(map(lambda x: float(x), coord.split(','))))
                        # Copy first coordinate to end of list to complete polygon
                        coordinates.append(coordinates[0])

                        with open(os.path.join(self.pathRoots["fileRoot"], "dem/cutline.geojson"), "w") as cutline:
                            cutline.write(json.dumps({
                                "type": "polygon",
                                "coordinates": [coordinates]
                            }))

                try:
                    subprocess.check_output(
                        "gdalwarp -of GTiff -crop_to_cutline -overwrite --config CHECK_DISK_FREE_SPACE NO -cutline %s %s %s" % (os.path.join(self.pathRoots["fileRoot"], "dem/cutline.geojson"), self.pathRoots['local-dem-path'], os.path.join(self.pathRoots["fileRoot"], "dem/cut_dem.tif")), 
                        stderr=subprocess.STDOUT,
                        shell=True)
                except subprocess.CalledProcessError as e:
                    errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                    log.error(errStr)
                    raise RuntimeError(errStr)
            else:
                wc.createTestFile(os.path.join(self.pathRoots["fileRoot"], "dem/cut_dem.tif"))


            with self.output().open("w") as outFile:
                outFile.write(json.dumps({
                    'sourceFile': downloadedOutput["sourceFile"],
                    'productId': downloadedOutput["productId"],
                    'productPattern': downloadedOutput["productPattern"],
                    'cutDEM': os.path.join(self.pathRoots["fileRoot"], "dem/cut_dem.tif"),
                    'tempFile': downloadedOutput["tempFile"]
                }))


    def output(self):
        if self.processToS3:
            outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
            return wc.getS3StateTarget(outputFolder, 'cutDEM.json')
        else:
            outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
            return wc.getLocalStateTarget(outputFolder, 'cutDEM.json')
