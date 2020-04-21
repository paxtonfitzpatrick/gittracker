import pickle
import shlex
from collections import namedtuple
from configparser import ConfigParser
from pathlib import Path
from shutil import copy2
from subprocess import PIPE, run


# holds config files (name format: `<repo_name>.cfg`)
REPO_CONFIGS_DIR = Path(__file__).resolve().parents[1].joinpath('repo-configs')
# holds generated mock repositories
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


def add_submodule_config(filename, dest_dir):
    src = REPO_CONFIGS_DIR.joinpath('submodule-configs', filename)
    assert src.is_file()
    assert dest_dir.is_dir()
    if not dest_dir.joinpath(filename).is_file():
        copy2(src, dest_dir)


def matches_expected_output(repo_name, test_output, verbose=2, include_submodules=False):
    # TODO: handling output format for multiple nested levels of submodules
    output_filepath = MOCK_OUTPUT_DIR.joinpath(f"{repo_name}.p")
    if output_filepath.is_file():
        with output_filepath.open('rb') as f:
            expected_output = pickle.load(f)
    else:
        expected_output = _create_expected_output(repo_name)

    # expected output reflects highest verbosity level so that we only
    # have to create one file per mock repository. If testing lower
    # verbosity level, prune data that wouldn't be there
    if verbose != 3:
        expected_output['submodules'] = None
        for field in (
                'files_staged',
                'files_not_staged',
                'files_untracked',
                'submodules'
        ):
            expected_output[field] = None
    elif not include_submodules:
        expected_output['submodules'] = None

    return test_output == expected_output


def _create_expected_output(repo_name, submodule=False):
    # submodule arg used for recursive calls to set proper config
    # directory and avoid output to file
    if submodule:
        config_dir = REPO_CONFIGS_DIR.joinpath('submodule-configs')
    else:
        config_dir = REPO_CONFIGS_DIR

    config_filepath = config_dir.joinpath(f"{repo_name}.cfg")
    output_filepath = MOCK_OUTPUT_DIR.joinpath(f"{repo_name}.p")
    config = ConfigParser(converters=CONVERTERS)
    with open(config_filepath, 'r') as f:
        config.read_file(f)

    # some upfront checks for conditions that will return a string
    # rather than a dict
    if config.getboolean('head', '_is_empty'):
        if submodule:
            expected = "not initialized"
        else:
            expected = "This should raise a ValueError"
    elif config.getboolean('head', 'is_detached'):
        hexsha = config.get('head', 'hexsha')
        expected = f"HEAD detached at {hexsha[:7]}"
    else:
        expected = dict()
        expected['local_branch'] = config.get('active_branch', 'name')
        expected['remote_branch'] = config.get('active_branch', 'remote_branch')
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
        expected['files_unstaged'] = [(f.change_type, f.a_path, f.b_path)
                                    for f in files_unstaged]
        expected['n_unstaged'] = len(files_unstaged)

        submodules = config.getdict('submodules', 'paths_configs')
        if not any(submodules):
            expected['submodules'] = None
        else:
            expected['submodules'] = {}

        for path, config_file in submodules.items():
            expected['submodules'][path] = _create_expected_output(config_file,
                                                                   submodule=True)

    if not submodule:
        with open(output_filepath, 'rb') as f:
            pickle.dump(expected, f)

    return expected


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
    splits a newline separated list of values for a single option (where
    each option takes the format `sub-option = sub-value`) into a
    dictionary with the format `{sub-option: sub-value}`
    NOTE: first item should be on a different line from the option key
    """
    keys_vals = map(lambda x: x.split('::'), val.splitlines()[1:])
    return {k.strip(): v.strip() for k, v in keys_vals}


def _get_diff_list(val):
    """
    splits a newline-separated list of ::-separated values for a single
    option (where each value is 3-item, ::-separated list) into a list of
    namedtuple types. Patched `.diff` method returns a list of git.Diff
    objects, but we only need to access 3 of their properties, so mocking
    them with namedtuples is a lot easier than adding a whole class
    NOTE: the resultant field names of the namedtuple correspond to the
    comma-separated values IN ORDER
    """
    Diff = namedtuple('Diff', ('change_type', 'a_path', 'b_path'))
    lines = val.splitlines()[1:]
    return [Diff(*map(lambda x: x.strip(), line.split('::'))) for line in lines]


CONVERTERS = {
    'difflist': _get_diff_list,
    'dict': _get_dict,
    'list': _get_multiline_list
}

