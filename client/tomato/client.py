import os
import platform
import shutil
import sys
import webbrowser

import webview

from .auth import AuthApi
from .data import Data
from .constants import USER_DIR


class Client:
    WINDOW_TITLE = 'Tomato Radio Automation'
    APP_HTML_URL = 'file://' + os.path.realpath(os.path.join(
        os.path.dirname(__file__), '..', 'assets', 'app.html')).replace(os.pathsep, '/')

    def __init__(self):
        os.makedirs(USER_DIR, exist_ok=True)
        self.data = Data()

    def create_window(self):
        kwargs = {'debug': True}

        if platform.system() == 'Windows':
            kwargs['gui'] = 'cef'

        webview.create_window(
            self.WINDOW_TITLE,
            self.APP_HTML_URL,
            js_api=AuthApi(data=self.data),
            width=1024,
            height=768,
            min_size=(800, 600),
            confirm_close=True,
            text_select=True,  # Handled by custom CSS
            #frameless=True,
        )
        webview.start(**kwargs)

    def run(self):
        try:
            self.create_window()
        finally:
            for dirname in ('blob_storage', 'webrtc_event_logs', 'webcache'):
                shutil.rmtree(dirname, ignore_errors=True)
