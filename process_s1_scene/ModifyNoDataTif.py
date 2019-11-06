import luigi
import os
import re
import json
import logging
import process_s1_scene.common as wc
import subprocess
import re
from os.path import join as joinPath
from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.AddMergedOverviews import AddMergedOverviews
from process_s1_scene.ConfigureProcessing import ConfigureProcessing
from process_s1_scene.CheckFileExists import CheckFileExists

log = logging.getLogger('luigi-interface')

@requires(AddMergedOverviews, ConfigureProcessing)
class ModifyNoDataTif(luigi.Task):
    paths = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()

    def run(self):
        addMergedOverviewsInfo = {}
        with self.input()[0].open('r') as addMergedOverviews:
            addMergedOverviewsInfo = json.load(addMergedOverviews)

        configureProcessingInfo = {}
        with self.input()[1].open('r') as configureProcessing:
            configureProcessingInfo = json.load(configureProcessing) 

        tempOutputDir = configureProcessingInfo["parameters"]["s1_ard_temp_output_dir"]
        mergedFilePath = addMergedOverviewsInfo["overviewsAddedTo"]
        mergedFileName = os.path.splitext(os.path.basename(mergedFilePath))[0]

        tmpBand1Path = os.path.join(tempOutputDir, "tmp-band1.tif")
        tmpBand2Path = os.path.join(tempOutputDir, "tmp-band2.tif")
        tempStackedPath = os.path.join(tempOutputDir, "tmp.vrt")
        tempModePrePath = os.path.join(tempOutputDir, mergedFileName+"-mode-pre.tif")
        outputFileName = os.path.join(tempOutputDir, mergedFileName+".tif")
        
        cmdString1 = 'gdal_calc.py --debug -A {} --A_band=1 --outfile={} --calc="nan_to_num(A)" --NoDataValue=0 --overwrite' \
            .format(mergedFilePath, tmpBand1Path)
        cmdString2 = 'gdal_calc.py --debug -A {} --A_band=2 --outfile={} --calc="nan_to_num(A)" --NoDataValue=0 --overwrite' \
            .format(mergedFilePath, tmpBand2Path)
        cmdString3 = 'gdalbuildvrt -separate {} {} {}' \
            .format(tempStackedPath, tmpBand1Path, tmpBand2Path)
        cmdString4 = 'gdal_translate -co COMPRESS=DEFLATE -co BIGTIFF=YES -co TILED=YES -co BLOCKXSIZE=512 -co BLOCKYSIZE=512 {} {}' \
            .format(tempStackedPath, tempModePrePath)
        cmdString5 = 'gdaladdo -r nearest {} 2 4 8 16 32 64 128 256 512' \
            .format(tempModePrePath)
        cmdString6 = 'gdal_translate -co COMPRESS=DEFLATE -co BIGTIFF=YES -co TILED=YES -co BLOCKXSIZE=512 -co BLOCKYSIZE=512 --config GDAL_TIFF_OVR_BLOCKSIZE 512 -co COPY_SRC_OVERVIEWS=YES {} {}' \
            .format(tempModePrePath, outputFileName)

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
            wc.createTestFile(outputFileName)

        with self.output().open('w') as out:
            out.write(json.dumps({
                "modifyNoDataTif" : outputFileName
            }))
                
    def output(self):
        outputFile = os.path.join(self.paths["state"], 'ModifyNoDataTif.json')
        return LocalTarget(outputFile)
