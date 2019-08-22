#!/bin/bash

python manage.py makemigrations api -v 2 "$@"
python manage.py migrate -v 2 "$@"
python manage.py collectstatic --noinput "$@" > /dev/null
if [ ! -f /var/webmaboss/data/settings/config.yml ]; then
  random_string=`head /dev/urandom | tr -dc A-Za-z0-9 | head -c 24`
  printf "secret_key: %s\nallowed_hosts: ['*']\n" "$random_string"> /var/webmaboss/data/settings/config.yml
fi