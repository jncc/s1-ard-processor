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


EO Team testing
===============
1 week ?

Manually run process
* create linux back
Check 
* base os they are running on - wsl, ubunut etc
* latest gdal
* snap version

