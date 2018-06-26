import luigi
import make_s1_ard.common as wc
import json
import logging
from os.path import join
from datetime import datetime
from functional import seq
from luigi.util import requires
from pebble import ProcessPool, ProcessExpired
from make_s1_ard.CreateSourceList import CreateSourceList
from docker.make_s1_ard.TeardownDockerArdProcess import TeardownDockerArdProcess

from make_s1_ard.RunDocker import RunDocker

log = logging.getLogger('luigi-interface')

@requires(CreateSourceList)
class ProcessRawS1Files(luigi.Task):
    pathroots = luigi.DictParameter()
    testProcessing = luigi.BoolParameter()
    #awsParams = luigi.DictParameter()
    dockerParams = luigi.DictParameter()
    runDate = luigi.DateParameter(default=datetime.now())
    dockerPathroots = luigi.DictParameter()

    def processTaskOutput(self, output):
        with output.open('r') as to:
            o = json.load(to)
            return o

    def makeTask(self, rawProduct, taskOutputs):

        productId = self.resolveProductId(rawProduct)

        task = []
        # task = RunDocker(
        #     pathroots = self.pathroots,
        #     testProcessing = self.testProcessing,
        #     awsParams = self.awsParams,
        #     dockerParams = self.dockerParams,
        #     sourceFile = rawProduct,
        #     productId = productId,
        #     dockerPathroots = self.dockerPathroots
        # )

        # taskOutputs.append(task.output())

        return task

    def resolveProductId(self, filepath):
        """Resolve the product ID from the given filepath.

        Example:
        s3://bucket-name/sentinel/1/raw/S1A_IW_GRDH_1SDV_20170806T174119_20170806T174144_017806_01DD7A_62EF.zip
        would give a Product ID of:
        S1A_20171101_065336_065401
        """
        filepath = filepath.rsplit('/', 1)[-1]
        productId = '%s_%s_%s_%s' % (
            filepath[0:3], filepath[17:25], filepath[26:32], filepath[42:48])
        return productId

    def run(self):
        tasks = []
        taskOutputs = []

        # with self.input().open('r') as pfile:
        #     p = json.load(pfile)

        #     rawProducts = seq(p["rawProducts"])

        #     tasks = (rawProducts
        #              .map(lambda o: self.makeTask(o, taskOutputs))).to_list()

        # yield tasks

        # completed = (seq(taskOutputs)
        #              .map(lambda x: self.processTaskOutput(x))).to_list()

        # output = {
        #     "completedJobs": completed
        # }

        # with self.output().open('w') as out:
        #     out.write(json.dumps(output))

    def output(self):
        statePath = join(self.pathroots["state-s3Root"], self.runDate.strftime("%Y-%m-%d"))
        return wc.getStateTarget(statePath, "_success.json")
