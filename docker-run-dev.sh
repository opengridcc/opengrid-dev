#!/bin/bash

if docker ps -a | grep -q opengrid-release; then
	echo "Stopping and/or removing existing opengrid-release container."
	docker stop opengrid-release > /dev/null
	docker rm opengrid-release > /dev/null
fi
CID=$(docker run -d -p 8888:8888 -v $(pwd -P):/usr/local/opengrid --name opengrid-dev opengrid/dev:latest)
echo "Opengrid notebook server running on $(docker inspect --format '{{ .NetworkSettings.IPAddress }}' ${CID}):8888"
echo "Please enter this in your browser to access the jupyter notebooks."