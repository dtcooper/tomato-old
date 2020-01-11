import platform
import sys

from cefpython3 import cefpython as cef


class MacCloseHandler:
    def DoClose(self, browser):
        cef.QuitMessageLoop()


def create_browser(
    title,
    url,
    bg_color='FFFFFF',
    width=1024,
    height=768,
):
    # TODO:
    # - JS API stuff using promises, or unified way to use callbacks
    # - Windows specific stuff (WindowUtils, etc)
    # - Context menu
    # - Devtool disable/enable (not just context menu)
    # - try/catch cleaning up folders (possible settings to put these in temp dir)

    sys.excepthook = cef.ExceptHook

    switches = {
        'autoplay-policy': 'no-user-gesture-required',
    }
    settings = {
        'background_color': 0xFF000000 + int(bg_color, 16),
    }

    cef.Initialize(switches=switches, settings=settings)

    window_info = cef.WindowInfo()
    window_info.SetAsChild(0, [0, 0, width, height])

    browser = cef.CreateBrowserSync(
        url=url,
        window_title=title,
        window_info=window_info,
    )

    if platform.system() == 'Darwin':
        browser.SetClientHandler(MacCloseHandler())

    # JS api goes here, possibly load URL after if required
    # browser.LoadUrl(url)

    cef.MessageLoop()
    cef.Shutdown()


create_browser('jew pizza', 'https://jew.pizza')
