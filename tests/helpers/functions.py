import shlex
from collections import namedtuple
from pathlib import Path
from shutil import copy2
from subprocess import PIPE, run


def run_command(cmd):
    """helper function that formats and tests command line input"""
    # split args
    cmd = shlex.split(cmd)
    # deal with POSIX/Windows path formatting
    cmd = [str(Path(arg)) if '/' in arg else arg for arg in cmd]
    result = run(cmd, stdout=PIPE, stderr=PIPE, encoding='UTF-8')
    return result.returncode, result.stdout, result.stderr


###########################################
# custom type converters for ConfigParser #
###########################################
def _get_multiline_list(val):
    """
    splits a newline-separated list of values for a single option into a
    list
    NOTE: first item should be on a different line from the option key
    """
    return val.splitlines()[1:]


def _get_diff_list(val):
    """
    specifcally for use in the MockIndex class; splits a
    newline-separated list of values for a single option (where each
    value is comma-separated list with length 3) into a list of
    namedtuple types.
    NOTE: the resultant field names of the namedtuple correspond to the
    comma-separated values IN ORDER
    """
    Diff = namedtuple('Diff', ('a_name', 'b_name', 'change_type'))
    return [Diff(*change.split(', ')) for change in val.splitlines()[1:]]


CONVERTERS = {
    'difflist': _get_diff_list,
    'list': _get_multiline_list
}

