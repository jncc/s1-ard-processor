# EO S1 workflow
The luigi workflow for processing Sentinel 1 ARD data. Processes both zipped data files from ESA and unzipped data folders from Mundi.

## Run Workflows

### Process S1 Scene
The processing of each ARD is a time intensive procedure, you can skip this part of the process by providing the `--testProcessing` parameter. The workflow will still execute all tasks but the `ProcessRawToArd` task will create dummy outputs instead of processing the ARD. Check the luigi.cfg file for default parameters.
```
PYTHONPATH='.' luigi --module process_s1_scene VerifyWorkflowOutput --productName <productName>
```

## Development
### Setup
Create virtual env
```
virtualenv -p python3 /<project path>/eo-s1-workflow-venv
```
Activate the virtual env
```
source ./eo-s1-workflow-venv/bin/activate
```
Install Requirements
```
pip install -r requirements.txt
```

#### Update Requirements
```
pip freeze > requirements.txt
```