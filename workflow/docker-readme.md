Readme for docker hub - this text must be manually published

## What is this?

This container provides a luigi workflow that processes raw Sentinal 1 files from ESA to an analysis ready data product utilising the SNAP toolbox from ESA. 

It is designed to generate data in the OSGB projection.

The luigi workflow can run standalone or with a luigi central scheduler.

This container derives from the [jncc/snap-base:latest](https://hub.docker.com/r/jncc/snap-base/) container that provides SNAP.

## Mount points

This ARD processor consumes and generates large ammounts of data and this may require you to mount external file systems to account for this. For this reason there are a number of locations in the container file system that you may wish to mount externally.

* Input - This mount point should contain the raw file you will be processing 
* Static - This should contain the DEM you will be using for terrain adjustment. 
* Working - Temporary files / paths created during processing. This folder is cleared at the end of each run unless you specify the --noClean switch.  The working data is written to a subfolder of the format <productId> where the date components are derived from the capture date of the source product. The product Id is also derived from the source product.
* Ouput - This folder wll contain the output. The output is written to a subfolder of the format <Year>/<Month>/<Day>/<product name> where the date components are derived from the capture date of the source product. The product name is also derived from the input product data.
* State - The state files generated for each task in the luigi workflow. This is an optional mount generally for debugging. State files are coppied into the a subfolder of output of the form ../state/<Year>/<Month>/<Day>/<productId> unless the --noStateCopy flag is specified


## Command line

The command line is of the format 

docker <docker parameters> jncc/s1-ard-processor VerifyWorkflowOutput <luigi-parameters>

VerifyWorkflowOutput is the luigi task that requries all processing steps to be run and verifys the ouput.

# Example:

```
docker run -i -v /data/input:/input -v /data/output:/output -v /data/state:/state -v /data/static:/static -v data/working:/working jncc/test-s1-ard-processor VerifyWorkflowOutput --inputFileName=S1A_IW_GRDH_1SDV_20180104T062254_20180104T062319_020001_02211F_A294.zip --demFile=DTM_UK_10m_WGS84_CompImg_S1vers3.tif --noClean --local-scheduler
```

# Luigi options

These parameters are relevant to the luigi worker running inside the container: See [Luigi docs](https://luigi.readthedocs.io/en/stable/configuration.html#core) for more information a full list of relevant options

* --local-scheduler - Use a container specific scheduler - assumed if scheduler host isn't provided
* --scheduler-host CORE_SCHEDULER_HOST - Hostname of machine running remote scheduler
* --scheduler-port CORE_SCHEDULER_PORT - Port of remote scheduler api process
* --scheduler-url CORE_SCHEDULER_URL - Full path to remote scheduler

# Workflow options

* --inputFileName FILENAME (required) - The raw input file name. This file should reside in the Input folder.
* --demFile FILENAME (required) - The terain model used in the processing. This should reside in the static folder.
* --memoryLimit LIMIT (in GB) - The memory limit set for the snap process. This should be not exceed about 75% of the host machine memory - Default 14GB
* --noClean - Don't remove the temporary files created in the working folder - May be useful for determining why a processing run failed by analysing preserved intermediate outputs and SNAP logs.
* --noStateCopy - Don't copy the luigi state files to a subfolder of output.
* --removeInputFile - Removes the input file from the input folder.

## Outputs

Following a successful run the output folder will contain the following structure.

    ../output
    ├── <Year>
    │   └── <Month>
    │       └── <Day>
    │           └── <Merged Output Product Name>
    │               ├── <Merged Output Product Name.tif> - Merged product data
    │               ├── <Merged Output Product Name.xml> - Product metadata
    │               ├── VH
    │               │   └── <VH Polarised Product Name.tif> - VH polarised product
    │               └── VV
    │                   └── <VH Polarised Product Name.tif> - VH polarised product
    └── state
        └── <Workflow Product ID>
            ├── AddMergedOverviews.json
            ├── CheckArdFilesExist.json
            ├── ConfigureProcessing.json
            ├── CopyInputFile.json
            ├── CutDEM.json
            ├── GenerateMetadata.json
            ├── GetConfiguration.json
            ├── GetManifest.json
            ├── MergeBands.json
            ├── ProcessRawToArd.json
            ├── ReprojectToOSGB.json
            ├── TransferFinalOutput.json
            └── VerifyWorkflowOutput.json

# Output Product Name

The output product name is derived from data acquired at various stages of the workflow and cosists of the following elements:
S1A_20180113_ORB001_Asc_062939_063004_VV_G0_GB_OSGB_RTCK
aaa_bbbbbbbb_cccccc_ddd_eeeeee_ffffff_gg_hh_ii_jjjj_kkkk

The raw file name is divided into elements separated by an underscore 

a – raw file name element 1

b – raw file name element 5 - date part only

c – if raw file name element 1 = S1A  -> abs orbit no =  raw file name element 7 --> rel orbit no = mod (Absolute Orbit Number orbit - 73, 175) + 1
	if raw file name element 2 = S1B  -> abs orbit no =  raw file name element 7 --> rel orbit no = mod (Absolute Orbit Number orbit - 27, 175) + 1

d – from source file manifest.xml metadataSection/[metadataObject ID=measurementOrbitReference]/metadataWrap/xmlData/safe:extension/s1:orbitProperties/s1:pass/ ASCENDING or DESCENDING 
	Output asc or desc

e – raw file name element 5 - time only part

f – raw file name element 6 - time only part

g – Polarisation (VV, VH or DV fot the merged bands)

h – Gamma-0

i – Elevation data used in processing - **hard coded to GB**

j – CRS for terrain corrected outputs - **Always OSGB**

k – Radiometric Normalisation method - **Always RCTK**

l – Speckle filter applied - **Always SpkRL**

# Workflow Product ID

The workflow product ID is derived from the name of the input product and is a simple unique identifier for the process. 

It is used to name temporary working folders in the /working mount and to name the folder to which state is coppied when the process completes. 

It is composed from the following elements
* Platform name
* Capture date
* Start capture time
* End capture time

Input Product Name: **S1A**_IW_GRDH_1SDV_**20180104**T0**62254**_20180104T**062319**_020001_02211F_A294.zip

Workflow Product Id: S1A_20180104_062254_062319

# Example Output

Processing the product S1A_IW_GRDH_1SDV_20180104T062254_20180104T062319_020001_02211F_A294.zip will give the following output:

    ../output
    ├── 2018
    │   └── 01
    │       └── 04
    │           └── S1A_20180104_154_desc_062254_062319_DV_Gamma-0_GB_OSGB_RCTK_SpkRL
    │               ├── S1A_20180104_154_desc_062254_062319_DV_Gamma-0_GB_OSGB_RCTK_SpkRL.tif
    │               ├── S1A_20180104_154_desc_062254_062319_DV_Gamma-0_GB_OSGB_RCTK_SpkRL.xml
    │               ├── VH
    │               │   └── S1A_20180104_154_desc_062254_062319_VH_Gamma-0_GB_OSGB_RCTK_SpkRL.tif
    │               └── VV
    │                   └── S1A_20180104_154_desc_062254_062319_VV_Gamma-0_GB_OSGB_RCTK_SpkRL.tif
    └── state
        └── S1A_20180104_062254_062319
            ├── AddMergedOverviews.json
            ├── CheckArdFilesExist.json
            ├── ConfigureProcessing.json
            ├── CopyInputFile.json
            ├── CutDEM.json
            ├── GenerateMetadata.json
            ├── GetConfiguration.json
            ├── GetManifest.json
            ├── MergeBands.json
            ├── ProcessRawToArd.json
            ├── ReprojectToOSGB.json
            ├── TransferFinalOutput.json
            └── VerifyWorkflowOutput.json

