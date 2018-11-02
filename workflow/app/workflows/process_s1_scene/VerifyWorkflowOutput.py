import luigi
import json
import os
import logging
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

        outputFiles = transferFinalOutputInfo["VV"] + transferFinalOutputInfo["VH"]
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

            if self.removeInputFile:
                os.remove(configuration["inputFilePath"])
                removedItems.append(configuration["inputFilePath"])

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "verifiedFiles": outputFiles,
                "cleanUp" : {
                    "removedItems" : removedItems
                }
            }))


    def output(self):
        outputFile = os.path.join(self.paths["state"], "VerifyWorkflowOutput.json")
        return LocalTarget(outputFile)




