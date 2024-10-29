#!/usr/bin/env sh

# wait for the database to be migrated by happyface container
sleep 30

python ./manage.py getDataRoutine