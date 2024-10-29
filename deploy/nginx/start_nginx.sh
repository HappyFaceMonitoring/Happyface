#!/usr/bin/env sh

#this little script checks if the website is up and running using nc before starting nginx
set -e

host="website"

sed "s/\$HF_HOSTS/${HF_HOSTS}/g" /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

until ping -c1 $host >/dev/null 2>&1; do
    echo "Waiting for $host - sleeping"
    sleep 1
done

>&2 echo "$host is up - starting nginx"
exec nginx -g "daemon off;"