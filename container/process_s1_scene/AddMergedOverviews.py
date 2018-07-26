import luigi
import json
import logging
import subprocess
import os
import container.process_s1_scene.common as wc
from luigi.util import requires
from container.process_s1_scene.MergeBands import MergeBands
from container.process_s1_scene.CheckFileExists import CheckFileExists

log = logging.getLogger('luigi-interface')

@requires(MergeBands)
class AddMergedOverviews(luigi.Task):
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter()
    testProcessing = luigi.BoolParameter()
    processToS3 = luigi.BoolParameter(default=False)

    def run(self):
        spec = {}
        with self.input().open('r') as i:
            spec = json.loads(i.read())
        
        mergedProduct = spec["files"]["merged"]

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
        if self.processToS3:
            outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
            return wc.getS3StateTarget(outputFolder, 'addMergedOverviews.json')
        else:
            outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
            return wc.getLocalStateTarget(outputFolder, 'addMergedOverviews.json')
        
