#!/usr/bin/env python3

import inspect
import io
import json
import logging
import mimetypes
import os
import pprint
import queue
import shutil
import sys
from urllib.parse import urlparse
from urllib.request import url2pathname
import threading
import traceback
import webbrowser

from cefpython3 import cefpython as cef
import jinja2

from . import constants
from .constants import (
    APIException,
    APP_URL,
    IS_LINUX,
    IS_MACOS,
    IS_WINDOWS,
    TEMPLATES_DIR,
    USER_DIR,
    WINDOW_SIZE_MIN_HEIGHT,
    WINDOW_SIZE_MIN_WIDTH,
)
from .config import Config
from .version import __version__

if IS_WINDOWS:
    import ctypes
    import win32api
    import win32con
    import win32gui

elif IS_MACOS:
    import AppKit

elif IS_LINUX:
    import Xlib.display
    import Xlib.Xutil
    import ewmh


logger = logging.getLogger('tomato')


class ResourceHandler:
    def __init__(self, client_handler):
        self.client_handler = client_handler
        self.url = self.file = None
        self.total_bytes_read = self.file_size = 0
        self.wants_content_range = False

    def ProcessRequest(self, request, callback):
        self.url = urlparse(request.GetUrl())
        self.wants_content_range = 'Range' in request.GetHeaderMap()
        callback.Continue()
        return True

    def GetResponseHeaders(self, response, response_length_out, redirect_url_out):
        file_path = url2pathname(self.url.path)

        if os.path.exists(file_path):
            headers = {'Access-Control-Allow-Origin': '*'}

            if file_path.startswith(TEMPLATES_DIR):
                template_name = file_path[len(TEMPLATES_DIR) + 1:]
                rendered = self.client_handler._cef_window.render_template(template_name)

                self.file = io.BytesIO(rendered.encode('utf-8'))
                self.file_size = len(rendered)
            else:
                self.file = open(file_path, 'rb')
                self.file_size = os.path.getsize(file_path)

            # Let's us seek audio files with MediaElement
            # https://magpcss.org/ceforum/viewtopic.php?f=6&t=13491#p27943
            if self.wants_content_range:
                status, status_text = 206, 'Partial Content'
                headers['Content-Range'] = f'bytes 0-{self.file_size - 1}/{self.file_size}'
            else:
                status, status_text = 200, 'OK'

            response.SetStatus(status)
            response.SetStatusText(status_text)
            response.SetMimeType(
                mimetypes.guess_type(file_path, strict=False)[0] or 'application/octet-stream')
            response.SetHeaderMap(headers)
            response_length_out[0] = self.file_size

        else:
            response.SetStatus(404)
            response.SetStatusText('Not Found')

    def ReadResponse(self, data_out, bytes_to_read, bytes_read_out, callback):
        has_bytes = False
        clean_up = True

        if self.total_bytes_read < self.file_size:
            bytes_read = self.file.read(bytes_to_read)
            num_bytes_read = len(bytes_read)
            has_bytes = num_bytes_read > 0

            if num_bytes_read > 0:
                has_bytes = True
                data_out[0] = bytes_read
                self.total_bytes_read += num_bytes_read
                bytes_read_out[0] = num_bytes_read

                clean_up = (self.total_bytes_read == self.file_size)

        if clean_up:
            logger.info(f'Served {self.url.geturl()} ({self.total_bytes_read} bytes)')
            self.file.close()
            self.client_handler._release_strong_resource_handler_reference(self)

        return has_bytes

    def Cancel(self):
        self.client_handler._release_strong_resource_handler_reference(self)
        self.file.close()

    def CanGetCookie(self, cookie):
        return True

    def CanSetCookie(self, cookie):
        return True


