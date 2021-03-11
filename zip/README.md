# Tag My Outfit Pipeline - Zip Distribution

## Overview

The Tag My Outfit Pipeline classifies clothing parts in images, 
as well as predicts its attributes.
It displays the results using a web visualization interface.

## Instructions

### Install Docker

The stages are executed using [Docker](https://www.docker.com).
You can install Docker on [Linux](https://docs.docker.com/engine/install/), 
[macOS](https://docs.docker.com/docker-for-mac/install/) 
or [Windows](https://docs.docker.com/docker-for-windows/install/).

We use Docker-Compose *(installed by default with Docker)* to run the multiple containers.
The images for the stages are available on [DockerHub](https://hub.docker.com), 
and we be automatically downloaded when you first executed the pipeline.

### Execute the Pipeline

To start the pipeline execution, run the following command from the directory root.

```shell
$ docker-compose up
```

The images for the stages should automatically start downloading, 
and the pipeline will start.

### See the Results

The see the results, open a browser window at http://localhost:5000.
The images should start appearing after some seconds 
*(you may need to refresh the window until the first image appears)*.

### Custom Images

The pipeline retrieves the images from the 'images' directory. 
You can replace the images inside the directory to classify your own images.