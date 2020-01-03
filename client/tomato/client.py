import datetime
import glob
import os
import shutil
import sys

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

    def __call__(self, filename):
        template = self.env.get_template(filename)
        static_prefix = f'file://{self.STATIC_DIR}/'

        base_font_path = os.path.join(self.STATIC_DIR, 'fonts')
        files = glob.glob(f'{base_font_path}/**/*.*', recursive=True)
        fonts = []
        for file in files:
            font = file[len(base_font_path) + 1:]
            url = f'{static_prefix}fonts/{font}'
            fonts.append((os.path.splitext(os.path.basename(font))[0], url))

        fonts.sort(key=lambda f: f[0].lower())

        kwargs = {
            'STATIC': static_prefix,
            'SOUNDS': f'file://{self.SOUNDS_DIR}/',
            'PATH': f'{Client.RENDER_PREFIX}{filename}',
            'fonts': fonts,
        }

        html = template.render(kwargs)
        path = os.path.join(self.RENDERED_TEMPLATE_DIR, filename)

        with open(path, 'w') as file:
            file.write(html)

        return path


render_template = __RenderTemplate()


class ClientHandler:
    def DoClose(self, browser):
        cefpython.QuitMessageLoop()

    def OnBeforeResourceLoad(self, browser, frame, request):
        url = request.GetUrl()
        if url.startswith(Client.RENDER_PREFIX):
            template = url[len(Client.RENDER_PREFIX):]
            path = render_template(template)
            print(f'{datetime.datetime.now()} Rendered {template} => {path}')
            request.SetUrl(f'file://{path}')

            print(f'{datetime.datetime.now()} Post Data: {request.GetPostData()}')
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
        browser.LoadUrl(f'{self.RENDER_PREFIX}login.html')
        cefpython.MessageLoop()
        cefpython.Shutdown()

    def run(self):
        try:
            self.create_window()
        finally:
            for dirname in ('blob_storage', 'webrtc_event_logs', 'webcache'):
                shutil.rmtree(dirname, ignore_errors=True)
