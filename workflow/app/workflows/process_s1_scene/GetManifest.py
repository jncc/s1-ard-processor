import luigi
import logging
import zipfile
import os
import json
import process_s1_scene.common as wc
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

        tempManifestFile = os.path.join(wc.createWorkingPath(self.paths["working"], "manifest"),"source_manifest.txt")

        rawZip = zipfile.ZipFile(inputFileInfo["inputFilePath"], 'r')
        manifestPath = os.path.join(os.path.splitext(os.path.basename(inputFileInfo["inputFilePath"]))[0]+".SAFE", "manifest.safe")
        manifest = rawZip.read(manifestPath).decode("utf-8")
        
        with open(tempManifestFile,'w') as manifestFile:
            manifestFile.write(manifest)
  
        with self.output().open('w') as out:
            out.write(json.dumps({
                "manifestFile" : tempManifestFile
            }))

    def output(self):
        outFile = os.path.join(self.paths["state"], 'GetManifest.json')
        return LocalTarget(outFile)
