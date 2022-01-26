#!/bin/bash

# IMPORTANT - Fill the "Common Name (e.g. server FQDN or YOUR name) []:" with the DNS name of your OpenWRT-SDN-Proxy

# Private keys for the JWT
ssh-keygen -t rsa -b 4096 -m PEM -f ./northbound.key
openssl rsa -in ./northbound.key -pubout -outform PEM -out ./northbound.key.pub

# SSL certificate for API's
openssl req -new -key ./northbound.key -out ./northbound.csr
cp ./northbound.key ./northbound.key.org
openssl rsa -in ./northbound.key.org -out ./northbound.key
openssl x509 -req -days 365 -in ./northbound.csr -signkey ./northbound.key -out ./northbound.crt