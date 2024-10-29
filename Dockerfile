# load alpine server with nginx installed
FROM python:3.12-alpine

# Needed for pycurl
ENV PYCURL_SSL_LIBRARY=openssl

# install additional packages
RUN apk add --no-cache --virtual build-deps curl-dev gcc musl-dev
RUN apk add --no-cache curl openssl jpeg libpng git
# change the directory
WORKDIR /app

# copy Happyface core and analyses to image
COPY . /app/
# install python packages, remove build dependencies and cache and add CERN CA certificates
RUN pip install --upgrade --no-cache-dir pip setuptools wheel \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del build-deps \
  && rm -r /root/.cache \
  && curl https://ca.cern.ch/cafiles/certificates/CERN%20Grid%20Certification%20Authority\(1\).crt | dos2unix >> /etc/ssl/certs/ca-certificates.crt \
  && curl https://ca.cern.ch/cafiles/certificates/CERN%20Root%20Certification%20Authority%202.crt | openssl x509 -inform DER -outform PEM >> /etc/ssl/certs/ca-certificates.crt

ENTRYPOINT [ "/app/entrypoint_happyface.sh" ]