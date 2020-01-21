#!/usr/bin/env python3

import inspect
import logging
import sys
import os
import queue
import shutil
from urllib.parse import urljoin
from urllib.request import pathname2url
import webbrowser
import threading

from cefpython3 import cefpython as cef

from .config import Config
from .constants import (
    IS_MACOS, IS_WINDOWS, WINDOW_SIZE_DEFAULT_WIDTH, WINDOW_SIZE_DEFAULT_HEIGHT)


if IS_WINDOWS:
    import ctypes
if IS_MACOS:
    import AppKit


if hasattr(sys, 'frozen') and IS_WINDOWS:
    APP_HTML_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'app.html')
else:
    APP_HTML_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'app.html')

logger = logging.getLogger('tomato')


class ClientHandler:
    def __init__(self):
        self._conf = Config()
        self._dom_loaded = False
        self._should_close = False

    def OnConsoleMessage(self, browser, level, message, source, line):
        logger.info(f'console.log({source}:{line}) - {message}')
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
        if self._should_close or not self._dom_loaded or self._conf.debug:
            if IS_MACOS:
                cef.QuitMessageLoop()
            return False
        else:
            browser.ExecuteFunction('cef.client.close')
            return True


class JSBindings:
    def __init__(self, browser, client_handler, js_api_list, _mac_window=None):
        self.browser = browser
        self.client_handler = client_handler
        self.js_apis = {}  # namespace -> (api, call_queue)
        self._mac_window = _mac_window

        for js_api in js_api_list:
            self.js_apis[js_api.namespace] = args = (js_api, queue.Queue())
            threading.Thread(target=self._run_call_thread, args=args).start()

    def call(self, namespace, method, args):
        self.js_apis[namespace][1].put((method, args))

    def _shutdown(self):
        for _, call_queue in self.js_apis.values():
            call_queue.put(None)

    @staticmethod
    def _run_call_thread(js_api, queue):
        namespace = js_api.namespace
        logger.info(f'JS call thread booting ({js_api.namespace})')

        while True:
            mesg = queue.get()
            if mesg is None:
                break

            method, args = mesg
            callback = None  # Optional last argument to be a callback for a response
            if len(args) >= 1 and isinstance(args[-1], cef.JavascriptCallback):
                callback = args.pop()

            # TODO: wrap in try/except so an exception in a thread doesn't kill everything
            response = getattr(js_api, method)(*args)

            if method == 'login':
                args[-1] = '********'  # Censor password
            logger.info(f'Called cef.{namespace}.{method}'
                        f'({", ".join(map(repr, args)) if args else ""}) -> {response!r}')

            if callback:
                if not isinstance(response, (list, tuple)):
                    response = (response,)
                callback.Call(*response)
        logger.info(f'JS call thread exiting ({namespace})')

    def dom_loaded(self):
        if IS_WINDOWS:
            self.browser.ExecuteJavascript('cef.is_windows = true')
        elif IS_MACOS:
            self.browser.ExecuteJavascript('cef.is_macos = true')

        for namespace, (js_api, _) in self.js_apis.items():
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

        if IS_MACOS:
            # Need to figure out 1<<7 ?
            # https://github.com/r0x0r/pywebview/blob/master/webview/platforms/cocoa.py
            self._mac_window.setCollectionBehavior_(1 << 7)
            self._mac_window.toggleFullScreen_(None)


def run_cef_window(*js_api_list):
    conf = Config()

    # TODO:
    # - Windows specific stuff (WindowUtils, etc)
    # - Context menu
    # - Devtool disable/enable (not just context menu)
    sys.excepthook = cef.ExceptHook

    switches = {
        'autoplay-policy': 'no-user-gesture-required',
        'enable-font-antialiasing': '',
    }
    settings = {
        'background_color': 0xFFDDDDDD,
        'context_menu': {'enabled': False},
        'debug': False,
        'remote_debugging_port': -1,
    }

    if conf.debug:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        logger.info(f'Starting Tomato with configuration: {dict(conf)}')

        settings.update({
            'context_menu': {'enabled': True, 'external_browser': False,
                             'print': False, 'view_source': False},
            'debug': True,
            'remote_debugging_port': 0,
        })

    max_width = max_height = float('inf')
    if IS_WINDOWS:
        max_width, max_height = map(ctypes.windll.user32.GetSystemMetrics, (16, 17))
    elif IS_MACOS:
        frame_size = AppKit.NSScreen.mainScreen().frame().size
        max_width, max_height = map(int, (frame_size.width, frame_size.height))
    width, height = min(conf.width, max_width), min(conf.height, max_height)

    try:
        cef.Initialize(switches=switches, settings=settings)

        if IS_WINDOWS:
            cef.DpiAware.EnableHighDpiSupport()

        window_info = cef.WindowInfo()
        window_info.SetAsChild(0, [0, 0, width, height])

        browser = cef.CreateBrowserSync(
            window_title='Tomato Radio Automation',
            window_info=window_info,
        )

        if IS_WINDOWS:
            # Maximize, based on
            # https://github.com/cztomczak/cefpython/blob/master/examples/snippets/window_size.py
            window_handle = browser.GetOuterWindowHandle()

            # 5 pixel buffer for maximize
            if width >= (max_width - 5) and height >= (max_height - 5):
                # Maximized with default minimize height
                ctypes.windll.user32.SetWindowPos(window_handle, 0, 0, 0,
                                                  WINDOW_SIZE_DEFAULT_WIDTH, WINDOW_SIZE_DEFAULT_HEIGHT, 0x0002)
                ctypes.windll.user32.ShowWindow(window_handle, 3)
            else:
                ctypes.windll.user32.SetWindowPos(window_handle, 0, 0, 0, width, height, 0x0002)

            #ctypes.windll.user32.SetWindowLongW(window_handle, GWL_WNDPROC, WndProcType(self.MyWndProc))

        mac_window = None
        if IS_MACOS:
            # Start on top and centered
            AppKit.NSApp.activateIgnoringOtherApps_(True)
            mac_window = AppKit.NSApp.windows()[0]
            mac_window.center()

        client_handler = ClientHandler()
        browser.SetClientHandler(client_handler)

        js_bindings_cef = cef.JavascriptBindings()
        js_bindings = JSBindings(
            browser=browser,
            client_handler=client_handler,
            js_api_list=js_api_list,
            _mac_window=mac_window,
        )
        js_bindings_cef.SetObject('_cefInternal', js_bindings)
        browser.SetJavascriptBindings(js_bindings_cef)

        # TODO: if hasattr(sys, 'frozen') for built
        browser.LoadUrl(urljoin('file:', pathname2url(os.path.realpath(APP_HTML_PATH))))

        cef.MessageLoop()
        logger.info('Shutting down Tomato')

        js_bindings._shutdown()
        cef.Shutdown()

    finally:
        for dirname in ('blob_storage', 'webrtc_event_logs', 'webcache'):
            shutil.rmtree(dirname, ignore_errors=True)
