import luigi
import os
import docker.make_s1_ard.common as wc
from luigi.util import requires
from docker.make_s1_ard.ClearDataFolder import ClearDataFolder

@requires(ClearDataFolder)
class InitialiseDataFolder(luigi.Task):
    productId = luigi.Parameter()
    pathRoots = luigi.DictParameter()
    processToS3 = luigi.BoolParameter(default=False)
    
    def makePath(self, newPath):
        if not os.path.exists(newPath):
            os.makedirs(newPath)

    def run(self):
        folders = ["raw_zip",
                    "raw",
                    "output",
                    "zip_processed",
                    "dem",
                    "processed"]
        
        for f in folders:
            newPath = os.path.join(self.pathRoots["fileRoot"], f)
            self.makePath(newPath)

        with self.output().open('w') as out:
            out.write('successfully initialised data folder')

    def output(self):
        if self.processToS3:
            outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
            return wc.getS3StateTarget(outputFolder, 'InitialiseDataFolder_SUCCESS')
        else:
            outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
            return wc.getLocalStateTarget(outputFolder, 'InitialiseDataFolder_SUCCESS')

        


