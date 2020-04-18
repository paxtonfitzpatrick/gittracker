import shlex
from collections import namedtuple
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


###########################################
# custom type converters for ConfigParser #
###########################################
def _get_multiline_list(val):
    return val.splitlines()[1:]


def _get_diff_list(val):
    Diff = namedtuple('Diff', ('a_name', 'b_name', 'change_type'))
    return [Diff(*change.split(', ')) for change in val.splitlines()[1:]]


CONVERTERS = {
    'difflist': _get_diff_list,
    'list': _get_multiline_list
}