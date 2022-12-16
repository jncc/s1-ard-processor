import luigi
import json
import os
import logging
import zipfile
import shutil

from luigi import LocalTarget

log = logging.getLogger('luigi-interface')

class EnforceZip(luigi.Task):
    paths = luigi.DictParameter()
    productName = luigi.Parameter()

    def run(self):
        zipFilename = self.productName+".zip"
        unzippedBasketPath = os.path.join(self.paths["input"], self.productName)
        zippedBasketPath = os.path.join(self.paths["input"], zipFilename)
        unzippedWorkingPath = os.path.join(self.paths["working"], self.productName)
        zippedWorkingPath = os.path.join(self.paths["working"], zipFilename)
        basketProductPath = ""

        if os.path.isfile(zippedBasketPath):
            basketProductPath = zippedBasketPath
            log.info("Input file is already a zip, copying to working area")
            shutil.copyfile(zippedBasketPath, zippedWorkingPath)
        else:
            basketProductPath = unzippedBasketPath
            log.info("Copying input folder to working area then zipping")
            shutil.copytree(unzippedBasketPath, unzippedWorkingPath)

            safeDirName = self.productName+".SAFE"
            safePath = os.path.join(self.paths["working"], safeDirName)

            zipf = zipfile.ZipFile(zippedWorkingPath, 'w', zipfile.ZIP_DEFLATED)
            try:
                os.rename(unzippedWorkingPath, safePath)
            except Exception as e:
                log.warning(f"renaming folder failed, folder probably already contains .SAFE extension: {e}")

            self.zipdir(safePath, zipf)
            zipf.close()
            shutil.rmtree(safePath)

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "productName": self.productName,
                "basketProductPath": basketProductPath,
                "zipFilePath": zippedWorkingPath
            }, indent=4))

    def zipdir(self, path, ziph):
        # ziph is zipfile handle
        len_path = len(path)
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                ziph.write(file_path, f"/{self.productName}.SAFE"+file_path[len_path:])

    def output(self):
        outFile = os.path.join(self.paths['state'], 'EnforceZip.json')
        return LocalTarget(outFile)