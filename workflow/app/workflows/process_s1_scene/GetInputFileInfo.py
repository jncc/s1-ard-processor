import luigi
import os
import process_s1_scene.common as wc

from process_s1_scene.CheckFileExists import CheckFileExists

class GetIntputFileInfo(luigi.Task):
    paths = luigi.DictParameter()
    productId = luigi.Parameter()
    inputFileName = luigi.Parameter()

    def run(self):
        inputFilePath = os.path.join(self.paths["input"], self.inputFileName)

        check = CheckFileExists(inputFilePath)
        yield check

        with self.output().open("w") as outFile:
            outFile.write(json.dumps({
                "inputFilePath" : inputFilePath,
                "productPattern" : wc.getProductPatternFromSourceFile(self.inputFileName)
            }))

    def output(self):
        outFile = os.path.join(self.paths['state'], 'GetIntputFileInfo.json')
        return LocalTarget(outFile)