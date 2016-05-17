#!/bin/bash

CID=$(docker run -d -p 8888:8888 -v $PWD:/usr/local/opengrid --name opengrid-release opengrid/release:latest)
echo "Opengrid notebook server running on $(docker inspect --format '{{ .NetworkSettings.IPAddress }}' ${CID}):8888"

