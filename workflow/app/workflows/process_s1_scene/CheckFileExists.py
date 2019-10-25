import luigi
import os
import logging
from luigi import LocalTarget

log = logging.getLogger('luigi-interface')

class CheckFileExists(luigi.ExternalTask):
    filePath = luigi.Parameter()

    def output(self):
        if not os.path.getsize(self.filePath) > 0:
            raise Exception("file {0} has no size".format(self.filePath))
            
        return LocalTarget(self.filePath)