#!/bin/bash
# On Mac, start docker daemon if not running
if docker-machine  > /dev/null 2>&1; then
    eval $(docker-machine env default)
fi
# Stop and/or remove existing opengrid-dev container, if any
if docker ps -a | grep -q opengrid-release; then
	echo "Stopping and/or removing existing opengrid-release container."
	docker stop opengrid-release > /dev/null
	docker rm opengrid-release > /dev/null
fi
# Start the docker, publish port 8888 to host and mount current folder to /usr/local/opengrid in the container
CID=$(docker run -d -p 8888:8888 -v $(pwd -P)/notebooks:/usr/local/opengrid/notebooks/user --name opengrid-release opengrid/release:latest)

echo "Opengrid notebook server running on http://$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' ${CID}):8888"
echo "Please enter this in your browser to access the jupyter notebooks."

