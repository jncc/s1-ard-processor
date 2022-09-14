import luigi
import os
import json
from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.ProcessRawToArd import ProcessRawToArd
from process_s1_scene.CheckFileExists import CheckFileExists

@requires(ProcessRawToArd)
class CheckArdFilesExist(luigi.Task):

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
            outFile.write(json.dumps(processedOutput, indent=4))

    def output(self):
        outputFile = os.path.join(self.paths["state"], "CheckArdFilesExist.json")
        return LocalTarget(outputFile)

