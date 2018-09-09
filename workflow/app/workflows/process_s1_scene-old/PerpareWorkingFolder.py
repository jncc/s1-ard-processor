import luigi
import os
import process_s1_scene.common as wc
from luigi.util import requires
from process_s1_scene.ClearDataFolder import ClearDataFolder

class PrepareWorkingFolder(luigi.Task):
    productId = luigi.Parameter()
    paths = luigi.DictParameter()
    processToS3 = luigi.BoolParameter(default=False)
    

    def makePath(self, newPath):
        if not os.path.exists(newPath):
            os.makedirs(newPath)

    def clearFolder(self, folder):
        for f in os.listdir(folder):
            path = os.path.join(folder, f)

            if os.path.isfile(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)

    def run(self):

        folders = [ "zip_processed",
                    "temp",
                    "dem",
                    "output"]
                
        for f in folders:
            path os.path.join("/working", f)

            if (os.path.exists(f):
                self.clearFolder()
            else:
                self.makePath(f)
                
        with self.output().open('w') as o:
            o.write('\{\}')

    def output(self):
        outFile = os.path.join(self.paths['state'], 'PrepareWorkingFolder_SUCCESS.json')
        return LocalTarget(outFile)