# Tag My Outfit Pipeline

## Overview

This repository provides multiple input and output nodes to build a pipeline for the Tag My Outfit Server. 
Some of the created nodes can be encapsulated into docker containers to provided an easier deployment.

## API

The nodes on ths project rely on the gRPC protocol defined in the [Pipeline Core Project](https://github.com/DuarteMRAlves/Pipeline-Core).
The input nodes should create stubs to send requests for the first processing node, while the output nodes should receive and process the results and not retransmit the information.

## Getting Started

 * Run the Tag My Outfit Service node and the attached processing node sepecified in the [Docker Compose file](docker-compose.yml):
 ```
 $ docker-compose up
 ```

 * Choose one source *(input node)* and destination *(output node)* and run them.

 * The output node should start to display and store any relevant information.


## Available Nodes

### Sources

 * [Image Folder](Images%20Folder%20Source): Reads images from folder and sends them to the next node.

### Destinations

 * [Visualization](Visualization%20Destination): Shows the original images as well as the received results.
