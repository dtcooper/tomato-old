#!/usr/bin/env python3

import json
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

from . import constants
from .constants import APIException
from .config import Config

if constants.IS_WINDOWS:
    import ctypes
    import win32api
    import win32con
    import win32gui

if constants.IS_MACOS:
    import AppKit

if constants.IS_LINUX:
    import Xlib.display
    import Xlib.Xutil
    import ewmh


APP_HTML_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'app.html')

logger = logging.getLogger('tomato')


class ClientHandler:
    def __init__(self):
        self._conf = Config()
        self._dom_loaded = False
        self._should_close = False

    def OnConsoleMessage(self, browser, level, message, source, line):
        logger.info(f'{source}:{line}:console.log() - {message}')
        return False

    def OnBeforePopup(self, target_url, **kwargs):
        webbrowser.open(target_url)
        return True

    def OnLoadStart(self, browser, **kwargs):
        browser.ExecuteJavascript('''
            if (document.readyState === 'complete') {
                cef.bridge.dom_loaded();
            } else {
                document.addEventListener('DOMContentLoaded', function() {
                    cef.bridge.dom_loaded();
                });
            }
        ''')

    def DoClose(self, browser):
        if self._should_close or not self._dom_loaded or self._conf.debug:
            if constants.IS_MACOS:
                # macOS doesn't quit message loop when the window closes, so app
                # remains in dock for no good reason. So we quit it manually.
                cef.QuitMessageLoop()
            return False
        else:
            browser.ExecuteFunction('cef.close')
            return True


class JSBridge:
    def __init__(self, browser, client_handler, js_api_list, _window=None, _linux_ewmh=None):
        self.conf = Config()
        self.browser = browser
        self.client_handler = client_handler
        self.js_apis = {}  # namespace -> (api, call_queue)
        self.threads = []

        self._window = _window
        self._linux_ewmh = _linux_ewmh

        for js_api in js_api_list:
            namespace = js_api.namespace
            self.js_apis[namespace] = args = (js_api, queue.Queue())
            thread = threading.Thread(name=f'{namespace}', target=self._run_call_thread, args=args)
            thread.daemon = True  # Thread won't block program from exiting
            thread.start()
            self.threads.append(thread)

    def call(self, namespace, method, resolve, reject, args):
        _, call_queue = self.js_apis[namespace]
        call_queue.put((method, resolve, reject, args))

    def _shutdown(self):
        for _, call_queue in self.js_apis.values():
            call_queue.put(None)

        for thread in self.threads:
            thread.join(1.5)  # Wait a half 1.5 seconds for daemon thread to terminate cleanly
            if thread.is_alive():
                logger.info(f"JSBridge call thread didn't exit cleanly ({thread.name})")

    @staticmethod
    def _run_call_thread(js_api, queue):
        namespace = js_api.namespace
        logger.info(f'JSBridge call thread booting ({namespace})')

        while True:
            queue_message = queue.get()  # Blocks
            if queue_message is None:
                break

            method, resolve, reject, args = queue_message
            pretty_args = ", ".join(map(repr, args)) if args else ""

            try:
                response = getattr(js_api, method)(*args)
            except APIException as e:
                logger.exception(f'APIException raised by cef.{namespace}.{method}({pretty_args})')
                reject.Call((str(e),))  # todo: null if unexpected, string if expected
            except Exception:
                logger.exception(f'Unexpected exception raised by cef.{namespace}.{method}({pretty_args})')
                reject.Call(('An unexpected error occurred.',))
            else:
                logger.info(f'Called cef.{namespace}.{method}'
                            f'({", ".join(map(repr, args)) if args else ""}) -> {response!r}')
                if not isinstance(response, (list, tuple)):
                    response = (response,)
                resolve.Call(response)

        logger.info(f'JSBridge call thread exiting ({namespace})')

    def dom_loaded(self):
        self.browser.ExecuteJavascript(
            f'cef.constants = {json.dumps({c: getattr(constants, c) for c in dir(constants) if c.isupper()})}')

        for namespace, (js_api, _) in self.js_apis.items():
            self.browser.ExecuteJavascript(f'cef.{namespace} = {{}}')
            for method in dir(js_api):
                if not method.startswith('_') and inspect.ismethod(getattr(js_api, method)):
                    self.browser.ExecuteJavascript(f'''
                        cef.{namespace}.{method} = function() {{
                            var args = Array.from(arguments);
                            return new Promise(function(resolve, reject) {{
                                cef.bridge.call('{namespace}', '{method}', resolve, reject, args);
                            }});
                        }}
                    ''')

        self.browser.ExecuteJavascript("window.dispatchEvent(new CustomEvent('cefReady'))")
        self.client_handler._dom_loaded = True

    def close_browser(self):
        self.client_handler._should_close = True
        self.browser.SendFocusEvent(True)
        self.browser.TryCloseBrowser()

    def windows_resize(self):
        rect = win32gui.GetWindowRect(self._window)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        logger.info(f'Got Windows resize event: {width}x{height}')
        self.conf.update(width=width, height=height)

    def toggle_fullscreen(self):
        if constants.IS_WINDOWS:
            self.browser.ToggleFullscreen()

        elif constants.IS_MACOS:
            # Need to figure out 1<<7 ?
            # https://github.com/r0x0r/pywebview/blob/master/webview/platforms/cocoa.py
            self._window.setCollectionBehavior_(1 << 7)
            self._window.toggleFullScreen_(None)

        elif constants.IS_LINUX:
            self._linux_ewmh.setWmState(self._window, 2, '_NET_WM_STATE_FULLSCREEN')
            self._linux_ewmh.display.flush()


