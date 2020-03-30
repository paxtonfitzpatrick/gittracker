import os
from .util.util import is_windows

# enable ANSI escape sequences on Windows
if is_windows():
    os.system('color')