import luigi
import os
import re
import json
import logging
import shutil
import process_s1_scene.common as wc
from luigi.util import requires
from process_s1_scene.TransferFinalOutput import TransferFinalOutput

log = logging.getLogger('luigi-interface')

@requires(TransferFinalOutput)
class Cleanup(luigi.Task):
    sourceFile = luigi.Parameter()
    productId = luigi.Parameter()
    pathRoots = luigi.DictParameter()
    removeSourceFile = luigi.BoolParameter(default=False)

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
                out.write('successful teardown of data folder')
        else:
            with self.output().open('w') as out:
                out.write('folder path doesn\'t exist, nothing to teardown')

        if self.removeSourceFile:
            log.info('Removing source file from basket')
            os.unlink(os.path.join(self.pathRoots["basketPath"], os.path.basename(self.sourceFile)))

    def output(self):
        outputFolder = os.path.join(self.pathRoots["state-localRoot"], self.productId)
        return wc.getLocalStateTarget(outputFolder, 'Cleanup_SUCCESS')
