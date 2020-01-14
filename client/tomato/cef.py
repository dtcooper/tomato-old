#!/usr/bin/env python3

import inspect
import platform
import sys
import os
import shutil
from urllib.parse import urljoin
from urllib.request import pathname2url
import webbrowser

from cefpython3 import cefpython as cef

from .constants import STARTUP_WINDOW_SIZE


IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'

if hasattr(sys, 'frozen') and IS_WINDOWS:
    APP_HTML_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'app.html')
else:
    APP_HTML_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'app.html')


class ClientHandler:
    def __init__(self):
        self._dom_loaded = False
        self._should_close = False

    def OnConsoleMessage(self, browser, level, message, source, line):
        # TODO: logger
        print(f'{source}:{line} - {message}')
        return False

    def OnBeforePopup(self, target_url, **kwargs):
        webbrowser.open(target_url)
        return True

    def OnLoadStart(self, browser, **kwargs):
        browser.ExecuteJavascript('''
            if (document.readyState === 'complete') {
                cef.internal.dom_loaded();
            } else {
                document.addEventListener('DOMContentLoaded', function() {
                    cef.internal.dom_loaded();
                });
            }
        ''')

    def DoClose(self, browser):
        if self._dom_loaded and not self._should_close:
            browser.ExecuteFunction('cef.client.showCloseModal')
            return True
        else:
            if IS_MACOS:
                cef.QuitMessageLoop()
            return False


class JSBindings:
    def __init__(self, browser, client_handler, js_api_list):
        self.browser = browser
        self.client_handler = client_handler
        self.js_api_list = {js_api.namespace: js_api for js_api in js_api_list}

    def call(self, namespace, method, args):
        method = getattr(self.js_api_list[namespace], method)
        callback = None

        # Allow for last argument to be a callback for a response
        if len(args) >= 1:
            if isinstance(args[-1], cef.JavascriptCallback):
                callback = args.pop()

        response = method(*args)
        if callback:
            if not isinstance(response, (list, tuple)):
                response = [response]
            callback.Call(*response)

    def dom_loaded(self):
        if IS_WINDOWS:
            self.browser.ExecuteJavascript('cef.is_windows = true')
        elif IS_MACOS:
            self.browser.ExecuteJavascript('cef.is_macos = true')

        for namespace, js_api in self.js_api_list.items():
            self.browser.ExecuteJavascript(f'cef.{namespace} = {{}}')
            for method in dir(js_api):
                if not method.startswith('_') and inspect.ismethod(getattr(js_api, method)):
                    self.browser.ExecuteJavascript(f'''
                        cef.{namespace}.{method} = function() {{
                            cef.internal.call('{namespace}', '{method}', Array.from(arguments));
                        }}
                    ''')

        self.browser.ExecuteJavascript("window.dispatchEvent(new CustomEvent('cefReady'))")
        self.client_handler._dom_loaded = True

    def close_browser(self):
        self.client_handler._should_close = True
        self.browser.SendFocusEvent(True)
        self.browser.TryCloseBrowser()

    def toggle_fullscreen(self):
        if IS_WINDOWS:
            self.browser.ToggleFullscreen()


def run_cef_window(debug=False, js_api_list=()):
    # TODO:
    # - Windows specific stuff (WindowUtils, etc)
    # - Context menu
    # - Devtool disable/enable (not just context menu)

    try:
        sys.excepthook = cef.ExceptHook

        switches = {
            'autoplay-policy': 'no-user-gesture-required',
        }
        settings = {
            'background_color': 0xFFDDDDDD,
            'context_menu': {'enabled': False},
            'debug': False,
            'remote_debugging_port': -1,
        }

        if debug:  # TODO: check some DEBUG flag
            settings.update({
                'context_menu': {'enabled': True, 'external_browser': False,
                                 'print': False, 'view_source': False},
                'debug': True,
                'remote_debugging_port': 0,
            })

        cef.Initialize(switches=switches, settings=settings)

        if IS_WINDOWS:
            cef.DpiAware.EnableHighDpiSupport()

        width, height = STARTUP_WINDOW_SIZE
        window_info = cef.WindowInfo()
        window_info.SetAsChild(0, [0, 0, width, height])

        browser = cef.CreateBrowserSync(
            window_title='Tomato Radio Automation',
            window_info=window_info,
        )

        if IS_WINDOWS:
            # Maximize, based on
            # https://github.com/cztomczak/cefpython/blob/master/examples/snippets/window_size.py
            import ctypes
            ctypes.windll.user32.ShowWindow(browser.GetOuterWindowHandle(), 3)

        client_handler = ClientHandler()
        browser.SetClientHandler(client_handler)

        js_bindings = cef.JavascriptBindings()
        js_bindings.SetObject('_cefInternal', JSBindings(
            browser=browser, client_handler=client_handler, js_api_list=js_api_list))
        browser.SetJavascriptBindings(js_bindings)

        # TODO: if hasattr(sys, 'frozen') for built
        browser.LoadUrl(urljoin('file:', pathname2url(os.path.realpath(APP_HTML_PATH))))

        cef.MessageLoop()
        cef.Shutdown()

    finally:
        for dirname in ('blob_storage', 'webrtc_event_logs', 'webcache'):
            shutil.rmtree(dirname, ignore_errors=True)
