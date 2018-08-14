import luigi
import process_s1_scene.common as wc
import os
import json
from luigi.util import requires
from process_s1_scene.ProcessRawToArd import ProcessRawToArd
from process_s1_scene.CheckFileExists import CheckFileExists

@requires(ProcessRawToArd)
class CheckOutputFilesExist(luigi.Task):
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter()
    processToS3 = luigi.BoolParameter(default=False)

    def run(self):
        processedOutput = {}
        with self.input().open('r') as inFile:
            processedOutput = json.load(inFile)

        files = processedOutput["files"]["VV"] + processedOutput["files"]["VH"] 
        
        tasks = []

        for f in files:
            tasks.append(CheckFileExists(filePath=f))

        yield tasks

        with self.output().open("w") as outFile:
            outFile.write(json.dumps(processedOutput))

    def output(self):
        if self.processToS3:
            outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
            return wc.getS3StateTarget(outputFolder, 'checkOutputFilesExist.json')
        else:
            outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
            return wc.getLocalStateTarget(outputFolder, 'checkOutputFilesExist.json')

