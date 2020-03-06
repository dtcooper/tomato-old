#!/bin/sh

/venv/server/bin/python /app/server/manage.py migrate -v0
/venv/server/bin/python /app/server/manage.py sqlflush \
    | /venv/server/bin/python /app/server/manage.py dbshell  > /dev/null
cat <<'EOF' | /venv/server/bin/python /app/server/manage.py shell
from django.contrib.auth.models import User
User.objects.create_superuser(username="test", password="test")
EOF

supervisord -c /etc/supervisor/supervisord.conf

if [ "$#" -gt 0 ]; then
    exec $@
else
    exec bash
fi
