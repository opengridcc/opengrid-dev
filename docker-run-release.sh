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
# Start the docker, publish port 8888 to host 
# mount current folder to /usr/local/opengrid in the container
# for data persistence, mount ./data to the /data folder
# if you want to store the data in a different location, modify the command below
CID=$(docker run -d -p 8888:8888 -v $(pwd -P)/notebooks:/usr/local/opengrid/notebooks/User -v $(pwd -P)/data:/data --name opengrid-release opengrid/release:latest)

# Give it some time
sleep 1s 

URL=http://$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' ${CID}):8888
echo "Opengrid notebook server running on $URL"
echo "We will attempt to open your browser on this page."
echo "If it fails, enter this in a browser to access the jupyter notebook server."

# open the browser
if which xdg-open > /dev/null
then
  xdg-open $URL/tree
elif which gnome-open > /dev/null
then
  gnome-open $URL/tree
fi