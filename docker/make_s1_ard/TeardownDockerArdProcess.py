import os
import luigi
import boto3
import shutil
import json
import docker.make_s1_ard.common as wc

from luigi.util import inherits, requires
from docker.make_s1_ard.TransferArdToS3 import TransferArdToS3
from workflow_common.s3 import getPathFromS3Path, getBucketNameFromS3Path

@requires(TransferArdToS3)
class TeardownDockerArdProcess(luigi.Task):
    sourceFile = luigi.Parameter()
    productId = luigi.Parameter()
    pathRoots = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()
    
    def cleanFolder(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        os.makedirs(path)

    def run(self):
        output = {}
        current_progress = {}
        with self.input().open("r") as transfers:
            current_progress = json.loads(transfers.read())
        
        # Delete file on S3 if we didn't skip processing
        if not self.testProcessing:
            client = boto3.client('s3')
            response = client.delete_object(Bucket=getBucketNameFromS3Path(self.sourceFile), Key=getPathFromS3Path(self.sourceFile))
        
        with self.output().open('w') as out:
            out.write(json.dumps(current_progress))

    def output(self):
        outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
        return wc.getStateTarget(outputFolder, 'teardownArdProcess.json')