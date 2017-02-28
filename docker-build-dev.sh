#!/bin/bash
docker build -f Dockerfile.dev -t opengrid/dev:latest .
docker push opengrid/dev:latest

docker build -f Dockerfile_python3.dev -t opengrid/dev:python3 .
docker push opengrid/dev:python3