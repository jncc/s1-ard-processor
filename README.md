# Luigi Workflows
The luigi workflow tasks for `EO-Alpha`. These tasks deal with the management and processing of Sentinel 1 & Sentinel 2 ARD data.

## Run Workflows

### Sentinel 1
#### Get Raw S1
Gets available products in a window spanning from the last end capture date (from available.json in the previous folder) to the newly computed end date (rundate - queryWindowOffset). "queryWindowOffset" is set in luigi.cfg and is currently 3 days. It will also aquire any previously identified but not download products.
```
PYTHONPATH='.' luigi --module get_s1_raw GetS1RawProducts --runDate=2017-11-05 --useLocalTarget --local-scheduler
```
Set `useLocalTarget` to use the local filesystem path for luigi state. 
Root paths for storing data for both s3 and local are set in luigi.cfg in the [GetS1RawProducts] section.
Set `queryWindowOffset` to the number of days back from the runDate at which the capture window should be terminated.

*Seeding*
Create a folder (local or s3) in the root path of the format YYYY-mm-dd ie 2017-11-04 if using the command line above. The date shoul be one day before the runDate you intend to start with. Copy the contents of the *seed* subfolder into this location.

##### Tasks
###### GetAvailableProductsFromLastRun
Gets list of avaialable products from previous days run (AvailableProducts.json)

###### GetAcquiredProductsFromLastRun
Gets list of acquired products from previous days run (S1RawProducts.json)

###### GetRawDataFeed
Depends on: 

- GetAvailableProductsFromLastRun

Steps:

- Determines the latest capture end datetime from the last run and uses it as the start of the query window
    - If no data uses the start datetime of the last query window
- Computes and end datetime based on the rundate - 3 days
- Downloads each page of data outputting the url to the luigi log

Output: RawDataFeed.json

- Query: Each query parameter that was submitted
- Entries: The list of raw entries from the CEDA opensearch atom feed

###### MakeNewProductsList
Depends on:

- GetRawDataFeed

Steps:

Ingests the output of GetRawFeedData and outputs a simplified list with the following feildst:

- productId - The full name of the ESA S1 product
- startCapture - The datetime indicating when the capture of the element started
- endCapture - The datetime indicating when the capture of the element ended
- sourceURL - The ftp URL for retrieving the zip product

Output:

NewProducts.json

- queryWindow - The start and end timestamps of the query window
- products - The list of products as described above that are available for download

###### MakeAvailableProductsList
Depends on 

- MakeNewProductsList
- GetAvailableProductsFromLastRun
- GetAcquriredProductsFromLastRun

Steps: 

- Combines output from *MakeNewProductsList* and *GetAvailableProductsFromLastRun*
- Removes duplicates
- Removes products that occur in the combined list and the output from *GetAcquriredProductsFromLastRun*

Output:

- AvailableProducts.json
- queryWindow - The start and end timestamps of the query window executed during this run
- products - The list of products to be downloaded including any carried over from the last run that didn't download.

###### GetS1RawProducts
TODO

#### Make S1 ARD
This workflow takes the raw product obtained via the `Get Raw S1` workflow and processes it into an ARD.
```
PYTHONPATH='.' luigi --module make_s1_ard ProcessRawS1Files
```
The processing of each ARD is a time intensive procedure, you can skip this part of the process by providing the `--testProcessing` parameter. The workflow will still execute all tasks but the `ProcessRawToArd` task will create dummy output instead of processing the ARD. It will also not delete the original raw .zip file as part of the `TeardownArdProcess` when this parameter is set.

##### Tasks
###### ProcessRawS1Files
This is the main orchestration task. It creates a chain of all the other tasks for each product that requires processing and then yields to them.

###### CreateSourceList
Create a JSON file listing the paths to all of the products that have been identified for processing.

###### DownloadRawProduct
Download each raw product to a temporary location for processing.

###### ProcessRawToArd
Runs a shell script to process the raw product into many files that constitute an ARD.

###### TransferArdToS3
Copy the ARD to a location within S3

###### TeardownArdProcess
A clean-up task, deletes local temporary files created as part of the ARD processing and deletes the original raw .zip product that was successfully processed from S3.

### Sentinel 2
TODO

## Development
### Setup
Create virtual env
```
virtualenv -p python3 /<project path>/luigi-workflows-venv
```
Activate the virtual env
```
source ./luigi-workflows-venv/bin/activate
```
Install Requirements
```
pip install -r requirements.txt
```

#### Update Requirements
```
pip freeze > requirements.txt
```