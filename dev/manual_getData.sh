#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

HF_CONTAINER_NAME=happyface_getData
HF_SERVICE_NAME=getData

# if HF_CONTAINER_NAME is not running, start it
if [ ! "$(docker ps -a | grep $HF_CONTAINER_NAME)" ]; then
    . ./start_dev.sh
fi

docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec $HF_SERVICE_NAME python3 /app/Happyface4/manage.py getData $@