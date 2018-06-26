import luigi
import json
import re
import logging
import os
import docker.make_s1_ard.common as wc
import luigi
import subprocess
from luigi.util import requires
from functional import seq
from os.path import join
from luigi import LocalTarget
from docker.make_s1_ard.ReprojectToOSGB import ReprojectToOSGB

log = logging.getLogger('luigi-interface')

@requires(ReprojectToOSGB)
class MergeBands(luigi.Task):
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter()
    outputFile = luigi.Parameter()
    testProcessing = luigi.BoolParameter()
    processToS3 = luigi.BoolParameter(default=False)

    def run(self):
        spec = {}
        with self.input().open('r') as i:
            spec = json.loads(i.read())
    
        p = re.compile(self.outputFile)

        srcFiles = (seq(spec['files']['VV'])
            .union(seq(spec['files']['VH']))
            .filter(lambda f: p.match(f))
            .reduce(lambda x, f: x + ' ' + f))
        
        log.debug('merging files %s', srcFiles)
        productPattern = spec['productPattern']

        outputFile = join(join(self.pathRoots["fileRoot"], 'output/{}'.format(productPattern)), '{}_APGB_OSGB1936_RTC_SpkRL_dB.tif'.format(self.productId))

        cmdString = 'gdalbuildvrt -separate /vsistdout/ {}|gdal_translate -a_nodata nan -co BIGTIFF=YES -co TILED=YES -co COMPRESS=LZW --config CHECK_DISK_FREE_SPACE no /vsistdin/ {}' \
                    .format(srcFiles, outputFile) 

        if not self.testProcessing:
            log.info('Creating merged product from Gamma VH & VV bands')
            try:
                subprocess.check_output(cmdString, shell=True) 
            except subprocess.CalledProcessError as e:
                errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                log.error(errStr)
                raise RuntimeError(errStr)
        else:
            wc.createTestFile(outputFile)

        spec["files"]["merged"] = outputFile

        with self.output().open('w') as out:
            out.write(json.dumps(spec))

    def output(self):
        if self.processToS3:
            outputFolder = join(self.pathRoots["state-s3Root"], self.productId)
            return wc.getS3StateTarget(outputFolder, 'mergeBands.json')
        else:
            outputFolder = join(self.pathRoots["state-localRoot"], self.productId)
            return wc.getLocalStateTarget(outputFolder, 'mergeBands.json')


