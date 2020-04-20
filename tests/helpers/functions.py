import pickle
import shlex
from collections import namedtuple
from pathlib import Path
from shutil import copy2
from subprocess import PIPE, run


# holds config files (name format: `repo-<repo_name>.cfg`)
REPO_CONFIGS_DIR = Path(__file__).resolve().parent.joinpath('repo-configs')
# holds mocked repositories
MOCK_REPOS_DIR = REPO_CONFIGS_DIR.parent.joinpath('mock-repos')
# holds data files of expected test output (name format `<repo_name>.p`)
MOCK_OUTPUT_DIR = REPO_CONFIGS_DIR.parent.joinpath('expected-output')


def run_command(cmd):
    """helper function that formats and tests command line input"""
    # split args
    cmd = shlex.split(cmd)
    # deal with POSIX/Windows path formatting
    cmd = [str(Path(arg)) if '/' in arg else arg for arg in cmd]
    result = run(cmd, stdout=PIPE, stderr=PIPE, encoding='UTF-8')
    return result.returncode, result.stdout, result.stderr


def add_config(filename, dest_dir):
    src = REPO_CONFIGS_DIR.joinpath(filename)
    assert src.is_file()
    assert dest_dir.is_dir()
    copy2(src, dest_dir)


def matches_expected_output(test_output, repo_name):
    output_filepath = MOCK_OUTPUT_DIR.joinpath(f"{repo_name}.p")
    with output_filepath.open('rb') as f:
        expected_output = pickle.load(f)

    return test_output == expected_output


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


def _get_dict(val):
    """
    splits a newline separated list of values for a single option
    (where each option takes the format `sub-option = sub-value`) into a
    dictionary with the format `{sub-option: sub-value}`
    NOTE: first item should be on a different line from the option key
    """
    keys_vals = val.splitlines()[1:]
    return {k: v for k, v in map(lambda x: x.split(' = '), keys_vals)}


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
    'dict': _get_dict,
    'list': _get_multiline_list
}

