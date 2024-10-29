#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

HF_CONTAINER_NAME=happyface_website
HF_SERVICE_NAME=website

# if HF_CONTAINER_NAME is not running, start it
if [ ! "$(docker ps -a | grep $HF_CONTAINER_NAME)" ]; then
    . ./start_dev.sh
fi

docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec $HF_SERVICE_NAME sh