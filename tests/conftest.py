import pytest
from os.path import splitext
from shutil import copy2, rmtree
from .helpers.mock_repo import MockRepo
from .helpers.tracker_helpers import create_tracker_output
from .helpers.constants import (MOCK_OUTPUT_DIR,
                                MOCK_REPOS_DIR,
                                REPO_CONFIGS_DIR,
                                MockConfigNotFound)


@pytest.fixture(autouse=True)
def patch_repo(monkeypatch):
    # monkeypatch `git.Repo` object at session level
    monkeypatch.setattr('gittracker.tracker.tracker.Repo', MockRepo)


@pytest.fixture(scope='session')
def mock_repo():
    def _setup_repo(config_file):
        """dynamically creates mock repo directories as needed"""
        config_path = REPO_CONFIGS_DIR.joinpath(config_file)
        if not config_path.is_file():
            raise MockConfigNotFound("test", config_path)
        repo_path = MOCK_REPOS_DIR.joinpath(splitext(config_file)[0])
        # repo/data file may have already been created for previous test
        if not repo_path.is_dir():
            # create directory, add .git directory and config file
            repo_path.mkdir()
            repo_path.joinpath('.git').mkdir()
            copy2(config_path, repo_path)
        return str(repo_path)

    # ==== SETUP ====
    assert REPO_CONFIGS_DIR.is_dir()
    MOCK_REPOS_DIR.mkdir()
    MOCK_OUTPUT_DIR.mkdir()
    # have to filter globbed output in a roundabout way due to
    # Python 3.6/Windows bug: https://bugs.python.org/issue31202
    configs = [f for f in REPO_CONFIGS_DIR.glob('*.cfg') if f.stem != 'TEMPLATE']
    for config in configs:
        create_tracker_output(config)
        # create_display_output(config)

    # yield function to tests as fixture
    yield _setup_repo

    # ==== TEARDOWN ====
    rmtree(MOCK_REPOS_DIR)
    rmtree(MOCK_OUTPUT_DIR)


def pytest_generate_tests(metafunc):
    # test all three verbosity levels separately
    if 'verbosity' in metafunc.fixturenames:
        if 'submodules' in metafunc.fixturenames:
            metafunc.parametrize('verbosity,submodules',
                                 [(1, 0), (2, 0), (3, 0), (3, 1)])
        else:
            metafunc.parametrize('verbosity', (1, 2, 3))
