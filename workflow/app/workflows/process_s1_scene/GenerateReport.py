import luigi
import os
import csv
import json
import re

from luigi import LocalTarget
from luigi.util import requires

from process_s1_scene.TransferFinalOutput import TransferFinalOutput
from process_s1_scene.GetConfiguration import GetConfiguration

@requires(TransferFinalOutput, GetConfiguration)
class GenerateReport(luigi.Task):
    paths = luigi.DictParameter()
    reportFileName = luigi.Parameter()

    def parseInputName(self, productId):
        pattern = re.compile("S1([AB])\_IW_GRDH_1SDV\_((20[0-9]{2})([0-9]{2})([0-9]{2})T([0-9]{2})([0-9]{2})([0-9]{2}))")
        
        m = pattern.search(productId)

        satellite = "SENTINEL1%s" % m.group(1)
        captureDate = "%s-%s-%s" % (m.group(3), m.group(4), m.group(5)) 
        captureTime = "%s:%s:%s" % (m.group(6), m.group(7), m.group(8)) 

        return [productId, satellite, captureDate, captureTime]

    def run(self):
        transferFinalOutputInfo = {}
        with self.input()[0].open('r') as transferFinalOutput:
            transferFinalOutputInfo = json.load(transferFinalOutput)

        configuration = {}
        with self.input()[1].open('r') as getConfiguration:
            configuration = json.load(getConfiguration)

        inputProductName = os.path.basename(configuration["inputFilePath"]).split('.')[0]
        outputProductName = os.path.basename(transferFinalOutputInfo["outputPath"])

        reportLine = self.parseInputName(inputProductName)
        reportLine.append(outputProductName)

        reportFilePath = os.path.join(self.paths["report"], self.reportFileName)

        exists = os.path.isfile(reportFilePath)

        if exists:
            openMode = "a"
        else:
            openMode = "w"

        with open(reportFilePath, openMode, newline='') as csvFile: 
            writer = csv.writer(csvFile)

            if not exists:  
                writer.writerow(["ProductId", "Platform", "Capture Date", "Capture Time", "ARD ProductId"])

            writer.writerow(reportLine)            

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "reportFilePath" : reportFilePath,
                "reportLine" : reportLine
            }))
            
    def output(self):
        outputFile = os.path.join(self.paths["state"], "GenerateReport.json")
        return LocalTarget(outputFile)