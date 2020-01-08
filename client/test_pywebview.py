#!/usr/bin/env python3

import platform

import webview


webview.create_window(
    'CEF test window',
    'file:///Users/dave/tomato/client/assets/app.html',
    confirm_close=True,
)

webview_kwargs = {}

if platform.system() == 'Windows':
    webview_kwargs['gui'] = 'cef'

webview.start(debug=True, **webview_kwargs)
