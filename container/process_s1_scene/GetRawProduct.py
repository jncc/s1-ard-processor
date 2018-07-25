import boto3
import botocore
import luigi
import os
import logging
import json
import common as wc

from workflow_common.s3 import getPathFromS3Path, getBucketNameFromS3Path
from luigi.util import requires
from InitialiseDataFolder import InitialiseDataFolder
from shutil import copyfile

log = logging.getLogger('luigi-interface')

@requires(InitialiseDataFolder)
class GetRawProduct(luigi.Task):
    sourceFile = luigi.Parameter()
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter()
    processToS3 = luigi.BoolParameter(default=False)

    def run(self):
        # sourceFile        s3://bucket-name/sentinel/1/raw/S1A_IW_GRDH_1SDV_20171101T065336_20171101T065401_019068_020409_0E93.zip
        # productFilename   S1A_IW_GRDH_1SDV_20171101T065336_20171101T065401_019068_020409_0E93.zip
        # productId         S1A_20171101_065336_065401
        # productPattern    S1A_01Nov2017_065336_065401
        
        if self.processToS3:
            productFilename = os.path.basename(getPathFromS3Path(self.sourceFile))
        else:
            productFilename = os.path.basename(self.sourceFile)
        # productId = '%s_%s_%s_%s' % (productFilename[0:3], productFilename[17:25], productFilename[26:32], productFilename[42:48])
        # productPattern = '%s_%s%s%s_%s_%s' % (productFilename[0:3], productFilename[23:25], datetime.strptime(productFilename[21:23], '%m').strftime('%b'), productFilename[17:21], productFilename[26:32], productFilename[42:48])

        productPattern = wc.getProductPatternFromSourceFile(self.sourceFile)

        with self.output().open('w') as out:
            tempFile = os.path.join(os.path.join(self.pathRoots["fileRoot"], 'raw'), productFilename)

            if self.processToS3:
                s3 = boto3.resource('s3')
                s3.Bucket(getBucketNameFromS3Path(self.sourceFile)).download_file(getPathFromS3Path(self.sourceFile), tempFile)

            copyfile(self.sourceFile, tempFile)

            out.write(json.dumps({
                'sourceFile': self.sourceFile,
                'productId': self.productId,
                'productPattern': productPattern,
                'tempFile': tempFile
            }))

    def output(self):
        if self.processToS3:
            outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
            return wc.getS3StateTarget(outputFolder, 'downloaded.json')
        else:
            outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
            return wc.getLocalStateTarget(outputFolder, 'downloaded.json')
        