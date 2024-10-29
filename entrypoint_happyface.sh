#!/usr/bin/env sh

# check if HF4-Analyses repo exists already
if [ -e "HF4-Analyses/.git" ]; then
    echo "HF4-Analyses repo exists already"
    cd HF4-Analyses
    git pull
    cd ..
else
    echo "clone HF4-Analyses repo"
    [ -d "HF4-Analyses" ] || mkdir HF4-Analyses
    # clone files in HF4-Analyses folder is not directly possible because of the mounted docker volume
    git clone --depth 1 --single-branch --branch $HF_ANALYSES_BRANCH -- $HF_ANALYSES_REPO HF4-Analyses || exit 1
fi

find HF4-Analyses -name "requirement*" -type f -exec pip install -r {} ';'

# Export additional PYTHONPATHS where python modules for django
export PYTHONPATH='/app/Happyface4:/app/HF4-Analyses'
# Export path to CA certificates (see https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification)
export CURL_CA_BUNDLE='/etc/ssl/certs/ca-certificates.crt'

# Wait till postgres container started.
if [ "$DB_NAME" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $DB_HOST $DB_PORT; do
        sleep 0.1
    done

    echo "PostgreSQL started"
fi

cd Happyface4

exec "$@"