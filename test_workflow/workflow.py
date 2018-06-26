import luigi
import logging
import os
from luigi.util import inherits, requires

logger = logging.getLogger('luigi-interface') 

class CentralSchedulerTestAncestorTask(luigi.Task):
    def run(self):
        with self.output().open('w') as test:
            test.write('successfull')

    def output(self):
        outfile = os.path.join(self.localFilesystemRoot, 'test-workflow-s1.txt')
        return luigi.LocalTarget(outfile)

@requires(CentralSchedulerTestAncestorTask)
class TestCentralScheduler(luigi.Task):
    localFilesystemRoot = luigi.Parameter()

    def requires(self):
        return CentralSchedulerTestAncestorTask(self.localFilesystemRoot)

    def run(self):
        with self.input().open('r') as test, self.output().open('w') as test_out:
            test_out.write(test.read())
    
    def output(self):
        outfile = os.path.join(self.localFilesystemRoot, 'test-workflow-s2.txt')
        return luigi.LocalTarget(outfile)


