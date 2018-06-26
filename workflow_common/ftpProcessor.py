import boto3
import logging
import ftplib
import os

from tempfile import NamedTemporaryFile
from os.path import join
from pebble import ProcessPool, ProcessExpired
from urllib.parse import urlparse
from ftplib import FTP

log = logging.getLogger('luigi-interface')   

def getProduct(jobSpec):
    f = urlparse(jobSpec["ftpUrl"])

    tempFileName = ""
    with NamedTemporaryFile(mode='wb+', delete=False) as temp:
        tempFileName = temp.name

        try:
            conn = FTP(f.netloc, jobSpec["ftpUser"], jobSpec["ftpPassword"])
            log.info("Binary download of %s", jobSpec["ftpUrl"])
            conn.retrbinary('RETR ' + f.path, temp.write)
            conn.close()
        except ftplib.all_errors as ftpError:
            log.warning("FTP transfer failed: %s", ftpError)

            result = {
                "productId": jobSpec["productId"],
                "location": "",
                "success": False
            }

            return result

    log.info("Temp file: %s", tempFileName)
    
    fileName = f.path.rsplit('/', 1)[1]
    s3TargetPath = jobSpec["targetPath"]

    targetUrl = join(s3TargetPath, fileName)
    log.info("Target Url %s", targetUrl)
    s = urlparse(targetUrl)

    s3 = boto3.client('s3')
    
    targetKey = s.path[1:]

    log.info("Upload file %s to bucket %s with key %s",tempFileName, s.netloc, targetKey)
    s3.upload_file(tempFileName, s.netloc, targetKey)
    log.info("upload complete")

    result = {
        "productId": jobSpec["productId"],
        "location": targetUrl,
        "success": True
    }
    
    os.remove(tempFileName)
    log.info("Removed temp file: %s", tempFileName)

    return result

def processJobs(jobs):
    with ProcessPool(max_workers=2) as pool:
        futureJobs = pool.map(getProduct, jobs)

        iterator = futureJobs.result()

        results = []
        #compile output urls and errors
        while True:
            try:
                result = next(iterator)
                results.append(result)
            except StopIteration:
                break
            except ProcessExpired as error:
                log.error("%s. Exit code: %d" % (error, error.exitcode))

        return results