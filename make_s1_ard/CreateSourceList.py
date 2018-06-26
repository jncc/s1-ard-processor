import luigi
import json
import logging
import boto3
import make_s1_ard.common as wc
from os.path import join

log = logging.getLogger('luigi-interface')


class CreateSourceList(luigi.Task):
    #s3Bucket = luigi.DictParameter()
    rawFileLocation = luigi.DictParameter()
    pathroots = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()
    runDate = luigi.DateParameter()

    def retrieveFileNamesFromS3Bucket(self, bucket, directory):
        """Retrieve a list of filenames for a directory in an S3 Bucket.

        Keyword arguments:
        bucket    -- the name of the S3 bucket 
        directory -- the directory to retrieve the list of files for.
        """
        # files = []

        # client = boto3.client('s3')
        # result = client.list_objects_v2(Bucket=bucket, Prefix=directory)

        # for idx, item in enumerate(result['Contents']):

        #     key = item.get('Key')
        #     if key:
        #         # Ignore root directory path
        #         if directory == key:
        #             continue

        #         filepath = 's3://' + bucket + '/' + key
        #         files.append(filepath)

        #         if idx > 1 and self.testProcessing:
        #             break


        # return files

    def logOutput(self, files):
        """Output information to the log regarding files ready for ARD processing."""

        totalFiles = len(files)
        if totalFiles > 0:
            log.info(
                'Identified the following %d file(s) for ARD processing:', totalFiles)
            for item in files:
                log.info(item)

    def run(self):
        files = []
        # files = self.retrieveFileNamesFromS3Bucket(
        #     self.s3Bucket, self.rawFileLocation)
        # self.logOutput(files)

        output = {
            "rawProducts": files
        }

        with self.output().open('w') as out:
            out.write(json.dumps(output))

    def output(self):
        statePath = join(self.pathroots["state-localRoot"], self.runDate.strftime("%Y-%m-%d"))
        return wc.getStateTarget(statePath, "RawSourceProducts.json")
