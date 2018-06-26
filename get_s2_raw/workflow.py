import luigi
import datetime
import os
import json
import logging
import pprint
import workflow_common as wc
import feedparser
import urllib
import workflow_common.polygon as polygon
import copy

from pprint import PrettyPrinter

from functional import seq
from datetime import timedelta, datetime
from dateutil import parser as dateparser
from luigi import LocalTarget
from luigi.util import inherits, requires
from math import ceil
from urllib.parse import urlparse, urlencode

pp = PrettyPrinter()

log = logging.getLogger('luigi-interface')   


def getStatePaths(pathRoutes):
    paths = {
                "localRoot": pathRoutes["state-localRoot"],
                "s3Root": pathRoutes["state-s3Root"]
            }

    return paths

class GetAvailableProductsFromLastRun(luigi.ExternalTask):
    useLocalTarget = luigi.BoolParameter()
    runDate = luigi.DateParameter()
    pathroots = luigi.DictParameter()

    def output(self): 
        lastDate = self.runDate - timedelta(days=1)
        return wc.getTarget('AvailableProducts.json', lastDate, getStatePaths(self.pathroots), self.useLocalTarget)

class GetAcquriredProductsFromLastRun(luigi.ExternalTask):
    useLocalTarget = luigi.BoolParameter()
    runDate = luigi.DateParameter()
    pathroots = luigi.DictParameter()

    def output(self):
        lastDate = self.runDate - timedelta(days=1)
        return wc.getTarget('S2RawProducts.json', lastDate, getStatePaths(self.pathroots), self.useLocalTarget)

CEDA_OPENSEARCH_URL = 'http://opensearch.ceda.ac.uk/opensearch/atom?'
@requires(GetAvailableProductsFromLastRun)
class GetRawDataFeed(luigi.Task):
    useLocalTarget = luigi.BoolParameter()
    runDate = luigi.DateParameter()
    pathroots = luigi.DictParameter()

    def getBaseQuery(self):

        query = {
            "mission": "sentinel-2",
            "maxCloudCoverPercentage": 75,
            "geometry": polygon.getSearchPolygon(),
            "startDate": None,
            "endDate": None
        }

        #defaults to the rundateT00:00:00 - queryWindowOffset
        endDate = datetime.combine(self.runDate, datetime.min.time())
        query["endDate"] = endDate.isoformat()

        with self.input().open('r') as lastRun:
            data = json.load(lastRun)
            d = seq(data["products"])

            if d.empty():
                # if we got nothing last time query from the last window start to the current end
                query["startDate"] = data["queryWindow"]["start"]
            else:
                # go from last end aquisition date
                query["startDate"] = (d
                    .select(lambda x: dateparser.parse(x["endCapture"]))
                    .max()).isoformat()

        return query

    def queryCEDA(self, query):
        qs = urlencode(query)
        url = CEDA_OPENSEARCH_URL + qs

        log.info(url)

        d = feedparser.parse(url)

        if d.bozo:
            log.exception("Read CEDA feed failed")
            raise TypeError(d.bozo_exception)

        return d

    def run(self):
        query = self.getBaseQuery()

        d = self.queryCEDA(query)

        totalResults = int(d["feed"]["os_totalresults"])
        # if total records exceeds 10,000 shrink the window
        if totalResults > 10000:
            logger.exception("Total number of results exceeds 10,000 and cannot be retreived")
            raise Exception("Query returns more then 10000 results")

        pageSize = int(d["feed"]["os_itemsperpage"])

        pages = ceil(totalResults / pageSize)

        log.info("data pages %d", pages)

        log.info("total results %d", totalResults)
        output = {
            "query": copy.deepcopy(query),
            "entries": d["entries"]
        }

        if pages > 1:
            for page in range(2, pages + 1):
                
                query["startPage"] = page

                log.info("getting page %d", page)
                d = self.queryCEDA(query)

                output["entries"].extend(d["entries"])

        with self.output().open('w') as out:
            out.write(json.dumps(output))
            
    def output(self):
        return wc.getTarget('RawDataFeed.json', self.runDate, getStatePaths(self.pathroots), self.useLocalTarget) 

