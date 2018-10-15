S1 ARD Processor
================

Docker container that runs the s1-processing-scripts.

S1 processing scripts subtree
--------------------
The S1 processing scripts branch is required at build time

### Add the remote
Create a link to the proper remote repo

    git remote add -f s1-processing-scripts https://github.com/jncc/s1-processing-scripts.git


### Linking to the correct branch
At development time you will need to link to a development branch for testing.
Before building a production contain this branch should be merged into master and this project should be set to master.

To change s1-processing-scripts to a different branch:

    git rm -rf workflow/app/toolchain/scripts
    git commit
    git subtree add --prefix=workflow/app/toolchain/scripts s1-processing-scripts <branch> --squash

Current:

    git subtree add --prefix=workflow/app/toolchain/scripts s1-processing-scripts master --squash

### Fetching changes from the subtree

All changes to the current working tree need to be commited

    git fetch s1-processing-scripts
    git subtree add --prefix=workflow/app/toolchain/scripts s1-processing-scripts <branch> --squash

### Pulling changes from the subtree

    git subtree pull --prefix=workflow/app/toolchain/scripts s1-processing-scripts <branch> --squash

Current:

    git subtree pull --prefix=workflow/app/toolchain/scripts s1-processing-scripts master --squash

### Pushing changes from the subtree back to the repo

    git subtree push --prefix=workflow/app/toolchain/scripts s1-processing-scripts <branch> --squash

Current:

    git subtree push --prefix=workflow/app/toolchain/scripts s1-processing-scripts master --squash

Luigi workflows subtree
-----------------------
The luigi workflows project is required at build time

### Add the remote
Create a link to the proper remote repo

    git remote add -f eo-s1-workflow https://github.com/jncc/eo-s1-workflow.git

### Linking to the correct branch
At development time you will need to link to a development branch for testing.
Before building a production contain this branch should be merged into master and this project should be set to master.

To change eo-s1-workflow to a different branch:

    git rm -rf workflow/app/workflows
    git commit
    git subtree add --prefix=workflow/app/workflows eo-s1-workflow <branch> --squash


Current:

    git subtree add --prefix=workflow/app/workflows eo-s1-workflow <branch> --squash

### Fetching changes from the subtree

All changes to the current working tree need to be commited

    git fetch eo-s1-workflow
    git subtree add --prefix workflow/app/workflows eo-s1-workflow <branch> --squash

### Pulling changes from the subtree

    git subtree pull --prefix workflow/app/workflows eo-s1-workflow <branch> --squash

Current:

    git subtree pull --prefix workflow/app/workflows eo-s1-workflow <branch> --squash

### Pushing changes from the subtree back to the workflows repo


    git subtree push --prefix workflow/app/workflows eo-s1-workflow <branch> 

Current:

    git subtree push --prefix app/workflows eo-s1-workflow <branch> 

Build and run instructions
--------------------------

Build to image:

    docker build -t s1-ard-processor .

Use --no-cache to build from scratch

Run Interactivly:

docker run -i --entrypoint /bin/bash 
    -v /<hostPath>/input:/input 
    -v /<hostPath>/output:/output 
    -v /<hostPath>/state:/state 
    -v /<hostPath>/static:/static 
    -v /<hostPath>/working:/working 
    -t jncc/test-s1-ard-processor 

Where <hostpath> is the path on the host to the mounted fole

Convert Docker image to Singularity image
-----------------------------------------

Create a Singularity file

    Bootstrap: docker
    Registry: http://localhost:5000
    Namespace:
    From: s1-ard-processor:latest

Run a local docker registry
	
    docker run -d -p 5000:5000 --restart=always --name registry registry:2

Tag and push your docker image to the registry

    docker tag s1-ard-processor localhost:5000/s1-ard-processor
    docker push localhost:5000/s1-ard-processor

Build a Singularity image using your Docker image

    sudo SINGULARITY_NOHTTPS=1 singularity build s1-ard-processor.simg Singularity

Run:

    singularity exec
        -bind /<hostPath>/input:/input 
        --bind /<hostPath>/output:/output 
        --bind /<hostPath>/state:/state 
        --bind /<hostPath>/static:/static 
        --bind /<hostPath>/working:/working 
        s1-ard-processor.simg /app/exec.sh
        --sourceFile '/S1A_IW_GRDH_1SDV_20180104T062204_20180104T062229_020001_02211F_43DB.zip'
        --outputFile '^[\w\/-]+_Gamma0_APGB_OSGB1936_RTC_SpkRL_dB.tif'
