import luigi
import os
import re
import json
import logging
import process_s1_scene.common as wc
from luigi.util import inherits
from process_s1_scene.ProcessRawToArd import ProcessRawToArd
from process_s1_scene.ReprojectToOSGB import ReprojectToOSGB
from process_s1_scene.MergeBands import MergeBands
from process_s1_scene.AddMergedOverviews import AddMergedOverviews
 
from shutil import copyfile

log = logging.getLogger('luigi-interface')

@inherits(ProcessRawToArd)
@inherits(ReprojectToOSGB)
@inherits(MergeBands)
@inherits(AddMergedOverviews)
class TransferFinalOutput(luigi.Task):
    paths = luigi.DictParameter()
    productId = luigi.Parameter(default=False)

    def requires(self):
        t = []
        t.append(self.clone(ProcessRawToArd))
        t.append(self.clone(ReprojectToOSGB))
        t.append(self.clone(MergeBands))
        t.append(self.clone(AddMergedOverviews))
        return t

    def run(self):
        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "test" : "test" 
            }))

    def output(self):
        outFile = os.path.join(self.paths['state'], 'TransferFinalOutput.json')
        return LocalTarget(outFile)
    #     processRawToArdInfo = {}
    #     with self.input()[0].open('r') as processRawToArd:
    #         processRawToArdInfo = json.load(processRawToArd)

    #     current_progress['outputs'] = {
    #         'VV': [],
    #         'VH': [],
    #         'merged' : ''
    #     }

    #     generatedProductPath = self.getPathFromProductId(self.paths["output"], self.productId)

    #     self.copyPolarisationFiles("VH", generatedProductPath, current_progress)
    #     self.copyPolarisationFiles("VV", generatedProductPath, current_progress)

    #     product = current_progress['files']['merged']
    #     targetPath = os.path.join(generatedProductPath, os.path.basename(product)) 
    #     copyfile(product, targetPath)
    #     current_progress['outputs']['merged'] = targetPath

    #     with self.output().open('w') as out:
    #         out.write(json.dumps(current_progress))

    # def output(self):
    #     outputFolder = os.path.join(self.paths["state-localRoot"], self.productId)
    #     return wc.getLocalStateTarget(outputFolder, 'transferFinalOutput.json')

    # def getPathFromProductId(self, root, productId):
    #     year = productId[4:8]
    #     month = productId[8:10]
    #     day = productId[10:12]

    #     return os.path.join(os.path.join(os.path.join(os.path.join(root, year), month), day), productId)

    # def copyPolarisationFiles(self, polarisation, generatedProductPath, current_progress):
    #     p = re.compile(self.outputFile)

    #     polarisationPath = os.path.join(generatedProductPath, polarisation)
    #     if not os.path.exists(polarisationPath):
    #         os.makedirs(polarisationPath)

    #     for product in current_progress['files'][polarisation]:
    #         if p.match(product):
    #             targetPath = os.path.join(polarisationPath, '%s%s' % (self.productId, os.path.basename(product)[27:]))
    #             copyfile(product, targetPath)
    #             current_progress['outputs'][polarisation].append(targetPath)
