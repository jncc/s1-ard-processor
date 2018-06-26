import luigi
import os
import json
import boto3
import docker.make_s1_ard.common as wc
from luigi.util import inherits, requires
from docker.make_s1_ard.AddMergedOverviews import AddMergedOverviews
from workflow_common.s3 import getPathFromS3Path, getBucketNameFromS3Path

# todo: There should probably be a test like CheckOutputFilesExist for the uploaded files after this.

@requires(AddMergedOverviews)
class TransferArdToS3(luigi.Task):
    sourceFile = luigi.Parameter()
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter(default=False)
    
    def getPathFromProductId(self, root, productId):
        year = productId[4:8]
        month = productId[8:10]
        day = productId[10:12]

        return os.path.join(os.path.join(os.path.join(os.path.join(root, year), month), day), productId)


    def run(self):
        with self.input().open('r') as processed:
            
            current_progress = json.loads(processed.read())
            current_progress['outputs'] = {
                'VV': [],
                'VH': [],
                'merged' : ''
            }

            generatedProductPath = self.getPathFromProductId(getPathFromS3Path(self.pathRoots["product-s3Root"]), self.productId)

            s3 = boto3.resource('s3')
            s3Bucket = s3.Bucket(getBucketNameFromS3Path(self.sourceFile))

            for product in current_progress['files']['VV']:
                targetPath = os.path.join(os.path.join(generatedProductPath, 'VV'), '%s%s' % (self.productId, os.path.basename(product)[27:]))
                s3Bucket.upload_file(product, targetPath)
                current_progress['outputs']['VV'].append(targetPath)

            for product in current_progress['files']['VH']:
                targetPath = os.path.join(os.path.join(generatedProductPath, 'VH'), '%s%s' % (self.productId, os.path.basename(product)[27:]))
                s3Bucket.upload_file(product, targetPath)
                current_progress['outputs']['VH'].append(targetPath)

            product = current_progress['files']['merged']
            targetPath = os.path.join(generatedProductPath, os.path.basename(product)) 
            s3Bucket.upload_file(product, targetPath)
            current_progress['outputs']['merged'] = targetPath

            with self.output().open('w') as out:
                out.write(json.dumps(current_progress))

    def output(self):
        outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
        return wc.getLocalStateTarget(outputFolder, 'transferedArd.json')

