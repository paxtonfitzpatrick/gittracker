import os
from .util.util import is_windows
from .version import version_info, __version__

# enable ANSI escape sequences on Windows
if is_windows():
    os.system('color')