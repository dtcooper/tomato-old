#!/bin/sh

/venv/server/bin/python /app/server/manage.py migrate -v0
/venv/server/bin/python /app/server/manage.py sqlflush \
    | /venv/server/bin/python /app/server/manage.py dbshell  > /dev/null
cat <<'EOF' | /venv/server/bin/python /app/server/manage.py shell
import json
import os

from django.contrib.auth.models import User

User.objects.create_superuser(username="test", password="test")

os.mkdir('/root/.tomato')
json.dump({'hostname': 'localhost:8000', 'protocol': 'http'},
          open('/root/.tomato/config.json', 'w'))
EOF

supervisord -c /etc/supervisor/supervisord.conf

if [ "$#" -gt 0 ]; then
    exec $@
else
    exec bash
fi
