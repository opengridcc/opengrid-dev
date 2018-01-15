#!/bin/bash

ERROUT="Please pass build or run [with command] to the script."

if [[ $1 ]]; then
	if [[ $1 = "build" ]]; then
		docker build -t sphinx -f Dockerfile.sphinx .
		DONE=1;
	fi
	if [[ $1 = "run" ]]; then
		if ! [[ -e ./build ]]; then
			mkdir build
		fi 
		docker run --rm -it --name sphinx -v "$PWD/build:/home/sphinx" sphinx $2 $3 $4
		DONE=1
	fi 
	if ! [[ $DONE ]]; then
		echo $ERROUT;
	fi
else
	echo $ERROUT;
fi