class ClientHandler:
    def __init__(self, cef_window):
        self._cef_window = cef_window
        self._conf = cef_window.conf
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
            if IS_MACOS:
                # macOS doesn't quit message loop when the window closes, so app
                # remains in dock for no good reason. So we quit it manually.
                cef.QuitMessageLoop()
            return False
        else:
            browser.ExecuteFunction('cef.close')
            return True

    _resource_handlers = set()

    def _add_strong_resource_handler_reference(self, resource_handler):
        self._resource_handlers.add(resource_handler)

    def _release_strong_resource_handler_reference(self, resource_handler):
        self._resource_handlers.discard(resource_handler)

    def GetResourceHandler(self, browser, frame, request):
        # Intercept local URLs (needed to AJAX + wavesurfer.js)
        if request.GetUrl().lower().startswith(f'http://tomato/'):
            resource_handler = ResourceHandler(self)
            self._add_strong_resource_handler_reference(resource_handler)
            return resource_handler

        else:
            return False


class JSBridge:
    def __init__(self, cef_window):
        # Make sure Django is configured before importing so model import doesn't blow up
        from .api import API_LIST

        self.cef_window = cef_window
        self.js_apis = {}  # namespace -> (api, call_queue)
        self.threads = []

        for js_api_class in API_LIST:
            js_api = js_api_class(cef_window=self.cef_window)
            namespaces = [js_api.namespace]

            for method_name in dir(js_api):
                method = getattr(js_api, method_name)
                if (
                    not method_name.startswith('_') and inspect.ismethod(method)
                    and getattr(method, 'use_own_thread', False)
                ):
                    namespaces.append(f'{js_api.namespace}::{method_name}')

            for namespace in namespaces:
                call_queue = queue.Queue()
                self.js_apis[namespace] = (js_api, call_queue)
                thread = threading.Thread(name=namespace, target=self._run_call_thread,
                                          args=(js_api, namespace, call_queue))
                thread.daemon = True  # Thread won't block program from exiting
                thread.start()
                self.threads.append(thread)

    def call(self, namespace, method, resolve, reject, args):
        _, call_queue = self.js_apis.get(f'{namespace}::{method}', self.js_apis[namespace])
        call_queue.put((method, resolve, reject, args))

    def _shutdown(self):
        for _, call_queue in self.js_apis.values():
            call_queue.put(None)

        for thread in self.threads:
            thread.join(1.5)  # Wait a half 1.5 seconds for daemon thread to terminate cleanly
            if thread.is_alive():
                logger.info(f"JSBridge call thread didn't exit cleanly ({thread.name})")

    @staticmethod
    def _run_call_thread(js_api, namespace, queue):
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
                reject.Call((str(e),) + e.extra_args)  # todo: null if unexpected, string if expected
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
        self.cef_window.client_handler._dom_loaded = True

    def close_browser(self):
        self.cef_window.client_handler._should_close = True
        self.cef_window.browser.SendFocusEvent(True)
        self.cef_window.browser.TryCloseBrowser()

    def windows_resize(self):
        rect = win32gui.GetWindowRect(self.cef_window.window_handle)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        logger.info(f'Got Windows resize event: {width}x{height}')
        self.cef_window.conf.update(width=width, height=height)

    def toggle_fullscreen(self):
        if IS_WINDOWS:
            self.cef_window.browser.ToggleFullscreen()

        elif IS_MACOS:
            # Need to figure out 1<<7 ?
            # https://github.com/r0x0r/pywebview/blob/master/webview/platforms/cocoa.py
            self.cef_window.window.setCollectionBehavior_(1 << 7)
            self.cef_window.window.toggleFullScreen_(None)

        elif IS_LINUX:
            self.cef_window.ewmh.setWmState(self.cef_window.window, 2, '_NET_WM_STATE_FULLSCREEN')
            self.cef_window.ewmh.display.flush()


