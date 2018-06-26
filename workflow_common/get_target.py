import luigi
import logging
import os

from luigi import LocalTarget
from luigi.contrib.s3 import S3Target, S3Client

logger = logging.getLogger('luigi-interface')   

def getTarget(fileName, date, pathroots, useLocalTarget):
    workPath = ''
    if useLocalTarget:
        workPath = os.path.join(pathroots['localRoot'], date.strftime("%Y-%m-%d"))
    else:
        workPath = os.path.join(pathroots['s3Root'], date.strftime("%Y-%m-%d"))

    filePath = os.path.join(workPath, fileName)

    if useLocalTarget:
        logger.info("Use local target - writing to %s", filePath)
        return LocalTarget(filePath)
    else:
        client = S3Client()
        return S3Target(path=filePath, client=client)

def getProductTarget(fileName, pathroots, useLocalTarget):
    workPath = ''
    if useLocalTarget:
        workPath = pathroots['localRoot']
    else:
        workPath = pathroots['s3Root']

    filePath = os.path.join(workPath, fileName)

    if useLocalTarget:
        logger.info("Use local target - writing to %s", filePath)
        #todo temp line
        return LocalTarget(filePath)
        #return LocalTarget(filePath, format=luigi.format.Nop)
    else:
        client = S3Client()
        return S3Target(path=filePath, client=client, format=luigi.format.Nop)