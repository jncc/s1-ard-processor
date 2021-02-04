import luigi
import logging
import zipfile
import os
import json
import process_s1_scene.common as wc
from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.GetConfiguration import GetConfiguration

@requires(GetConfiguration)
class GetManifest(luigi.Task):
    paths = luigi.DictParameter()

    def run(self):
        configuration = {}
        with self.input().open('r') as getConfiguration:
            configuration = json.load(getConfiguration)

        tempManifestFile = os.path.join(wc.createWorkingPath(configuration["workingRoot"], "manifest"),"source_manifest.txt")

        rawZip = zipfile.ZipFile(configuration["inputFilePath"], 'r')
        manifestPath = os.path.join(os.path.splitext(os.path.basename(configuration["inputFilePath"]))[0]+".SAFE", "manifest.safe")
        manifest = rawZip.read(manifestPath).decode("utf-8")
        
        with open(tempManifestFile,'w') as manifestFile:
            manifestFile.write(manifest)
  
        with self.output().open('w') as out:
            out.write(json.dumps({
                "manifestFile" : tempManifestFile
            }, indent=4))

    def output(self):
        outFile = os.path.join(self.paths["state"], 'GetManifest.json')
        return LocalTarget(outFile)