def run_cef_window(*js_api_list):
    logger.info('Initializing CEF window')
    conf = Config()

    sys.excepthook = cef.ExceptHook

    switches = {
        'autoplay-policy': 'no-user-gesture-required',  # Allow audio to play with no gesture
        'enable-media-stream': '',  # Get device names from `mediaDevices.enumerateDevices();'
        'enable-font-antialiasing': '',  # Better fonts in some cases on Windows
    }
    settings = {
        'background_color': 0xFFDDDDDD,
        'context_menu': {'enabled': False},
        'debug': False,
        'remote_debugging_port': -1,
    }

    if conf.debug:
        settings.update({
            'context_menu': {'enabled': True, 'external_browser': False,
                             'print': False, 'view_source': False},
            'debug': True,
            'remote_debugging_port': 0,
        })

    max_width = max_height = float('inf')
    window = linux_ewmh = None
    if constants.IS_WINDOWS:
        max_width, max_height = map(win32api.GetSystemMetrics,
                                    (win32con.SM_CXFULLSCREEN, win32con.SM_CYFULLSCREEN))
    elif constants.IS_MACOS:
        frame_size = AppKit.NSScreen.mainScreen().frame().size
        max_width, max_height = map(int, (frame_size.width, frame_size.height))

    elif constants.IS_LINUX:
        linux_ewmh = ewmh.EWMH()
        desktop = linux_ewmh.getCurrentDesktop()
        max_width, max_height = linux_ewmh.getWorkArea()[4 * desktop + 2:4 * (desktop + 1)]

    width = min(conf.width, max_width)
    height = min(conf.height, max_height)
    # 15 pixel buffer between max screen dimension, for maximizing window
    should_maximize = width >= (max_width - 15) or height >= (max_height - 15)
    logger.info(f'Dimensions: {width}x{height} [{max_width}x{max_height} max], '
                f'will maximize: {should_maximize}')

    try:
        cef.Initialize(switches=switches, settings=settings)

        if constants.IS_WINDOWS:
            cef.DpiAware.EnableHighDpiSupport()

        window_info = cef.WindowInfo()
        window_info.SetAsChild(0, [0, 0, width, height])

        browser = cef.CreateBrowserSync(
            window_title='Tomato Radio Automation',
            window_info=window_info,
        )

        if constants.IS_WINDOWS:
            window = browser.GetOuterWindowHandle()
            win32gui.SetWindowPos(window, 0, (max_width - width) // 2,
                                  (max_height - height) // 2, width, height, 0)

            # 5 pixel buffer for maximize
            if should_maximize:
                win32gui.ShowWindow(window, win32con.SW_SHOWMAXIMIZED)

            class MINMAXINFO(ctypes.Structure):
                _fields_ = [
                    ('ptReserved', ctypes.wintypes.POINT),
                    ('ptMaxSize', ctypes.wintypes.POINT),
                    ('ptMaxPosition', ctypes.wintypes.POINT),
                    ('ptMinTrackSize', ctypes.wintypes.POINT),
                    ('ptMaxTrackSize', ctypes.wintypes.POINT),
                ]

            def window_procedure(hwnd, msg, wparam, lparam):
                if msg == win32con.WM_GETMINMAXINFO:
                    info = MINMAXINFO.from_address(lparam)
                    info.ptMinTrackSize.x = constants.WINDOW_SIZE_MIN_WIDTH
                    info.ptMinTrackSize.y = constants.WINDOW_SIZE_MIN_HEIGHT

                elif msg == win32con.WM_DESTROY:
                    # Fix hanging on close
                    win32api.SetWindowLong(window, win32con.GWL_WNDPROC, old_window_procedure)

                return win32gui.CallWindowProc(old_window_procedure, hwnd, msg, wparam, lparam)

            # Minimum window size
            old_window_procedure = win32gui.SetWindowLong(window, win32con.GWL_WNDPROC,
                                                          window_procedure)

        elif constants.IS_MACOS:
            # Start on top and centered
            AppKit.NSApp.activateIgnoringOtherApps_(True)
            window = AppKit.NSApp.windows()[0]
            window.setMinSize_(AppKit.NSSize(constants.WINDOW_SIZE_MIN_WIDTH,
                                             constants.WINDOW_SIZE_MIN_HEIGHT))
            window.center()

        elif constants.IS_LINUX:
            window_handle = browser.GetOuterWindowHandle()
            window = linux_ewmh.display.create_resource_object('window', window_handle)
            window.set_wm_normal_hints(flags=Xlib.Xutil.PMinSize,
                                       min_width=constants.WINDOW_SIZE_MIN_WIDTH,
                                       min_height=constants.WINDOW_SIZE_MIN_HEIGHT)
            linux_ewmh.display.sync()

            # 5 pixel buffer for maximize
            if should_maximize:
                linux_ewmh.setWmState(window, 2, '_NET_WM_STATE_MAXIMIZED_VERT',
                                      '_NET_WM_STATE_MAXIMIZED_HORZ')
                linux_ewmh.display.flush()

        client_handler = ClientHandler()
        browser.SetClientHandler(client_handler)

        js_bindings = cef.JavascriptBindings()
        js_bridge = JSBridge(
            browser=browser,
            client_handler=client_handler,
            js_api_list=js_api_list,
            _window=window,
            _linux_ewmh=linux_ewmh,
        )
        js_bindings.SetObject('_jsBridge', js_bridge)
        browser.SetJavascriptBindings(js_bindings)

        browser.LoadUrl(urljoin('file:', pathname2url(os.path.realpath(APP_HTML_PATH))))

        cef.MessageLoop()
        logger.info('Shutting down Tomato')

        js_bridge._shutdown()
        cef.Shutdown()

    finally:
        for dirname in ('blob_storage', 'webrtc_event_logs', 'webcache'):
            shutil.rmtree(dirname, ignore_errors=True)
