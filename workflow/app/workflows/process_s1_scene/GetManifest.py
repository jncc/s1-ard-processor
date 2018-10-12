import luigi
import logging
import zipfile
import os
import json
from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.GetInputFileInfo import GetInputFileInfo

@requires(GetInputFileInfo)
class GetManifest(luigi.Task):
    paths = luigi.DictParameter()

    def run(self):
        inputFileInfo = {}
        with self.input().open('r') as getInputFileInfo:
            inputFileInfo = json.load(getInputFileInfo)

        rawZip = zipfile.ZipFile(inputFileInfo["inputFilePath"], 'r')
        manifestPath = os.path.join(os.path.splitext(os.path.basename(inputFileInfo["inputFilePath"]))[0]+".SAFE", "manifest.safe")
        manifest = rawZip.read(manifestPath).decode("utf-8")
       
        with self.output().open('w') as out:
            out.write(manifest)

    def output(self):
        outFile = os.path.join(self.paths['working'], 'source_manifest.txt')
        return LocalTarget(outFile)
