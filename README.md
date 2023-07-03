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


Build and run instructions
--------------------------

Build to image:

    docker build -t s1-ard-processor .

Use --no-cache to build from scratch

Run Interactively:

    docker run -i --entrypoint /bin/bash 
        -v /<hostPath>/input:/input 
        -v /<hostPath>/output:/output 
        -v /<hostPath>/state:/state 
        -v /<hostPath>/static:/static 
        -v /<hostPath>/working:/working
        -v /<hostPath>/report:/report 
        -v /<hostPath>/database:/database  
        -t jncc/test-s1-ard-processor 

Where \<hostpath> is the path on the host to the mounted folder

Convert Docker image to Apptainer image
-----------------------------------------

Run a local docker registry
	
    docker run -d -p 5000:5000 --restart=always --name registry registry:2

Tag and push your docker image to the registry

    docker tag s1-ard-processor localhost:5000/s1-ard-processor
    docker push localhost:5000/s1-ard-processor

Build an apptainer image using your Docker image

    sudo apptainer build --no-https s1-ard-processor.sif docker://localhost:5000/s1-ard-processor

Run:

    apptainer exec
        -bind /<hostPath>/input:/input 
        --bind /<hostPath>/output:/output 
        --bind /<hostPath>/state:/state 
        --bind /<hostPath>/static:/static 
        --bind /<hostPath>/working:/working 
        --bind /<hostPath>/report:/report 
        --bind /<hostPath>/database:/database 
        s1-ard-processor.sif /app/exec.sh
        --productName 'S1A_IW_GRDH_1SDV_20180104T062204_20180104T062229_020001_02211F_43DB'

Code change and deployment process
----------------------------------

The code in this repo will be jointly maintained by JNCC and DEFRA/CGI. Use the steps below as a guideline for making new changes:

1. Create a new `feature` branch from `main` and commit your changes there until you're ready to merge
2. Open a pull request to merge back into `main` and add a reviewer from both JNCC and CGI to notify them
3. JNCC then uses the `feature` branch to build a [jncc/s1-ard-processor-dev](https://hub.docker.com/r/jncc/s1-ard-processor-dev) docker image which both parties can use for testing and QA
4. Once it passes QA, JNCC will approve the PR, merge it into `main`, and build a live [jncc/s1-ard-processor](https://hub.docker.com/r/jncc/s1-ard-processor) docker image which can be deployed to production

