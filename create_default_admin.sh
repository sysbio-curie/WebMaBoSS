#!/bin/bash

/opt/conda/bin/python3 manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')"
printf "admin: admin\nadmin_email: admin@example.com\n" >> /var/webmaboss/data/settings/config.yml