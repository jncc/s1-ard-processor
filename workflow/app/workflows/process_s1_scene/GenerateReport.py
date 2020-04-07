import luigi
import os, stat
import csv
import sqlite3
import json
import re

from datetime import datetime
from luigi import LocalTarget
from luigi.util import requires

from process_s1_scene.TransferFinalOutput import TransferFinalOutput
from process_s1_scene.VerifyWorkflowOutput import VerifyWorkflowOutput

@requires(TransferFinalOutput, VerifyWorkflowOutput)
class GenerateReport(luigi.Task):
    paths = luigi.DictParameter()
    reportFileName = luigi.Parameter()
    dbFileName = luigi.OptionalParameter(default=None)
    dbConnectionTimeout = luigi.IntParameter(default=60000)

    def parseInputName(self, productId):
        pattern = re.compile("S1([AB])\_IW_GRDH_1SDV\_((20[0-9]{2})([0-9]{2})([0-9]{2})T([0-9]{2})([0-9]{2})([0-9]{2}))")
        
        m = pattern.search(productId)

        satellite = "1%s" % m.group(1)
        captureDate = "%s-%s-%s" % (m.group(3), m.group(4), m.group(5)) 
        captureTime = "%s:%s:%s" % (m.group(6), m.group(7), m.group(8)) 

        return [productId, satellite, captureDate, captureTime]

    def writeToCsv(self, reportLine, reportFilePath):
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

    def writeToDb(self, reportLine, dbPath):
        conn = sqlite3.connect(dbPath, timeout=self.dbConnectionTimeout)

        c = conn.cursor()
        c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='s1ArdProducts' ''')

        if c.fetchone()[0] != 1: 
            c.execute('''CREATE TABLE s1ArdProducts
                        (productId text, platform text, captureDate text, CaptureTime text, ardProductId text, recordTimestamp text)''')
            
            conn.commit()

        sql = "INSERT INTO s1ArdProducts VALUES (?,?,?,?,?,?)"

        recordTimestamp = str(datetime.now())
        row = (reportLine[0], reportLine[1], reportLine[2], reportLine[3], reportLine[4], recordTimestamp)

        c.execute(sql, row)

        conn.commit()
        conn.close()

    def run(self):
        transferFinalOutputInfo = {}
        with self.input()[0].open('r') as stateFile:
            transferFinalOutputInfo = json.load(stateFile)

        verifyWorkflowOutput = {}
        with self.input()[1].open('r') as stateFile:
            verifyWorkflowOutput = json.load(stateFile)

        inputProductName = verifyWorkflowOutput["sourceProductId"]
        outputProductName = os.path.basename(transferFinalOutputInfo["outputPath"])

        reportLine = self.parseInputName(inputProductName)
        reportLine.append(outputProductName)

        reportFilePath = os.path.join(self.paths["report"], self.reportFileName)

        if self.dbFileName:
            dbFilePath = os.path.join(self.paths["database"], self.dbFileName)
            dbExists = os.path.exists(dbFilePath)

            self.writeToDb(reportLine, dbFilePath)

            #If the file has just been created make it user and group writable.
            if not dbExists:
                os.chmod(dbFilePath, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP)

        self.writeToCsv(reportLine, reportFilePath)

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "reportFilePath" : reportFilePath,
                "reportLine" : reportLine
            }))
            
    def output(self):
        outputFile = os.path.join(self.paths["state"], "GenerateReport.json")
        return LocalTarget(outputFile)