#!/usr/bin/env python3

import shutil

from tomato import Client


if __name__ == '__main__':
    client = Client()
    try:
        client.run()
    finally:
        for dirname in ('blob_storage', 'webrtc_event_logs', 'webcache'):
            shutil.rmtree(dirname, ignore_errors=True)
