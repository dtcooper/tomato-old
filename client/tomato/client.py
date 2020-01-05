import datetime
import glob
import os
import shutil
import sys
import webbrowser

from cefpython3 import cefpython
import jinja2


class __RenderTemplate:
    STATIC_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    TEMPLATE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    RENDERED_TEMPLATE_DIR = os.path.join(os.path.expanduser('~'), '.tomato', 'rendered')
    SOUNDS_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..', 'testing', 'sample_sounds'))

    def __init__(self):
        loader = jinja2.FileSystemLoader(searchpath=self.TEMPLATE_DIR)
        self.env = jinja2.Environment(loader=loader)
        os.makedirs(self.RENDERED_TEMPLATE_DIR, exist_ok=True)

    def __call__(self, filename, kwargs=None):
        template = self.env.get_template(filename)
        static_prefix = f'file://{self.STATIC_DIR}/'

        base_font_path = os.path.join(self.STATIC_DIR, 'fonts')
        files = glob.glob(f'{base_font_path}/**/*.*', recursive=True)
        fonts = []
        for file in files:
            font = file[len(base_font_path) + 1:]
            name = os.path.splitext(os.path.basename(font))[0]
            if font.startswith('candidates'):
                name = f'[candidate] {name}'
            url = f'{static_prefix}fonts/{font}'
            fonts.append((name, url))

        fonts.sort(key=lambda f: f[0].lower())

        default_kwargs = {
            'STATIC': static_prefix,
            'SOUNDS': f'file://{self.SOUNDS_DIR}/',
            'PATH': f'{Client.RENDER_PREFIX}{filename}',
            'YEAR': datetime.date.today().strftime('%Y'),
            'fonts': fonts,
        }
        if kwargs:
            default_kwargs.update(kwargs)

        html = template.render(default_kwargs)
        print(html)
        path = os.path.join(self.RENDERED_TEMPLATE_DIR, filename)

        with open(path, 'w') as file:
            file.write(html)

        return path


render_template = __RenderTemplate()


class ClientHandler:
    def DoClose(self, browser):
        cefpython.QuitMessageLoop()

    def OnBeforeBrowse(self, browser, frame, request, user_gesture, is_redirect):
        return request.GetUrl().startswith('open://')

    def OnBeforeResourceLoad(self, browser, frame, request):
        url = request.GetUrl()
        if url.startswith(Client.RENDER_PREFIX):
            template = url[len(Client.RENDER_PREFIX):]
            kwargs = {}

            post_data = request.GetPostData()
            if b'font' in post_data:
                kwargs['font'] = post_data[b'font'].decode()

            path = render_template(template, kwargs)
            print(f'{datetime.datetime.now()} Rendered {template} => {path}')
            request.SetUrl(f'file://{path}')

        else:
            print(f'{datetime.datetime.now()} Loading {url}')

        return False


class Client:
    WINDOW_TITLE = 'Tomato Radio Automation'
    RENDER_PREFIX = 'file://tomato/render/'

    def create_window(self):
        sys.excepthook = cefpython.ExceptHook

        cefpython.Initialize(switches={'autoplay-policy': 'no-user-gesture-required'})

        window_info = cefpython.WindowInfo()
        window_info.SetAsChild(0, [200, 200, 900, 600])  # Testing

        browser = cefpython.CreateBrowserSync(
            window_title=self.WINDOW_TITLE,
            window_info=window_info,
        )

        browser.SetClientHandler(ClientHandler())

        bindings = cefpython.JavascriptBindings(bindToFrames=False, bindToPopups=False)
        bindings.SetFunction('open_link', webbrowser.open)
        browser.SetJavascriptBindings(bindings)

        browser.LoadUrl(f'{self.RENDER_PREFIX}login.html')
        cefpython.MessageLoop()
        cefpython.Shutdown()

    def run(self):
        try:
            self.create_window()
        finally:
            for dirname in ('blob_storage', 'webrtc_event_logs', 'webcache'):
                shutil.rmtree(dirname, ignore_errors=True)
