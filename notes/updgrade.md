base
====

Dockerfile changes
------------------

* Upgrade base to 20.04 
* Upgrade snap to 9?


Config changes
--------------

* config/install-snap.sh --> expect changes to install processs

Workflow
========

Dockerfile changes
------------------

* Python 3 --> 3.8
* GDAL --> latest

Workflow changes
----------------

* /app/workflows/requirements.txt --> versions
* gdal calls might need to be upated

build
=====

* Bump library versions in build script

-- caveat : output filenames could change due snap update - causes workflow code changes - 1 week 
-- move docker image repos into public aws repo - dockerhub deletes old images. ~ ?

EO Team tasks
=============

Manually run process
* dev team to supply vm on aws running ubuntu 20.04 
* EO to determine snap version and gdal version
* Run through manual process to ensure versions work before containers are build
* QA / QC outputs from new containers. 
