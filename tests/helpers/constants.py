from pathlib import Path


# holds config files (name format: `<repo_name>.cfg`)
REPO_CONFIGS_DIR = Path(__file__).resolve().parents[1].joinpath('repo-configs')
# holds generated mock repositories
MOCK_REPOS_DIR = REPO_CONFIGS_DIR.parent.joinpath('mock-repos')
# holds data files of expected test output (name format `<repo_name>.p`)
MOCK_OUTPUT_DIR = REPO_CONFIGS_DIR.parent.joinpath('expected-output')


class TestSetupError(Exception):
    pass


class InvalidConfigValue(TestSetupError):
    def __init__(self, config_file, section=None, message=None):
        msg = f"in {config_file}"
        if section is not None:
            msg += f", [{section}] section"
        if message is not None:
            msg += f":\n{message}"
        super().__init__(msg)


class MockConfigNotFound(TestSetupError):
    def __init__(self, source, missing_config):
        msg = f"{source} points to a config that doesn't exist: " \
              f"{missing_config}"
        super().__init__(msg)


# each of the fields returned by
# gittracker.tracker.tracker._single_repo_status - used for constructing
# expected test output
TRACKER_OUTPUT = {
    # local branch compared to remote tracking branch
    'local_branch': None,
    'remote_branch': None,
    'n_commits_ahead': None,
    'n_commits_behind': None,
    # uncommitted local changes
    'n_staged': None,
    'files_staged': None,
    'n_not_staged': None,
    'files_not_staged': None,
    'n_untracked': None,
    'files_untracked': None,
    # alternate info for repos in a detached HEAD state
    'is_detached': False,
    'hexsha': None,
    'from_branch': None,
    'ref_sha': None,
    'detached_commits': None,
    # info for submodules (if any)
    'submodules': None
}
