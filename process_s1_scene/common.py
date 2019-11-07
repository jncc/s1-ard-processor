import logging
import luigi
import os
import re
import shutil
from datetime import datetime
from os.path import basename, join
from luigi.contrib.s3 import S3Target, S3Client
from workflow_common.s3 import getBucketNameFromS3Path, getPathFromS3Path
from luigi import LocalTarget

def getS3Target(key):
    client = S3Client()
    return S3Target(path=key, client=client)

def getLocalTarget(key):
    return LocalTarget(key)

def getLocalStateTarget(targetPath, fileName):
    targetKey = join(targetPath, fileName)
    return getLocalTarget(targetKey)

def getS3StateTarget(targetPath, fileName):
    targetKey = join(targetPath, fileName)
    return getS3Target(targetKey)

def getProductIdFromSourceFile(sourceFile):
    productFilename = basename(sourceFile)
    return '{0}_{1}_{2}_{3}'.format(productFilename[0:3], productFilename[17:25], productFilename[26:32], productFilename[42:48])

def getProductPatternFromSourceFile(sourceFile):
    productFilename = basename(sourceFile)
    return '{0}_{1}{2}{3}_{4}_{5}'.format(productFilename[0:3], productFilename[23:25], datetime.strptime(productFilename[21:23], '%m').strftime('%b'), productFilename[17:21], productFilename[26:32], productFilename[42:48])

def createTestFile(outputfile):
    os.makedirs(os.path.dirname(outputfile), exist_ok=True)
    with open(outputfile, 'w') as f:
        f.write('TEST_FILE')


def createWorkingPath(workingPathRoot, workingPath): 
    newPath = os.path.join(workingPathRoot, workingPath)

    if (os.path.exists(newPath)):
        #empty out the structure
        for f in os.listdir(newPath):
            path = os.path.join(newPath, f)

            if os.path.isfile(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
    else:
        os.makedirs(newPath)

    return newPath

def getOutputFileName(inputFileName, polarisation, manifest, filenameDemData, filenameSrs):
    inputFileSegments = inputFileName.split('_')

    a = inputFileSegments[0]
    b = inputFileSegments[4].split('T')[0] #date part

    c = ''
    absOrbitNo = int(inputFileSegments[6])
    if a == "S1A":
        c = str(((absOrbitNo - 73) % 175) + 1)
    elif a == "S1B":
        c = str(((absOrbitNo - 27) % 175) + 1)
    else:
        msg = "Invalid input file name, should begin S1A or S1B not {0}".format(a)
        raise Exception(msg)

    pattern = "<s1:pass>(.+)<\/s1:pass>"
    orbitDirectionRaw = re.search(pattern, manifest).group(1)

    d = ''
    if orbitDirectionRaw == "ASCENDING":
        d = "asc"
    elif orbitDirectionRaw == "DESCENDING":
        d = "desc"
    else:
        msg = "Invalid orbit direction in manifest, must be ASCENDING or DESCENDING but is {0}".format(orbitDirectionRaw)
        raise Exception(msg)

    e = inputFileSegments[4].split('T')[1]
    f = inputFileSegments[5].split('T')[1]
    g = polarisation
    h = filenameDemData
    i = filenameSrs

    return "{0}_{1}_{2}_{3}_{4}_{5}_{6}_G0_{7}_{8}_RTCK_SpkRL.tif".format(a,b,c,d,e,f,g,h,i)


            