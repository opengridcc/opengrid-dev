#!/bin/bash
docker build -f Dockerfile.dev -t opengrid/dev:latest .
docker push opengrid/dev:latest