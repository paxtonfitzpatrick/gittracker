import shlex
from pathlib import PurePath
from subprocess import PIPE, run


def run_command(cmd):
    # helper function that formats and tests command line input
    # split args
    cmd = shlex.split(cmd)
    # deal with POSIX/Windows path formatting
    cmd = [str(PurePath(arg)) if '/' in arg else arg for arg in cmd]
    result = run(cmd, stdout=PIPE, stderr=PIPE, encoding='UTF-8')
    return result.returncode, result.stdout, result.stderr
