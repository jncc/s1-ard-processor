import luigi
import os
import logging
import json
import process_s1_scene.common as wc

from workflow_common.s3 import getPathFromS3Path, getBucketNameFromS3Path
from luigi.util import requires
from luigi import LocalTarget
from process_s1_scene.GenerateMetadata import GenerateMetadata

log = logging.getLogger('luigi-interface')

@requires(GenerateMetadata)
class RenameOutputFiles(luigi.Task):

    def run(self):
        
