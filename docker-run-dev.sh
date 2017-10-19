#!/bin/bash
# On Mac, start docker daemon if not running
if docker-machine  > /dev/null 2>&1; then
    docker-machine start
    docker-machine env
    eval $(docker-machine env default)
fi
# Stop and/or remove existing opengrid-dev container, if any
if docker ps -a | grep -q opengrid-dev; then
	echo "Stopping and/or removing existing opengrid-dev container."
	docker stop opengrid-dev > /dev/null
	docker rm opengrid-dev > /dev/null
fi
# Start the docker, publish port 8888 to host 
# mount current folder to /usr/local/opengrid in the container
# for data persistence, mount ./data to the /data folder
# if you want to store the data in a different location, modify the command below
docker run -d -p 8899:8888 -v $(pwd -P):/usr/local/opengrid  -v $(pwd -P)/data:/data --name opengrid-dev opengrid/dev:latest

# Give it some time
sleep 1s 

URL=http://$(docker-machine ip default):8899

if [ -z "$(docker-machine ip default)"]; then
	URL="http://localhost:8899"
fi
echo "Open the notebook server on $URL"

# open the browser
if gnome-open $URL > /dev/null 2>&1; then
echo “Notebook server opened in browser”
elif start $URL > /dev/null 2>&1; then
echo “Notebook server opened in browser”
elif open $URL > /dev/null 2>&1; then
echo “Notebook server opened in browser”
elif xdg-open $URL > /dev/null 2>&1; then
echo “Notebook server opened in browser”

else
echo “Opening notebook server in browser failed, surf to $URL“
fi

echo "To stop the docker machine run 'docker-machine stop'"