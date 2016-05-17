#!/bin/bash

docker run -d -p 8888:8888 -v $PWD:/usr/local/opengrid --name opengrid_release opengrid/release:latest
