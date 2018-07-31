# Luigi Workflows
The luigi workflow tasks from `EO-Alpha` for running on JASMIN. These tasks deal with the management and processing of Sentinel 1 ARD data.

## Run Workflows

### Sentinel 1

#### Process S1 Basket
This workflow takes all raw products in a given directory and processes them to ARD in a Singularity container on LOTUS.
```
PYTHONPATH='.' luigi --module process_s1_basket RunSingularityInLotus
```
The processing of each ARD is a time intensive procedure, you can skip this part of the process by providing the `--testProcessing` parameter. The workflow will still execute all tasks but the `ProcessRawToArd` task will create dummy outputs instead of processing the ARD.

#### Process S1 Scene
To process one scene you can also directly run the workflow without the RunSingularityInLotus orchestration task.
```
PYTHONPATH='.' luigi --module container Cleanup --productId <productId> --sourceFile '<rawInputFilePath>'
```

## Development
### Setup
Create virtual env
```
virtualenv -p python3 /<project path>/eo-s1-workflows-venv
```
Activate the virtual env
```
source ./eo-s1-workflows-venv/bin/activate
```
Install Requirements
```
pip install -r requirements.txt
```

#### Update Requirements
```
pip freeze > requirements.txt
```