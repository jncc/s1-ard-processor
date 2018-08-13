
from urllib.parse import urlparse, urlencode

def getBucketNameFromS3Path(path):
    if path.lower().startswith('s3://'):
        return path[5:(path[5:].find('/') + 5)]
    raise Exception('Not a valid s3 path')

def getPathFromS3Path(path):
    if path.lower().startswith('s3://'):
        return path[(path[5:].find('/') + 6):]
    raise Exception('Not a valid s3 path')

def getFilenameFromS3Path(path):
    if path.lower().startswith('s3://'):
         fileName = path.rsplit('/', 1)[1]
    raise Exception('Not a valid s3 path')