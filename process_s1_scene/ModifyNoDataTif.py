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
        with self.input().open('r') as addMergedOverviews:
            addMergedOverviewsInfo = json.load(addMergedOverviews)

        mergedFilePath = addMergedOverviewsInfo["overviewsAddedTo"]
        mergedFileName = os.path.splitext(os.path.basename(mergedFilePath))[0]
        outputFileName = os.path.join(self.paths["working"], mergedFileName+"-mode.tif")
        
        cmdString1 = 'gdal_calc.py --debug -A {} --A_band=1 --outfile=tmp-band1.tif --calc=nan_to_num(A) --NoDataValue=0 --overwrite' \
            .format(mergedFilePath)
        cmdString2 = 'gdal_calc.py --debug -A {} --A_band=2 --outfile=tmp-band2.tif --calc=nan_to_num(A) --NoDataValue=0 --overwrite' \
            .format(mergedFilePath)
        cmdString3 = 'gdalbuildvrt -separate temp.vrt tmp-band1.tif tmp-band2.tif'
        cmdString4 = 'gdal_translate -co COMPRESS=DEFLATE -co BIGTIFF=YES -co TILED=YES -co BLOCKXSIZE=512 -co BLOCKYSIZE=512 temp.vrt {}-mode-pre.tif' \
            .format(mergedFileName)
        cmdString5 = 'gdaladdo -r nearest {}-mode-pre.tif 2 4 8 16 32 64 128 256 512' \
            .format(mergedFileName)
        cmdString6 = 'gdal_translate -co COMPRESS=DEFLATE -co BIGTIFF=YES -co TILED=YES -co BLOCKXSIZE=512 -co BLOCKYSIZE=512 --config GDAL_TIFF_OVR_BLOCKSIZE 512 -co COPY_SRC_OVERVIEWS=YES {}-mode-pre.tif {}-mode.tif' \
            .format(mergedFileName, outputFileName)

        if not self.testProcessing:
            log.info('Running commands to modify no data values and perform cloud optimising')
            try:
                subprocess.check_output(cmdString1, shell=True)
                subprocess.check_output(cmdString2, shell=True)
                subprocess.check_output(cmdString3, shell=True)
                subprocess.check_output(cmdString4, shell=True)
                subprocess.check_output(cmdString5, shell=True)
                subprocess.check_output(cmdString6, shell=True)
            except subprocess.CalledProcessError as e:
                errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
                log.error(errStr)
                raise RuntimeError(errStr)
        else:
            wc.createTestFile(outputFileName, "TEST_FILE")

        with self.output().open('w') as out:
            out.write(json.dumps({
                "modifyNoDataTif" : outputFileName
            }))
                
    def output(self):
        outputFile = os.path.join(self.paths["state"], 'ModifyNoDataTif.json')
        return LocalTarget(outputFile)
