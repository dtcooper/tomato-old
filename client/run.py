#!/usr/bin/env python3

import os  # XXX
os.environ['TOMATO_DEBUG'] = '1'

from tomato import Client  # noqa


if __name__ == '__main__':
    client = Client()
    client.run()
