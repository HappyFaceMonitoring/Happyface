#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# check if argument flags are provided and if so, pass them to the logs command
if [ "$#" -gt 0 ]; then
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" --ansi=always logs $@
else
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" --ansi=always logs | less
fi