## ESA SNAP Toolbox Base Container

This container is designed to provide a base environment for running the ESA SNAP toolbox, which is used for processing remote sensing data, particularly Synthetic Aperture Radar (SAR) data from Sentinel-1 missions. It is currently based on the OSGeo GDAL base container currently version [3.10.3](https://github.com/osgeo/gdal/pkgs/container/gdal/390465960?tag=ubuntu-full-3.10.3) which currently uses Ubuntu 22.04 as the base operating system with the [ESA SNAP toolbox](http://step.esa.int/main/toolboxes/snap/) v12.0.0.0 installed.

## Usage

This container is currently used as the base for the [JNCC S1 ARD Processor](https://hub.docker.com/r/jncc/s1-ard-processor/). 

## Source Code

The source code for this container is available at [GitHub](https://github.com/jncc/s1-ard-processor)