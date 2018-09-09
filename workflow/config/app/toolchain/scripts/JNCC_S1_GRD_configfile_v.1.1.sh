#!/bin/sh

##### Directories set up  
##### ==================
##### INPUT directories
export MAIN_DIR="{{ s1_ard_main_dir }}" ##== MAIN DIRECTORY with DEM, Input dataset and Outputs
export BASKET_INDIR="{{ s1_ard_basket_dir }}" ##== directory containing  S1_GRDH.zip products to be processed
#####
export EXTDEMFILE="{{ s1_ard_ext_dem }}" ##== External APGB DEM
export EXTDEMNOVAL="-32768.0" ## External DEM No data value
##### OUTPUT directories
export MAIN_OUTDIR="{{ s1_ard_temp_output_dir }}"  ##== MAIN OUTPUT DIRECTORY where products output folders will be created 
##### After Processing
export PROZIP_DIR="${MAIN_DIR}/zip_processed"  ##== directory where S1.zip data are moved after processing
##### SW and processing xml chains directories
export SCRIPT_DIR="/app/toolchain/scripts"
export GRAPHSDIR="${SCRIPT_DIR}/xml" ##== DIRECTORY with snap xml graphs for the processing 
export SNAP_HOME="/app/snap/bin" ##== SNAP (version 6) directory
export SNAP_OPTS="-J-Xmx16204m -J-Xms4096m -J-XX:-UseGCOverheadLimit" ##== SNAP command line arguments
#####============================================================
##### STATIC Variable for Log files   
#####============================================================
export logtime=$(date +"%F_%H%M%S")
export software="@Snap_version6"
#### LOG files
export MAINLOG=${MAIN_OUTDIR}/Mainlog_${logtime}_${software}.txt  ### Generation of logfile for the processing 
#####============================================================
##### Processing Parameters 
#####============================================================
##### UTM map projection parameters
export UTMPROJ="UTM Zone 30, North"   ### e.g. "UTM Zone 30" , "UTM Zone 22, South"
export centralmeridian="-3.0" ### e.g. "-3", "-51"
export false_northing="0.0"  ### e.g. "0.0"
