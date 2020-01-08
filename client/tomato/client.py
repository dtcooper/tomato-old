import configparser
import os
import shutil
import sys
import webbrowser

from cefpython3 import cefpython

from .auth import AuthApi
from .data import Data
from .constants import USER_DIR


class ClientHandler:
    def DoClose(self, browser):
        cefpython.QuitMessageLoop()  # Mac only?


class Client:
    WINDOW_TITLE = 'Tomato Radio Automation'
    APP_HTML_URL = 'file://' + os.path.realpath(os.path.join(
        os.path.dirname(__file__), '..', 'assets', 'app.html')).replace(os.pathsep, '/')

    def __init__(self):
        os.makedirs(USER_DIR, exist_ok=True)
        self.data = Data()

    def create_window(self):
        sys.excepthook = cefpython.ExceptHook

        cefpython.Initialize(
            switches={'autoplay-policy': 'no-user-gesture-required'},
            settings={'background_color': 0xFFB3B3B3, 'cache_path': ''})

        window_info = cefpython.WindowInfo()
        window_info.SetAsChild(0, [200, 200, 900, 600])  # Testing

        browser = cefpython.CreateBrowserSync(
            window_title=self.WINDOW_TITLE,
            window_info=window_info,
        )

        browser.SetClientHandler(ClientHandler())

        bindings = cefpython.JavascriptBindings(bindToFrames=False, bindToPopups=False)
        bindings.SetFunction('openLink', webbrowser.open)
        bindings.SetObject('auth', AuthApi(self.data, browser))
        browser.SetJavascriptBindings(bindings)

        browser.LoadUrl(self.APP_HTML_URL)
        cefpython.MessageLoop()
        cefpython.Shutdown()

    def run(self):
        try:
            self.create_window()
        finally:
            for dirname in ('blob_storage', 'webrtc_event_logs', 'webcache'):
                shutil.rmtree(dirname, ignore_errors=True)