class CefWindow:
    WINDOW_TITLE = 'Tomato Radio Automation'

    def __init__(self):
        self.conf = Config()
        self.ewmh = None
        self.x_pos = self.y_pos = self.width = self.height = None
        self.should_maximize = None
        self.browser = None
        self.window = None
        self.window_handle = None
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath=TEMPLATES_DIR),
            autoescape=jinja2.select_autoescape(['html']),
        )
        self.template_env.filters['prettyduration'] = lambda seconds: (
            f'{round(seconds) // 60}:{round(seconds) % 60:02}')

    def init_platform(self):
        if IS_LINUX:
            self.ewmh = ewmh.EWMH()

    def init_window_dimensions(self):
        if IS_WINDOWS:
            max_width, max_height = map(win32api.GetSystemMetrics,
                                        (win32con.SM_CXFULLSCREEN, win32con.SM_CYFULLSCREEN))
        elif IS_MACOS:
            frame_size = AppKit.NSScreen.mainScreen().frame().size
            max_width, max_height = map(int, (frame_size.width, frame_size.height))
        elif IS_LINUX:
            desktop = self.ewmh.getCurrentDesktop()
            max_width, max_height = self.ewmh.getWorkArea()[4 * desktop + 2:4 * (desktop + 1)]

        self.width = min(self.conf.width, max_width)
        self.height = min(self.conf.height, max_height)
        self.x_pos, self.y_pos = (max_width - self.width) // 2, (max_height - self.height) // 2

        # 15 pixel buffer between max screen dimension, for maximizing window
        self.should_maximize = self.width >= (max_width - 15) or self.height >= (max_height - 15)
        logger.info(f'Dimensions: {self.width}x{self.height} [{max_width}x{max_height} max] '
                    f'@ ({self.x_pos}, {self.y_pos}), will maximize: {self.should_maximize}')

    def get_cef_initialize_kwargs(self):
        kwargs = {
            'switches': {
                'autoplay-policy': 'no-user-gesture-required',  # Allow audio to play with no gesture
                'enable-media-stream': '',  # Get device names from `mediaDevices.enumerateDevices();'
                'enable-font-antialiasing': '',  # Better fonts in some cases on Windows
            },
            'settings': {
                'background_color': 0xFFDDDDDD,
                'cache_path': os.path.join(USER_DIR, 'cef_cache'),
                'context_menu': {'enabled': False},
                'debug': False,
                'remote_debugging_port': -1,
            },
        }

        if self.conf.debug:
            kwargs['settings'].update({
                'context_menu': {'enabled': True, 'external_browser': False,
                                 'print': False, 'view_source': False},
                'debug': True,
                'remote_debugging_port': 6969,
            })

        return kwargs

    def render_template(self, template_name, context=None):
        default_context = {}

        # Performance: if we're rendering the app.html we add custom context here
        if template_name == 'app.html':
            # Make sure Django is configured before importing so model import doesn't blow up
            from .api import API_LIST

            default_context.update({
                'conf': self.conf.data,
                'constants': {c: getattr(constants, c) for c in dir(constants) if c.isupper()},
                'js_apis': {
                    api.namespace: [
                        method for method in dir(api)
                        if not method.startswith('_') and callable(getattr(api, method))
                    ] for api in API_LIST
                }
            })

        if context is not None:
            default_context.update(context)

        try:
            template = self.template_env.get_template(template_name)
            rendered = template.render(default_context)
            logger.info(f'Rendered {template_name}')
        except Exception as exc:
            logger.exception(f'Error rendering template {template_name}')
            template = jinja2.Template(
                '<html><body><h1>{{ title }}</h1><pre>{{ exc }}</pre></body></html>', autoescape=True)
            rendered = template.render({'title': exc, 'exc': traceback.format_exc()})

        if self.conf.print_html:
            print(f' {template_name} '.center(40, '-'))
            pprint.pprint(default_context)
            print('-' * 40)
            print(rendered)
            print('-' * 40)
        return rendered

    def on_conf_update(self, conf):
        self.browser.ExecuteJavascript(f'cef.conf = {json.dumps(conf)};')

    def init_window(self):
        self.window_handle = self.browser.GetOuterWindowHandle()

        if IS_WINDOWS:
            # Windows needs this additional call to set its window position
            win32gui.SetWindowPos(self.window_handle, 0, self.x_pos, self.y_pos,
                                  self.width, self.height, 0)

            if self.should_maximize:
                win32gui.ShowWindow(self.window_handle, win32con.SW_SHOWMAXIMIZED)

            # Below sets minimum window dimensions

            class MINMAXINFO(ctypes.Structure):
                _fields_ = [
                    ('ptReserved', ctypes.wintypes.POINT),
                    ('ptMaxSize', ctypes.wintypes.POINT),
                    ('ptMaxPosition', ctypes.wintypes.POINT),
                    ('ptMinTrackSize', ctypes.wintypes.POINT),
                    ('ptMaxTrackSize', ctypes.wintypes.POINT),
                ]

            def window_procedure(window_handle, mesg_type, w_param, l_param):
                if mesg_type == win32con.WM_GETMINMAXINFO:
                    info = MINMAXINFO.from_address(l_param)
                    info.ptMinTrackSize.x = WINDOW_SIZE_MIN_WIDTH
                    info.ptMinTrackSize.y = WINDOW_SIZE_MIN_HEIGHT

                elif mesg_type == win32con.WM_DESTROY:
                    # Fix hanging on close
                    win32api.SetWindowLong(self.window_handle, win32con.GWL_WNDPROC, old_window_procedure)

                return win32gui.CallWindowProc(old_window_procedure, window_handle, mesg_type, w_param, l_param)

            # Reference above
            old_window_procedure = win32gui.SetWindowLong(self.window_handle,
                                                          win32con.GWL_WNDPROC, window_procedure)

        elif IS_MACOS:
            # Start on top and centered
            AppKit.NSApp.activateIgnoringOtherApps_(True)
            self.window = AppKit.NSApp.windows()[0]
            self.window.setMinSize_(AppKit.NSSize(WINDOW_SIZE_MIN_WIDTH,
                                                  WINDOW_SIZE_MIN_HEIGHT))
            self.window.center()

        elif IS_LINUX:
            self.window = self.ewmh.display.create_resource_object('window', self.window_handle)
            self.window.set_wm_normal_hints(flags=Xlib.Xutil.PMinSize,
                                            min_width=WINDOW_SIZE_MIN_WIDTH,
                                            min_height=WINDOW_SIZE_MIN_HEIGHT)
            self.ewmh.display.sync()

            # 5 pixel buffer for maximize
            if self.should_maximize:
                self.ewmh.setWmState(self.window, 2, '_NET_WM_STATE_MAXIMIZED_VERT', '_NET_WM_STATE_MAXIMIZED_HORZ')
                self.ewmh.display.flush()

    def run(self):
        logger.info('Running CEF window')
        original_excepthook, sys.excepthook = sys.excepthook, cef.ExceptHook

        try:
            self.init_platform()
            self.init_window_dimensions()

            if IS_WINDOWS:
                logger.info('Enabling high DPI support for Windows')
                cef.DpiAware.EnableHighDpiSupport()

            logger.info('Initializing CEF window')
            cef.Initialize(**self.get_cef_initialize_kwargs())

            window_info = cef.WindowInfo()
            window_info.SetAsChild(0, [self.x_pos, self.y_pos, self.width, self.height])

            self.browser = cef.CreateBrowserSync(
                window_title=self.WINDOW_TITLE,
                window_info=window_info,
            )

            self.init_window()
            self.conf.register_on_update(self.on_conf_update)

            self.client_handler = ClientHandler(self)
            self.browser.SetClientHandler(self.client_handler)

            js_bindings = cef.JavascriptBindings()
            self.js_bridge = JSBridge(self)
            js_bindings.SetObject('_jsBridge', self.js_bridge)
            self.browser.SetJavascriptBindings(js_bindings)

            logger.info(f'Loading URL: {APP_URL}')
            self.browser.LoadUrl(APP_URL)

            cef.MessageLoop()

            logger.info('Shutting down')
            self.js_bridge._shutdown()
            cef.Shutdown()

            if self.client_handler._resource_handlers:
                logger.warn(f'{len(self.client_handler._resource_handlers)} ResourceHandlers exist, possible memleak!')

        finally:
            sys.excepthook = original_excepthook

            for dirname in ('blob_storage', 'webrtc_event_logs', 'webcache'):
                shutil.rmtree(dirname, ignore_errors=True)
