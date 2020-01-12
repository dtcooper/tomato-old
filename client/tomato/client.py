import os

from .auth import AuthApi
from .cef import run_cef_window
from .data import Data
from .constants import USER_DIR


class Client:
    def __init__(self):
        os.makedirs(USER_DIR, exist_ok=True)
        self.data = Data()

    def run(self):
        run_cef_window(AuthApi(data=self.data))
