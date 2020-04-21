import pytest
from os.path import splitext
from shutil import copy2, rmtree
from .helpers.mock_repo import MockRepo
# have to import MockRepo from helpers subpackage, and some helper funcs
# use these paths, so paths must be defined in functions file to avoid
# circular import
from .helpers.functions import (
    MOCK_OUTPUT_DIR,
    MOCK_REPOS_DIR,
    REPO_CONFIGS_DIR
)


@pytest.fixture(autouse=True)
def patch_repo(monkeypatch):
    monkeypatch.setattr('gittracker.tracker.tracker.Repo', MockRepo)


@pytest.fixture(scope='session')
def mock_repo():
    # ==== SETUP ====
    assert REPO_CONFIGS_DIR.is_dir()
    MOCK_REPOS_DIR.mkdir()
    MOCK_OUTPUT_DIR.mkdir()
    # monkeypatch `git.Repo` object at session level
    # monkeypatch.setattr('gittracker.tracker.tracker.Repo', MockRepo)

    def _setup_repo(config_file):
        """dynamically creates mock repo directories as needed"""
        config_path = REPO_CONFIGS_DIR.joinpath(config_file)
        assert config_path.is_file()
        repo_path = MOCK_REPOS_DIR.joinpath(splitext(config_file)[0])
        # repo/data file may have already been created for previous test
        if not repo_path.is_dir():
            # create directory, add .git directory and config file
            repo_path.mkdir()
            repo_path.joinpath('.git').mkdir()
            copy2(config_path, repo_path)
        # return as one-item list for use in `get_status` function
        return [repo_path]

    # yield function to tests as fixture
    yield _setup_repo

    # ==== TEARDOWN ====
    rmtree(MOCK_REPOS_DIR)
    rmtree(MOCK_OUTPUT_DIR)


# with monkeypatch.context() as m:
#     m.setattr('gittracker.tracker.tracker.Repo', MockRepo)
