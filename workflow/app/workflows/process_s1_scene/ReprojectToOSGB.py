import luigi
import os
import re
import errno
import json
import logging
import process_s1_scene.common as wc
import subprocess
import distutils.dir_util as distutils
from luigi.util import requires
from functional import seq
from process_s1_scene.CheckOutputFilesExist import CheckOutputFilesExist 

log = logging.getLogger('luigi-interface')

@requires(CheckOutputFilesExist)
class ReprojectToOSGB(luigi.Task):
    sourceFile = luigi.Parameter()
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter()
    outputFile = luigi.Parameter()
    testProcessing = luigi.BoolParameter()
    processToS3 = luigi.BoolParameter(default=False)

    def runReprojection(self):

        spec = {}
        with self.input().open('r') as i:
            spec = json.loads(i.read())

        wgsOutputFile = self.outputFile.replace("OSGB1936", "UTMWGS84")

        p = re.compile(wgsOutputFile)

        outputFiles = (seq(spec['files']['VV'])
            .union(seq(spec['files']['VH']))
            .filter(lambda f: p.match(f)))

        if outputFiles.len() < 1:
            errorMsg = "Found no files to reproject"
            log.error(errorMsg)
            raise RuntimeError(errorMsg)
        
        for outputFile in outputFiles:
            if not self.testProcessing:
                try:
                    subprocess.check_output(
                        "gdalwarp -overwrite -s_srs EPSG:32630 -t_srs EPSG:27700 -r bilinear -dstnodata 0 -of GTiff -tr 10 10 --config CHECK_DISK_FREE_SPACE NO %s %s" % (outputFile, self.changeWgsToOsgb(outputFile)), 
                        stderr=subprocess.STDOUT,
                        shell=True)
                except subprocess.CalledProcessError as e:
                    errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                    log.error(errStr)
                    raise RuntimeError(errStr)
            else:
                wc.createTestFile(self.changeWgsToOsgb(outputFile))


    def changeWgsToOsgb(self, oldFilename):
        return oldFilename.replace("UTMWGS84", "OSGB1936")


    def run(self):
        inputJson = {}
        with self.input().open('r') as inFile:
            state = json.load(inFile)

        self.runReprojection()

        for index, tifFile in enumerate(state["files"]["VV"]):
            state["files"]["VV"][index] = self.changeWgsToOsgb(tifFile)
        
        for index, tifFile in enumerate(state["files"]["VH"]):
            state["files"]["VH"][index] = self.changeWgsToOsgb(tifFile)

        with self.output().open("w") as outFile:
            outFile.write(json.dumps(state))
                
    def output(self):
        if self.processToS3:
            outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
            return wc.getS3StateTarget(outputFolder, 'reprojectToOSGB.json')
        else:
            outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
            return wc.getLocalStateTarget(outputFolder, 'reprojectToOSGB.json')
