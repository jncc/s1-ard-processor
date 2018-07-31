
from datetime import datetime
from os.path import basename, join
from luigi.contrib.s3 import S3Target, S3Client
from workflow_common.s3 import getPathFromS3Path
from luigi import LocalTarget

def getTarget(key):
    client = S3Client()
    return S3Target(path=key, client=client)

def getStateTarget(targetPath, fileName):
    targetKey = join(targetPath, fileName)
    return getTarget(targetKey)

def getLocalStateTarget(targetPath, fileName):
    targetKey = join(targetPath, fileName)
    return LocalTarget(targetKey)

def getProductIdFromLocalSourceFile(sourceFile):
    productFilename = basename(sourceFile)
    return '%s_%s_%s_%s' % (productFilename[0:3], productFilename[17:25], productFilename[26:32], productFilename[42:48])

def getProductIdFromSourceFile(sourceFile):
    productFilename = basename(getPathFromS3Path(sourceFile))
    return '%s_%s_%s_%s' % (productFilename[0:3], productFilename[17:25], productFilename[26:32], productFilename[42:48])

def getProductPatternFromSourceFile(sourceFile):
    productFilename = basename(getPathFromS3Path(sourceFile))
    return '%s_%s%s%s_%s_%s' % (productFilename[0:3], productFilename[23:25], datetime.strptime(productFilename[21:23], '%m').strftime('%b'), productFilename[17:21], productFilename[26:32], productFilename[42:48])

