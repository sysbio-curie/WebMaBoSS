#!/bin/bash

echo ">> Downloading JS dependencies"
yarn >/dev/null

echo ">> Initializing database"
mkdir -p data/db
mkdir -p data/media
/opt/conda/bin/python3 manage.py makemigrations > /dev/null
/opt/conda/bin/python3 manage.py migrate > /dev/null

echo ">> Creating super user"
/opt/conda/bin/python3 manage.py createsuperuser
