import luigi
import json
import os
import logging
import zipfile
import process_s1_scene.common as wc

from luigi import LocalTarget
from process_s1_scene.CheckFileExists import CheckFileExists

log = logging.getLogger('luigi-interface')

class EnforceZip(luigi.Task):
    paths = luigi.DictParameter()
    productName = luigi.Parameter()

    def run(self):
        unzippedFilePath = os.path.join(self.paths["input"], self.productName)

        if os.path.isfile(unzippedFilePath+".zip"):
            log.info("Input file is already a zip, nothing to do")
        else:
            log.info("Zipping input folder")
            zipf = zipfile.ZipFile(unzippedFilePath+".zip", 'w', zipfile.ZIP_DEFLATED)
            try:
                os.rename(unzippedFilePath, unzippedFilePath+".SAFE")
            except Exception as e:
                log.warning(f"renaming folder failed, folder probably already contains .SAFE extension: {e}")

            self.zipdir(unzippedFilePath+".SAFE", zipf)
            zipf.close()

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "productName": self.productName,
                "zippedFileName": self.productName+".zip"
            }))

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