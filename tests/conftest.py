import pytest
from os.path import splitext
from shutil import copy2, rmtree
from .helpers.mock_repo import MockRepo
from .helpers.functions import create_expected_output
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
        return repo_path

    # ==== SETUP ====
    assert REPO_CONFIGS_DIR.is_dir()
    MOCK_REPOS_DIR.mkdir()
    MOCK_OUTPUT_DIR.mkdir()
    for config in REPO_CONFIGS_DIR.glob('*[!TEMPLATE].cfg'):
        create_expected_output(config)

    # yield function to tests as fixture
    yield _setup_repo

    # ==== TEARDOWN ====
    rmtree(MOCK_REPOS_DIR)
    rmtree(MOCK_OUTPUT_DIR)


def pytest_generate_tests(metafunc):
    # restrict parametrization to relevant test modules
    if metafunc.module in ('test_tracker', 'test_display'):
        # test all three verbosity levels separately
        if 'verbosity' in metafunc.fixturenames:
            metafunc.parametrize('verbosity', (1, 2, 3), scope='function')
        if 'submodules' in metafunc.fixturenames:
            metafunc.parametrize('submodules', (0, 1), scope='function')
