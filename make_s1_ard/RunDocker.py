
import luigi
import logging
import subprocess
import json
import make_s1_ard.common as wc
from os.path import join

log = logging.getLogger('luigi-interface')

#todo maybe use the docker extension for luigi: https://luigi.readthedocs.io/en/stable/api/luigi.contrib.docker_runner.html
class RunDocker(luigi.Task):
    pathroots = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()
    awsParams = luigi.DictParameter()
    dockerParams = luigi.DictParameter()
    sourceFile = luigi.Parameter()
    outputFile = luigi.Parameter()
    productId = luigi.Parameter()
    dockerPathroots = luigi.DictParameter()

    def run(self):
        extraParams = ""

        if self.testProcessing:
            extraParams = "--testProcessing"


        dpr = {"state-s3Root": self.dockerPathroots["state-s3Root"],
            "product-s3Root": self.dockerPathroots["product-s3Root"],
            "source-dem-s3-path": self.dockerPathroots["source-dem-s3-path"],
            "local-dem-path": self.dockerPathroots[ "local-dem-path"]}

        #params
        # AWS Access key
        # AWS Secret key
        # host data path
        # host dem path
        # product id
        # source file url
        # output file regex
        # process to S3 bool
        # luigi scheduler host ip
        # extra luigi params

        cmd = "docker run -e AWS_ACCESS_KEY_ID={} -e AWS_SECRET_ACCESS_KEY={} -v {}:/data/sentinel/1 -v {}:/data/dem {} --scheduler-host {} --productId {} --sourceFile {} --outputFile {} --processToS3=True --pathRoots '{}' {}" \
                .format(self.awsParams["access-key-id"], 
                    self.awsParams["secret-access-key"],
                    self.dockerParams["host-data-path"],
                    self.dockerParams["host-dem-path"],
                    self.dockerParams["image-name"],
                    self.dockerParams["scheduler-host"],
                    self.productId,
                    self.sourceFile,
                    self.outputFile,
                    json.dumps(dpr),
                    extraParams)

        try:
            subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                shell=True)
        except subprocess.CalledProcessError as e:
            errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
            log.error(errStr)
            raise RuntimeError(errStr)
        
    def output(self):
        outputFolder = join(self.pathroots["state-s3Root"], self.productId)
        return wc.getStateTarget(outputFolder, "_run_success.json")