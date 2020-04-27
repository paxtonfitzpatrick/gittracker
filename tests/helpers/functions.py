import pickle
import shlex
from collections import namedtuple
from configparser import ConfigParser, NoOptionError, NoSectionError
from pathlib import Path
from shutil import copy2
from subprocess import PIPE, run
from .constants import (MOCK_OUTPUT_DIR,
                        REPO_CONFIGS_DIR,
                        TRACKER_OUTPUT,
                        InvalidConfigValue)


def add_submodule_config(dest_dir):
    filename = f"{dest_dir.name}.cfg"
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
    if config.getboolean('head', 'is_empty'):
        if submodule:
            return "not initialized"
        else:
            # shouldn't be using `matches_expected_output` in this case -
            # empty repositories intentionally raise ValueError
            return None

    files_staged = config.getdifflist('repo', 'staged_changes')
    files_unstaged = config.getdifflist('repo', 'unstaged_changes')
    expected['files_staged'] = [(f.change_type, f.a_path, f.b_path)
                                for f in files_staged]
    expected['files_not_staged'] = [(f.change_type, f.a_path, f.b_path)
                                    for f in files_unstaged]
    expected['files_untracked'] = config.getpathlist('repo', 'untracked_files')
    expected['n_staged'] = len(files_staged)
    expected['n_not_staged'] = len(files_unstaged)
    expected['n_untracked'] = len(expected['files_untracked'])
    expected['is_detached'] = config.getboolean('head', 'is_detached')

    if expected['is_detached']:
        sha_shortened = config.get('head', 'hexsha')[:7]
        if submodule:
            return f"HEAD detached at {sha_shortened}"
        else:
            expected['hexsha'] = sha_shortened
            expected['from_branch'] = config.get('head', 'from_branch')
            ref_sha = config.get('head', 'ref_sha')[:7]
            if ref_sha != sha_shortened:
                expected['ref_sha'] = ref_sha
                expected['detached_commits'] = config.getint('head',
                                                             'detached_commits')
    else:
        expected['local_branch'] = config.get('active_branch', 'name')
        expected['remote_branch'] = config.get('active_branch', 'remote_branch')
        if expected['remote_branch'] == '':
            # local branch isn't tracking a remote branch
            expected['n_commits_ahead'] = None
            expected['n_commits_behind'] = None
        else:
            expected['n_commits_ahead'] = config.getint('active_branch',
                                                        'n_commits_ahead')
            expected['n_commits_behind'] = config.getint('active_branch',
                                                         'n_commits_behind')

    submodule_paths = config.getpathlist('submodules', 'paths')
    if not any(submodule_paths):
        submodules = None
    else:
        submodules = {}
        for sm_path in submodule_paths:
            sm_config_path = REPO_CONFIGS_DIR.joinpath('submodule_configs',
                                                       f"{sm_path.name}.cfg")
            submodules[sm_path] = create_expected_output(sm_config_path,
                                                         submodule=True)
    expected['submodules'] = submodules

    if not submodule:
        with open(output_filepath, 'wb') as f:
            pickle.dump(expected, f)

    return expected


