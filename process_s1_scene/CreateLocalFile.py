import luigi
import process_s1_scene.common as wc
from luigi import LocalTarget

class CreateLocalFile(luigi.Task):
    filePath = luigi.Parameter()
    content = luigi.Parameter()

    def run(self):
        wc.createTestFile(self.filePath, self.content)

    def output(self):
        return LocalTarget(self.filePath)