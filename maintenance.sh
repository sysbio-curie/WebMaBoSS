#!/bin/bash

# Runs manage.py maintenance every MAINTENANCE_EVERY seconds (every hour by default, never with 0), in the background of
# the container. Each run is a new process : one which fails doesn't stop the next ones.

EVERY=${MAINTENANCE_EVERY:-3600}
if [ "$EVERY" -le 0 ] 2>/dev/null || ! [ "$EVERY" -eq "$EVERY" ] 2>/dev/null; then
    exit 0
fi

# After the server has started
sleep 60
while true; do
    /opt/conda/bin/python3 /var/webmaboss/manage.py maintenance --settings=settings.prod_settings
    sleep "$EVERY"
done
