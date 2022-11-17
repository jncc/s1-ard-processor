import luigi
import zipfile
import os
import json
import logging
import re
from luigi import LocalTarget
from luigi.util import requires
from process_s1_scene.GetConfiguration import GetConfiguration

log = logging.getLogger('luigi-interface')

@requires(GetConfiguration)
class GetRFIInfo(luigi.Task):
    paths = luigi.DictParameter()

    def run(self):
        configuration = {}
        with self.input().open('r') as getConfiguration:
            configuration = json.load(getConfiguration)

        inputZip = configuration["inputFilePath"]

        filesInZip = zipfile.ZipFile(inputZip, 'r').namelist()

        # match the VV and VH RFI filenames
        # e.g. S1A_IW_GRDH_1SDV_20220826T175933_20220826T175958_044727_055726_B7DC.SAFE/annotation/rfi/rfi-s1a-iw-grd-vh-20220826t175933-20220826t175958-044727-055726-002.xml
        pattern = '(\/annotation\/rfi\/rfi-s1a-iw-grd-[vv][vh]-[a-zA-Z0-9-]*.xml)' 

        matches = []
        for file in filesInZip:
            match = re.search(pattern, file)
            if match:
                matches.append(match.group(0))
        
        vvFile = ''
        vhFile = ''
        if not matches:
            log.warn('No RFI metadata found in ESA data, this should be present in newer ESA data only')
        else:
            rfiFileCount = len(matches)
            if rfiFileCount is not 2:
                raise Exception(f'Found {rfiFileCount} RFI metadata files in {inputZip}, expected 2')

            if 'vv' in matches[0]:
                vvFile = matches[0]
                vhFile = matches[1]
            else:
                vvFile = matches[1]
                vhFile = matches[0]

        rfiDetectedVV = 'N/A'
        rfiDetectedVH = 'N/A'
        rfiMitigationAppliedVV = 'N/A'
        rfiMitigationAppliedVH = 'N/A'

        log.info(f'vvFile: {vvFile}')
        log.info(f'vhFile: {vhFile}')

        if vvFile and vhFile:
            # todo extract the files and get the values
  
        with self.output().open('w') as out:
            out.write(json.dumps({
                "rfiDetectedVV": rfiDetectedVV,
                "rfiDetectedVH": rfiDetectedVH,
                "rfiMitigationAppliedVV": rfiMitigationAppliedVV,
                "rfiMitigationAppliedVH": rfiMitigationAppliedVH
            }, indent=4))

    def output(self):
        outFile = os.path.join(self.paths["state"], 'GetRFIInfo.json')
        return LocalTarget(outFile)
