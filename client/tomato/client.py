import os

from .auth import AuthApi
from .cef import run_cef_window
from .data import Data, DataApi
from .constants import USER_DIR


class Client:
    def __init__(self):
        os.makedirs(USER_DIR, exist_ok=True)

    def run(self):
        data = Data()
        js_api_list = (
            AuthApi(data=data),
            DataApi(data=data),
        )

        run_cef_window(debug=data.debug, js_api_list=js_api_list)
