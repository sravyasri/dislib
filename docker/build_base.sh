#!/bin/bash -e

docker build -t bscwdc/dislib-base:latest .

docker login -u ${dh_username} -p ${dh_password}
docker push bscwdc/dislib-base:latest
