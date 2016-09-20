#!/bin/bash
# On Mac, start docker daemon if not running
if docker-machine  > /dev/null 2>&1; then
    docker-machine start
    docker-machine env
    eval $(docker-machine env default)
fi
# Stop and/or remove existing opengrid-release container, if any
if docker ps -a | grep -q opengrid-release; then
	echo "Stopping and/or removing existing opengrid-release container."
	docker stop opengrid-release > /dev/null
	docker rm opengrid-release > /dev/null
fi
# Start the docker, publish port 8888 to host 
# mount current folder to /usr/local/opengrid in the container
# for data persistence, mount ./data to the /data folder
# if you want to store the data in a different location, modify the command below
docker run -d -p 8888:8888 -v $(pwd -P)/notebooks:/usr/local/opengrid/notebooks/User -v $(pwd -P)/data:/data --name opengrid-release opengrid/release:latest

# Give it some time
sleep 1s 

URL=http://$(docker-machine ip default):8888

# open the browser
if start $URL > /dev/null 2>&1; then
	echo “Notebook server opened in browser”
elif open $URL > /dev/null 2>&1; then
	echo “Notebook server opened in browser”
elif xdg-open $URL > /dev/null 2>&1; then
	echo “Notebook server opened in browser”
elif gnome-open $URL > /dev/null 2>&1; then
	echo “Notebook server opened in browser”
else
	echo “Opening notebook server in browser failed, surf to $URL“
fi