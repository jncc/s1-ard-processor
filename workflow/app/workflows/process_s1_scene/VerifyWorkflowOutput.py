import luigi
import json
import os
import logging
import process_s1_scene.common as wc

from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.TransferFinalOutput import TransferFinalOutput
from process_s1_scene.CheckFileExists import CheckFileExists

@requires(TransferFinalOutput)
class VerifyWorkflowOutput(luigi.Task):

    def run(self):
        transferFinalOutputInfo = {}
        with self.input()[0].open('r') as transferFinalOutput:
            transferFinalOutputInfo = json.load(transferFinalOutput)

        outputFiles = transferFinalOutputInfo["VV"] + transferFinalOutputInfo["VH"]
        outputFiles.append(transferFinalOutputInfo["merged"])
        outputFiles.append(transferFinalOutputInfo["metadata"])

        tasks = []

        for f in outputFiles:
            tasks.append(CheckFileExists(filePath=f))

        yield tasks

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "verifiedFiles": outputFiles
            }))


    def output(self):
        outputFile = os.path.join(self.paths["state"], "VerifyWorkflowOutput.json")
        return LocalTarget(outputFile)




