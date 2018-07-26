import luigi
import logging
import subprocess
import json
import os
import stat
import glob
import process_s1_basket.common as wc
from os.path import join

log = logging.getLogger('luigi-interface')

class RunSingularityInLotus(luigi.Task):
    pathRoots = luigi.DictParameter()
    outputFile = luigi.Parameter()

    def createSingularityScript(self, inputFile, processingFileRoot, stateFileRoot, singularityScriptPath):
        demDir = self.pathRoots["demDir"]
        outputDir = self.pathRoots["outputDir"]
        singularityDir = self.pathRoots["singularityDir"]
        singularityImgDir = self.pathRoots["singularityImgDir"]

        realRawDir = os.path.dirname(os.path.realpath(inputFile))
        productId = wc.getProductIdFromLocalSourceFile(inputFile)

        singularityCmd = "{}/singularity exec --bind {}:/data/sentinel/1 --bind {}:/data/states --bind {}:/data/raw --bind {}:/data/dem --bind {}:/data/processed {}/s1-ard-processor.simg /app/exec.sh --productId {} --sourceFile '{}' --outputFile '{}'" \
            .format(singularityDir,
                processingFileRoot,
                stateFileRoot,
                realRawDir,
                demDir,
                outputDir,
                singularityImgDir,
                productId,
                inputFile,
                outputDir)
        
        with open(singularityScriptPath, 'w') as singularityScript:
            singularityScript.write(singularityCmd)

        st = os.stat(singularityScriptPath)
        os.chmod(singularityScriptPath, st.st_mode | 0o110 )

        log.info("Created run_singularity_workflow.sh for " + inputFile + " with command " + singularityCmd)

    def run(self):
        inputDir = self.pathRoots["inputDir"]
        processingDir = self.pathRoots["processingDir"]

        for inputFile in glob.glob(os.path.join(inputDir, "*.zip")):
            log.info("Found " + inputFile + ", setting up directories")

            filename = os.path.basename(os.path.splitext(inputFile)[0])

            workspaceRoot = os.path.join(processingDir, filename)
            
            processingFileRoot = os.path.join(workspaceRoot, "processing")
            if not os.path.exists(processingFileRoot):
                os.makedirs(processingFileRoot)

            stateFileRoot = os.path.join(workspaceRoot, "states")
            if not os.path.exists(stateFileRoot):
                os.makedirs(stateFileRoot)

            singularityScriptPath = os.path.join(workspaceRoot, "run_singularity_workflow.sh")
            if not os.path.isfile(singularityScriptPath):
                self.createSingularityScript(inputFile, processingFileRoot, stateFileRoot, singularityScriptPath)

            lotusCmd = "bsub -q short-serial -R 'rusage[mem=18000]' -M 18000000 -W 10:00 -o {}/%J.out -e {}/%J.err {}" \
                .format(
                    workspaceRoot,
                    workspaceRoot,
                    singularityScriptPath
                )

            try:
                # subprocess.check_output(
                #     lotusCmd,
                #     stderr=subprocess.STDOUT,
                #     shell=True)
                log.info("Successfully submitted lotus job for " + inputFile + " using command: " + lotusCmd)
            except subprocess.CalledProcessError as e:
                errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                log.error(errStr)
                raise RuntimeError(errStr)

    def output(self):
        outputFolder = self.pathRoots["processingDir"]
        return wc.getLocalStateTarget(outputFolder, "lotus_submit_success.json")