@requires(GetRawDataFeed)
class MakeNewProductsList(luigi.Task):
    useLocalTarget = luigi.BoolParameter()
    runDate = luigi.DateParameter()
    pathroots = luigi.DictParameter()

    def run(self):
        newProducts = {
            "queryWindow": {
                "start": None,
                "end": None
            },
            "products": []
        }

        with self.input().open('r') as rawFile:
            rawData = json.load(rawFile)
            entries = seq(rawData["entries"])

            newProducts["queryWindow"]["start"] = rawData["query"]["startDate"]
            newProducts["queryWindow"]["end"] = rawData["query"]["endDate"]

            if not entries.empty():
                newProducts["products"] = (
                    entries.map(lambda x: {
                        "productId": x["dcterms_identifier"],
                        "startCapture": x["dcterms_date"].split('/')[0],
                        "endCapture": x["dcterms_date"].split('/')[1],
                        "sourceUrl": (seq(x["links"])
                                        .where(lambda l: l["type"] == "application/zip" and l["title"] == "ftp")
                                        .first())["href"]
                    })).to_list()
        
        with self.output().open('w') as out:
            out.write(json.dumps(newProducts))

    def output(self):
        return wc.getTarget('NewProductsList.json', self.runDate, getStatePaths(self.pathroots), self.useLocalTarget)  

@inherits(MakeNewProductsList)
@inherits(GetAcquriredProductsFromLastRun)
@inherits(GetAvailableProductsFromLastRun)
class MakeAvailableProductsList(luigi.Task):
    useLocalTarget = luigi.BoolParameter()
    runDate = luigi.DateParameter()
    pathroots = luigi.DictParameter()

    def requires(self):
        t = []
        t.append(self.clone(MakeNewProductsList))
        t.append(self.clone(GetAcquriredProductsFromLastRun))
        t.append(self.clone(GetAvailableProductsFromLastRun))
        
        return t

    def run(self):
        with self.input()[0].open('r') as availableFile, \
            self.input()[1].open('r') as lastAcquiredFile, \
            self.input()[2].open('r') as lastAvailableFile:

            available = json.load(availableFile)
            lastAcquired = json.load(lastAcquiredFile)
            lastAvailable = json.load(lastAvailableFile)

            available["products"].extend(lastAvailable["products"])

            available["products"] = (seq(available["products"])
                                    .distinct_by(lambda x: x["productId"])
                                    .filter_not(lambda x: seq(lastAcquired["products"])
                                                        .where(lambda y: y["productId"] == x["productId"])
                                                        .any())
                                    ).to_list()
        
        with self.output().open('w') as out:
            json.dump(available, out)

    def output(self):
        return wc.getTarget('AvailableProducts.json', self.runDate, getStatePaths(self.pathroots), self.useLocalTarget) 
    
@requires(MakeAvailableProductsList)
class GetS2RawProducts(luigi.Task):
    useLocalTarget = luigi.BoolParameter()
    runDate = luigi.DateParameter(default=datetime.now())
    pathroots = luigi.DictParameter()
    cedaFtpUser = luigi.Parameter()
    cedaFtpPassword = luigi.Parameter()

    def getJobSpec(self, product, targetPath):
        jobspec = {
            "ftpUser": self.cedaFtpUser,
            "ftpPassword": self.cedaFtpPassword,
            "productId": product["productId"],
            "ftpUrl": product["sourceUrl"],
            "targetPath": targetPath
        }

        return jobspec

    def run(self):
        log.info("Get S2 raw products")

        # todo check for zero products
        pl = {}

        with self.input().open('r') as productList:
           pl = json.load(productList)

        products = seq(pl["products"])

        targetPath = self.pathroots["product-s3Root"]

        jobs = (products
                .map(lambda p: self.getJobSpec(p, targetPath))).to_list()

        r = wc.ftpProcessor.processJobs(jobs)
        results = seq(r)

        acquiredProducts = (products
            .map(lambda p: (p["productId"], p))
            .inner_join(results.map(lambda r: (r["productId"], r)))
            .filter(lambda x: x[1][1]["success"])
            .map(lambda x: {
                "productId": x[0],
                "startCapture": x[1][0]["startCapture"],
                "endCapture": x[1][0]["endCapture"],
                "sourceUrl": x[1][0]["sourceUrl"],
                "location": x[1][1]["location"]
            })
            ).to_list()

        output = {
            "products": acquiredProducts
        }

        with self.output().open('w') as out:
            json.dump(output, out)

    def output(self):
        return wc.getTarget('S2RawProducts.json', self.runDate, getStatePaths(self.pathroots), self.useLocalTarget)  




