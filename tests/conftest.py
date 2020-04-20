import pytest
from pathlib import Path
from shutil import copy2, rmtree

REPO_CONFIGS_DIR = Path(__file__).resolve().parent.joinpath('repo-configs')
MOCK_REPOS_DIR = REPO_CONFIGS_DIR.parent.joinpath('mock-repos')


@pytest.fixture(scope='session')
def setup_repository():
    # ==== SETUP ====
    assert REPO_CONFIGS_DIR.is_dir()
    MOCK_REPOS_DIR.mkdir()

    def _generate_from_config(config_file):
        """dynamically creates mock repo directories as needed"""
        config_path = REPO_CONFIGS_DIR.joinpath(config_file)
        assert config_path.is_file()
        # repo dirname is config file's basename with "repo-" removed
        repo_path = MOCK_REPOS_DIR.joinpath(config_file.stem[5:])
        # repo structure have already been created for previous test
        if not repo_path.is_dir():
            # create directory, add .git directory and config file
            repo_path.mkdir()
            repo_path.joinpath('.git').mkdir()
            copy2(config_path, repo_path)

        return repo_path

    # yield function to tests as fixture
    yield _generate_from_config

    # ==== TEARDOWN ====
    rmtree(MOCK_REPOS_DIR)
