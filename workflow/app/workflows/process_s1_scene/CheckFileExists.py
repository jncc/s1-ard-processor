import luigi
import os
from luigi import LocalTarget

class CheckFileExists(luigi.ExternalTask):
    filePath = luigi.Parameter()

    #file size checking

    def output(self):
        return LocalTarget(self.filePath)