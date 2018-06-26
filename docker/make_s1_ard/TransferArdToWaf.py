import luigi
import os
import re
import json
import logging
import docker.make_s1_ard.common as wc
from luigi.util import requires
from docker.make_s1_ard.AddMergedOverviews import AddMergedOverviews
from shutil import copyfile

log = logging.getLogger('luigi-interface')

@requires(AddMergedOverviews)
class TransferArdToWaf(luigi.Task):
    sourceFile = luigi.Parameter()
    pathRoots = luigi.DictParameter()
    productId = luigi.Parameter(default=False)

    def run(self):
        with self.input().open('r') as processed:

            current_progress = json.loads(processed.read())
            current_progress['outputs'] = {
                'VV': [],
                'VH': [],
                'merged' : ''
            }

            generatedProductPath = self.getPathFromProductId(self.pathRoots["wafRoot"], self.productId)

            self.copyPolarisationFiles("VH", generatedProductPath, current_progress)
            self.copyPolarisationFiles("VV", generatedProductPath, current_progress)

            product = current_progress['files']['merged']
            targetPath = os.path.join(generatedProductPath, os.path.basename(product)) 
            copyfile(product, targetPath)
            current_progress['outputs']['merged'] = targetPath

            with self.output().open('w') as out:
                out.write(json.dumps(current_progress))

    def output(self):
        outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
        return wc.getLocalStateTarget(outputFolder, 'transferedArdToWaf.json')

    def getPathFromProductId(self, root, productId):
        year = productId[4:8]
        month = productId[8:10]
        day = productId[10:12]

        return os.path.join(os.path.join(os.path.join(os.path.join(root, year), month), day), productId)

    def copyPolarisationFiles(self, polarisation, generatedProductPath, current_progress):
        p = re.compile("^[\w\/-]+_Gamma0_APGB_OSGB1936_RTC_SpkRL_dB.tif")

        polarisationPath = os.path.join(generatedProductPath, polarisation)
        if not os.path.exists(polarisationPath):
            os.makedirs(polarisationPath)

        for product in current_progress['files'][polarisation]:
            if p.match(product):
                targetPath = os.path.join(polarisationPath, '%s%s' % (self.productId, os.path.basename(product)[27:]))
                copyfile(product, targetPath)
                current_progress['outputs'][polarisation].append(targetPath)
