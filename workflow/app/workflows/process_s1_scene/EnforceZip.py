import luigi
import json
import os
import logging
import shutil
import glob

from luigi import LocalTarget

log = logging.getLogger('luigi-interface')

class EnforceZip(luigi.Task):
    paths = luigi.DictParameter()
    productName = luigi.Parameter()

    def run(self):
        productNameWithoutSuffix = self.productName.removesuffix(".SAFE") # make sure name has no .SAFE suffix
        zipFilename = productNameWithoutSuffix+".zip"
        zippedBasketPath = os.path.join(self.paths["input"], zipFilename)
        zippedWorkingPath = os.path.join(self.paths["working"], zipFilename)

        basketProductPath = ""
        if os.path.isfile(zippedBasketPath):
            basketProductPath = zippedBasketPath
            log.info("Input file is already a zip, copying to working area")
            shutil.copyfile(basketProductPath, zippedWorkingPath)
        else:
            unzippedBasketPathPattern = os.path.join(self.paths["input"], productNameWithoutSuffix + "*")
            unzippedWorkingPath = os.path.join(self.paths["working"], productNameWithoutSuffix)

            paths = glob.glob(unzippedBasketPathPattern)
            if len(paths) != 1:
                raise Exception(f"Something went wrong, found {len(paths)} matches for {unzippedBasketPathPattern}")
            
            basketProductPath = paths[0]
            log.info("Copying input folder to working area then zipping")
            shutil.copytree(basketProductPath, unzippedWorkingPath)

            safeDirName = productNameWithoutSuffix+".SAFE" # add it back in for zipping
            safePath = os.path.join(self.paths["working"], safeDirName)

            os.rename(unzippedWorkingPath, safePath)
            shutil.make_archive(zippedWorkingPath.removesuffix('.zip'), 'zip', self.paths["working"], safePath)
            shutil.rmtree(safePath)

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "productName": self.productName,
                "basketProductPath": basketProductPath,
                "zipFilePath": zippedWorkingPath
            }, indent=4))

    def output(self):
        outFile = os.path.join(self.paths['state'], 'EnforceZip.json')
        return LocalTarget(outFile)