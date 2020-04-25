import pickle
import shlex
from collections import namedtuple
from configparser import ConfigParser
from pathlib import Path
from shutil import copy2
from subprocess import PIPE, run
from .constants import (
    MOCK_OUTPUT_DIR,
    REPO_CONFIGS_DIR,
    TRACKER_OUTPUT,
    InvalidConfigValue,
    MockConfigNotFound
)


def add_submodule_config(filename, dest_dir):
    src = REPO_CONFIGS_DIR.joinpath('submodule-configs', filename)
    assert src.is_file()
    assert dest_dir.is_dir()
    if not dest_dir.joinpath(filename).is_file():
        copy2(src, dest_dir)


def create_expected_output(config_path, submodule=False):
    # submodule arg used for recursive calls to set proper config
    # directory and avoid output to file
    repo_name = config_path.stem
    output_filepath = MOCK_OUTPUT_DIR.joinpath(f"{repo_name}.p")
    config = load_validate_config(config_path)

    expected = TRACKER_OUTPUT.copy()
    expected['local_branch'] = config.get('active_branch', 'name')
    expected['remote_branch'] = config.get('active_branch', 'remote_branch')
    if expected['remote_branch'] == '':
        expected['n_commits_ahead'] = None
        expected['n_commits_behind'] = None
    else:
        expected['n_commits_ahead'] = config.getint('active_branch',
                                                    'n_commits_ahead')
        expected['n_commits_behind'] = config.getint('active_branch',
                                                     'n_commits_behind')
    files_staged = config.getdifflist('repo', 'staged_changes')
    files_unstaged = config.getdifflist('repo', 'unstaged_changes')
    expected['files_untracked'] = config.getlist('repo', 'untracked_files')
    expected['n_untracked'] = len(expected['files_untracked'])
    expected['files_staged'] = [(f.change_type, f.a_path, f.b_path)
                                for f in files_staged]
    expected['n_staged'] = len(files_staged)
    expected['files_not_staged'] = [(f.change_type, f.a_path, f.b_path)
                                for f in files_unstaged]
    expected['n_not_staged'] = len(files_unstaged)

    submodules = config.getdict('submodules', 'paths_configs')
    if not any(submodules):
        expected['submodules'] = None
    else:
        expected['submodules'] = {}

    for path, config_file in submodules.items():
        expected['submodules'][path] = _create_expected_output(config_file,
                                                               submodule=True)

    if not submodule:
        with open(output_filepath, 'wb') as f:
            pickle.dump(expected, f)

    return expected


def matches_expected_output(repo_name, test_output, verbose=2, include_submodules=False):
    # TODO: handle output format for multiple nested levels of submodules
    output_filepath = MOCK_OUTPUT_DIR.joinpath(f"{repo_name}.p")
    with output_filepath.open('rb') as f:
        expected_output = pickle.load(f)

    # expected output reflects highest verbosity level so that we only
    # have to create one file per mock repo. If testing lower verbosity
    # level, prune data that wouldn't be there
    if verbose != 3:
        for field in ('files_staged', 'files_not_staged',
                      'files_untracked', 'submodules'):
            expected_output[field] = None
    elif not include_submodules:
        expected_output['submodules'] = None

    return test_output == expected_output


def run_command(cmd):
    """helper function that formats and tests command line input"""
    # split args
    cmd = shlex.split(cmd)
    # deal with POSIX/Windows path formatting
    cmd = [str(Path(arg)) if '/' in arg else arg for arg in cmd]
    result = run(cmd, stdout=PIPE, stderr=PIPE, encoding='UTF-8')
    return result.returncode, result.stdout, result.stderr


#########################################################################
#                Custom type converters for ConfigParser                #
#########################################################################
def _get_multiline_list(val):
    """
    splits a newline-separated list of values for a single option into a
    list
    """
    return val.strip().splitlines()


def _get_dict(val):
    """
    splits a newline separated list of values for a single option (where
    each option takes the format `sub-option = sub-value`) into a
    dictionary with the format `{sub-option: sub-value}`
    """
    keys_vals = map(lambda x: x.split('::'), val.strip().splitlines())
    return {k.strip(): v.strip() for k, v in keys_vals}


def _get_diff_list(val):
    """
    splits a newline-separated list of ::-separated values for a single
    option (where each value is 3-item, ::-separated list) into a list of
    namedtuple types. Patched `.diff` method returns a list of git.Diff
    objects, but we only need to access 3 of their properties, so mocking
    them with namedtuples is a lot easier than adding a whole class
    NOTE: the resulting field names of the namedtuple correspond to the
    comma-separated values IN ORDER
    """
    Diff = namedtuple('Diff', ('change_type', 'a_path', 'b_path'))
    lines = val.strip().splitlines()
    return [Diff(*map(lambda x: x.strip(), line.split('::'))) for line in lines]


CONVERTERS = {
    'difflist': _get_diff_list,
    'dict': _get_dict,
    'list': _get_multiline_list
}

