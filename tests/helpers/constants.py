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
    def __init__(self, config_file, section, message):
        msg = f"in {config_file}, [{section}] section:\n\t{message}"
        super().__init__(msg)

