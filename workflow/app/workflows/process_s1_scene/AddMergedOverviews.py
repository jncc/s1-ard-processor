import luigi
import json
import logging
import subprocess
import os
import process_s1_scene.common as wc
from luigi.util import requires
from process_s1_scene.MergeBands import MergeBands
from process_s1_scene.CheckFileExists import CheckFileExists

log = logging.getLogger('luigi-interface')

@requires(MergeBands)
class AddMergedOverviews(luigi.Task):
    paths = luigi.DictParameter()
    productId = luigi.Parameter()
    testProcessing = luigi.BoolParameter()

    def run(self):
        mergeBandsInfo = {}
        with self.input().open('r') as mergeBands:
            mergeBandsInfo = json.load(mergeBands)
        
        mergedProduct = mergeBandsInfo["mergedOutputFile"]

        t = CheckFileExists(filePath=mergedProduct)
        yield t

        cmdString = 'gdaladdo {} 2 4 8 16 32 64 128'.format(mergedProduct)

        retcode = 0
        if not self.testProcessing:
            log.info('Adding overlays to merged file')
            try:
                subprocess.check_output(cmdString, shell=True) 
            except subprocess.CalledProcessError as e:
                errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                log.error(errStr)
                raise RuntimeError(errStr)

        with self.output().open('w') as out:
            out.write(json.dumps(spec))

    def output(self):
        outputFile = os.path.join(self.paths["state"], "addMergedOverviews.json")
        return LocalTarget(outputFile)
