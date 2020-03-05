#!/bin/sh

supervisord -c /etc/supervisor/supervisord.conf

if [ "$#" -gt 0 ]; then
    exec $@
else
    exec bash
fi
