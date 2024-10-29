#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker compose -f "${SCRIPT_DIR}/docker-compose.yml" up --remove-orphans -d --build