import boto3
import botocore
import luigi
import os
import logging
import json
import docker.make_s1_ard.common as wc

from workflow_common.s3 import getPathFromS3Path, getBucketNameFromS3Path
from luigi.util import requires
from luigi import LocalTarget
from docker.make_s1_ard.InitialiseDataFolder import InitialiseDataFolder
from docker.make_s1_ard.common import getFullDEMPath

log = logging.getLogger('luigi-interface')

@requires(InitialiseDataFolder)
class FetchSourceDEM(luigi.Task):
    sourceFile = luigi.Parameter()
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter()
    processToS3 = luigi.BoolParameter(default=False)

    def run(self):
        if self.processToS3:
            s3 = boto3.resource('s3')
            s3.Bucket(getBucketNameFromS3Path(self.pathRoots["source-dem-s3-path"])).download_file(getPathFromS3Path(self.pathRoots["source-dem-s3-path"]), getFullDEMPath(self.pathRoots['local-dem-path']))

    def output(self):
        return LocalTarget(getFullDEMPath(self.pathRoots['local-dem-path']))
        