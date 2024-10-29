#!/usr/bin/env sh

# Migrate the django db and collect static files.
echo "Migrate changes to the DB"
python ./manage.py migrate --noinput
echo "Collect static files"
python ./manage.py collectstatic --noinput
echo "Create API user"

# Start gunicorn.
echo "Start gunicorn $(if [ "$DEBUG" = "True" ]; then echo "(with \"--reload\" as DEBUG=$DEBUG)"; fi) "
exec gunicorn Happyface4.wsgi $(if [ "$DEBUG" = "True" ]; then echo "--reload"; fi) --timeout 90 --access-logfile "-" --forwarded-allow-ips="*" --bind="0.0.0.0:8000"
