import luigi
import os
import shutil
import process_s1_scene.common as wc

class ClearDataFolder(luigi.Task):
    productId = luigi.Parameter()
    pathRoots = luigi.DictParameter()
    processToS3 = luigi.BoolParameter(default=False)

    def run(self):
        folder = self.pathRoots["fileRoot"]

        if (os.path.exists(folder)):
            for f in os.listdir(folder):
                path = os.path.join(folder, f)

                if os.path.isfile(path):
                    os.unlink(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)

            if os.path.isfile(os.path.join(self.pathRoots["fileRoot"], "dem/cutline.geojson")):
                os.unlink(os.path.join(self.pathRoots["fileRoot"], "dem/cutline.geojson"))
            
            with self.output().open('w') as out:
                out.write('successfully cleared data folder')
        else:
            with self.output().open('w') as out:
                out.write('folder path doesn\'t exist, nothing to clear')

    def output(self):
        if self.processToS3:
            outputFolder = os.path.join(self.pathRoots["state-s3Root"], self.productId)
            return wc.getS3StateTarget(outputFolder, 'ClearDataFolder_SUCCESS')
        else:
            outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
            return wc.getLocalStateTarget(outputFolder, 'ClearDataFolder_SUCCESS')
