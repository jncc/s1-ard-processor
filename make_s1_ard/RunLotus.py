import luigi
import logging
import subprocess
import json
import os
import stat
import glob
import make_s1_ard.common as wc
from os.path import join

log = logging.getLogger('luigi-interface')

class RunLotus(luigi.Task):
    pathRoots = luigi.DictParameter()
    outputFile = luigi.Parameter()

    def createLuigiScript(self, inputFile, processingFileRoot, stateFileRoot, luigiScriptPath):
        luigiDir = self.pathRoots["luigiDir"]
        scriptDir = self.pathRoots["scriptDir"]
        demDir = self.pathRoots["demDir"]
        snapDir = self.pathRoots["snapDir"]
        outputDir = self.pathRoots["outputDir"]
        outputFile = self.outputFile

        productId = wc.getProductIdFromLocalSourceFile(inputFile)
        pathRoots = {
            "fileRoot": processingFileRoot,
            "state-localRoot": stateFileRoot,
            "scriptRoot": scriptDir,
            "local-dem-path": demDir,
            "snapPath": snapDir,
            "wafRoot": outputDir
        }

        luigiVenvCmd = "source {}/luigi-workflows-venv/bin/activate\n".format(luigiDir)
        luigiCmd = "PYTHONPATH='{}' luigi --module docker TeardownWorkflowFolders --productId {} --sourceFile '{}' --outputFile '{}' --pathRoots '{}' --removeSourceFile --local-scheduler" \
            .format(luigiDir,
                productId,
                inputFile,
                outputFile,
                json.dumps(pathRoots))
        
        with open(luigiScriptPath, 'w') as luigiScript:
            luigiScript.write("export PATH=/group_workspaces/jasmin2/defra_eo/tools/conda/miniconda2/bin:$PATH\n")
            luigiScript.write("source activate gdalenv\n")
            luigiScript.write(luigiVenvCmd)
            luigiScript.write(luigiCmd)

        st = os.stat(luigiScriptPath)
        os.chmod(luigiScriptPath, st.st_mode | stat.S_IEXEC | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def run(self):
        inputDir = self.pathRoots["inputDir"]
        processingDir = self.pathRoots["processingDir"]

        for inputFile in glob.glob(os.path.join(inputDir, "*.zip")):
            filename = os.path.basename(os.path.splitext(inputFile)[0])

            workspaceRoot = os.path.join(processingDir, filename)
            
            processingFileRoot = os.path.join(workspaceRoot, "processing")
            if not os.path.exists(processingFileRoot):
                os.makedirs(processingFileRoot)

            stateFileRoot = os.path.join(workspaceRoot, "states")
            if not os.path.exists(stateFileRoot):
                os.makedirs(stateFileRoot)

            luigiScriptPath = os.path.join(workspaceRoot, "run_luigi_workflow.sh")
            if not os.path.isfile(luigiScriptPath):
                self.createLuigiScript(inputFile, processingFileRoot, stateFileRoot, luigiScriptPath)

            lotusCmd = "bsub -q short-serial -R 'rusage[mem=18000]' -M 18000 -W 10:00 -o {}/%J.out -e {}/%J.err {}" \
                .format(
                    workspaceRoot,
                    workspaceRoot,
                    luigiScriptPath
                )

            try:
                subprocess.check_output(
                    lotusCmd,
                    stderr=subprocess.STDOUT,
                    shell=True)
            except subprocess.CalledProcessError as e:
                errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                log.error(errStr)
                raise RuntimeError(errStr)

    def output(self):
        outputFolder = self.pathRoots["state-localRoot"]
        return wc.getLocalStateTarget(outputFolder, "lotus_submit_success.json")