def load_validate_config(config_path):
    """
    run some checks for proper config formatting upfront. This helps
    prevent errors due to config formatting from cropping up during
    actual tests, where they can be hard to differentiate from actual
    test failures
    """
    config_file = config_path.name
    config = ConfigParser(converters=CONVERTERS)
    with open(config_path, 'r') as f:
        config.read_file(f)

    # validate section and option presence and names
    # ===================================================================
    sections_options = {
        'repo': ('untracked_files', 'staged_changes', 'unstaged_changes'),
        'active_branch': ('name', 'remote_branch', 'n_commits_ahead',
                          'n_commits_behind'),
        'head': ('is_empty', 'is_detached', 'hexsha', 'from_branch', 'ref_sha',
                 'detached_commits'),
        'submodules': ('paths',)
    }
    required_sections = sections_options.keys()
    present_sections = config.sections()
    bad_sections = [s for s in present_sections if s not in required_sections]
    if any(bad_sections):
        message = "config must contain only the following sections: " \
                  f"{', '.join(required_sections)}\n(contains: " \
                  f"{', '.join(bad_sections)}) "
        raise InvalidConfigValue(config_file, message=message)

    for section, options in sections_options.items():
        try:
            for option in options:
                config.get(section, option)

            bad_options = [opt for opt in config[section] if opt not in options]
            assert len(bad_options) == 0

        except Exception as e:
            if isinstance(e, NoSectionError):
                message = f"missing required section: {section}"
                s = None
            elif isinstance(e, NoOptionError):
                message = f"missing required option: {option}"
                s = section
            elif isinstance(e, AssertionError):
                message = f"contains unrecognized option: {option}"
                s = section
            else:
                message = "unexpected exception in parsing options/values"
                s = None
            raise InvalidConfigValue(config_file, s, message)

    # validate staged_changes and unstaged_changes value formatting
    # ===================================================================
    for option in ('staged_changes', 'unstaged_changes'):
        valid_change_types = ('R', 'M', 'A', 'D')
        if option == 'unstaged_changes':
            valid_change_types = valid_change_types[1:]
        lines = config.get('repo', option).strip().splitlines()
        for val in lines:
            if val.count(':') != 2:
                message = f"{option} value should be a newline-separated " \
                          "list, where each line contains three double colon " \
                          "(::)-separated values: the change type, a_path, " \
                          "and b_path"
                raise InvalidConfigValue(config_file, 'repo', message)

            change_type = val.split('::')[0].strip()
            if change_type not in valid_change_types:
                message = f"invalid change type in {option} value " \
                          f"({change_type}). Valid change types are: " \
                          f"{', '.join(valid_change_types)}"
                raise InvalidConfigValue(config_file, 'repo', message)

    # validate mutual exclusivity of is_empty and is_detached
    # ===================================================================
    try:
        is_empty = config.getboolean('head', 'is_empty')
        is_detached = config.getboolean('head', 'is_detached')
        assert not (is_empty and is_detached)
    except Exception as e:
        if isinstance(e, ValueError):
            message = "both is_empty and is_detached fields must be booleans"
        elif isinstance(e, AssertionError):
            message = "is_empty and is_detached may not both be true"
        else:
            message = "unexpected exception in is_empty/is_detached values"
        raise InvalidConfigValue(config_file, 'head', message) from e

    # validate options required when is_empty is/isn't set to true
    # ===================================================================
    if is_detached:
        for val in ('hexsha', 'from_branch', 'ref_sha', 'detached_commits'):
            if config.get('head', val) == '':
                message = f"{val} is required if is_detached is set to true"
                raise InvalidConfigValue(config_file, 'head', message)

        for val in ('hexsha', 'ref_sha'):
            if len(config.get('head', val)) < 7:
                message = f"{val} must be 7 characters (code expects 40 characters)"
                raise InvalidConfigValue(config_file, 'head', message)

        try:
            detached_commits = config.getint('head', 'detached_commits')
        except ValueError as e:
            message = "detached_commits must be an integer"
            raise InvalidConfigValue(config_file, 'head', message) from e

        hexsha_short = config.get('head', 'hexsha')[:7]
        ref_sha_short = config.get('head', 'ref_sha')[:7]

        if (detached_commits == 0) is not (hexsha_short == ref_sha_short):
            message = "if detached_commits is set to 0, hexsha and ref_sha " \
                      "must match. Otherwise, they must be different"
            raise InvalidConfigValue(config_file, 'head', message)

    elif not is_empty and config.get('active_branch', 'remote_branch') != '':
        # active branch values matter only if is_empty and is_detached are false
        if '/' not in config.get('active_branch', 'remote_branch'):
            message = "remote_branch format should be: <remote_name>/<branch_name>"
            raise InvalidConfigValue(config_file, 'active_branch', message)

        for option in ('n_commits_ahead', 'n_commits_behind'):
            try:
                config.getint('active_branch', option)
            except ValueError as e:
                message = f"{option} must be an integer if remote_branch is set"
                raise InvalidConfigValue(config_file,
                                         'active_branch',
                                         message) from e

    # validate submodule path formatting and existence of config files
    # ===================================================================
    sm_paths = config.get('submodules', 'paths').strip().splitlines()
    # will be skipped if no submodules are set
    for sm_path in sm_paths:
        if sm_path.startswith('/'):
            message = "submodule paths should be relative (from the parent " \
                      "repository's root directory), not absolute"
            raise InvalidConfigValue(config_file, 'submodules', message)
        elif '..' in sm_path:
            message = "submodule paths cannot be outside the parent " \
                      "repository (cannot include '..')"
            raise InvalidConfigValue(config_file, 'submodules', message)

        sm_config_name = f'{sm_path.name}.cfg'
        sm_config_path = REPO_CONFIGS_DIR.joinpath('submodule-configs',
                                                   sm_config_name)
        if not sm_config_path.is_file():
            message = f"missing config file for submodule: {sm_path}.\n" \
                      f"Expected file at {sm_config_path}"
            raise InvalidConfigValue(config_file, 'submodules', message)

    return config


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
def _get_path_list(val):
    """
    splits a newline-separated list of values for a single option into a
    list
    """
    return val.strip().splitlines()


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
    'pathlist': _get_path_list
}

