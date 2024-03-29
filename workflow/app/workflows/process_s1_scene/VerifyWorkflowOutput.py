import luigi
import json
import os
import shutil

from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.TransferFinalOutput import TransferFinalOutput
from process_s1_scene.GetConfiguration import GetConfiguration
from process_s1_scene.CheckFileExists import CheckFileExists

@requires(TransferFinalOutput, GetConfiguration)
class VerifyWorkflowOutput(luigi.Task):
    paths = luigi.DictParameter()
    removeInputFile = luigi.BoolParameter()
    noClean = luigi.BoolParameter()

    def run(self):
        transferFinalOutputInfo = {}
        with self.input()[0].open('r') as transferFinalOutput:
            transferFinalOutputInfo = json.load(transferFinalOutput)

        configuration = {}
        with self.input()[1].open('r') as getConfiguration:
            configuration = json.load(getConfiguration)

        sourceProductId = os.path.basename(configuration["inputFilePath"]).split('.')[0]

        outputFiles = []
        outputFiles.append(transferFinalOutputInfo["merged"])
        outputFiles.append(transferFinalOutputInfo["metadata"])

        tasks = []

        for f in outputFiles:
            tasks.append(CheckFileExists(filePath=f))

        yield tasks

        removedItems = []
        if not self.noClean:
            shutil.rmtree(configuration["workingRoot"])
            removedItems.append(configuration["workingRoot"])

            os.remove(configuration["inputFilePath"])
            removedItems.append(configuration["inputFilePath"])
            
            if self.removeInputFile:
                if os.path.isfile(configuration["basketProductPath"]):
                    os.remove(configuration["basketProductPath"])
                else:
                    shutil.rmtree(configuration["basketProductPath"])
                    
                removedItems.append(configuration["basketProductPath"])

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "sourceProductId" : sourceProductId,
                "verifiedFiles": outputFiles,
                "cleanUp" : {
                    "removedItems" : removedItems
                }
            }, indent=4))


    def output(self):
        outputFile = os.path.join(self.paths["state"], "VerifyWorkflowOutput.json")
        return LocalTarget(outputFile)




