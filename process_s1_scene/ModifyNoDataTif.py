import luigi
import os
import re
import json
import logging
import process_s1_scene.common as wc
import subprocess
import re
from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.AddMergedOverviews import AddMergedOverviews
from os.path import join as joinPath

log = logging.getLogger('luigi-interface')

@requires(AddMergedOverviews)
class ModifyNoDataTif(luigi.Task):
    paths = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()

    def run(self):
        addMergedOverviewsInfo = {}
        with self.input()[2].open('r') as addMergedOverviews:
            addMergedOverviewsInfo = json.load(addMergedOverviews)

        mergedFile = addMergedOverviewsInfo["overviewsAddedTo"]
        cmdString1 = 'gdal_calc.py --debug -A {} --A_band=1 --outfile=tmp-band1.tif --calc=nan_to_num(A) --NoDataValue=0 --overwrite' \
            .format(mergedFile) 

        if not self.testProcessing:
            log.info('Creating merged product from Gamma VH & VV bands')
            try:
                subprocess.check_output(cmdString1, shell=True) 
            except subprocess.CalledProcessError as e:
                errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                log.error(errStr)
                raise RuntimeError(errStr)
        else:
            wc.createTestFile(outputFile, "TEST_FILE")

        with self.output().open("w") as outFile:
            outFile.write(json.dumps(state))
                
    def output(self):
        outputFile = os.path.join(self.paths["state"], 'ModifyNoDataTif.json')
        return LocalTarget(outputFile)
