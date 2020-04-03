import os
from .utils.utils import is_windows

version_info = (0, 0, 1)
__version__ = '.'.join(map(str, version_info))

# enable ANSI escape sequences on Windows
if is_windows():
    os.system('color')
