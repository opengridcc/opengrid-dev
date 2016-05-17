#!/bin/bash
docker build -t opengrid/release:latest .
docker push opengrid/release:latest
