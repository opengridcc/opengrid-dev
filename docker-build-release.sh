#!/bin/bash
docker build -f Dockerfile.release -t opengrid/release:test .
#docker push opengrid/release:latest
