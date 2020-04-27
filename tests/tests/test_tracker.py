import pytest
from git import InvalidGitRepositoryError
from gittracker.tracker.tracker import get_status
from ..helpers.functions import matches_expected_output


# NOTE: "verbosity" and "submodules" parameters are verbosity levels and
# presence/absence of submodule info, and are dynamically parametrized by
# the `pytest_generate_tests` collection hook in conftest.py
def test_even_clean(mock_repo, verbosity):
    # repo is even with remote and working tree is clean
    repo = mock_repo('even-clean.cfg')
    output = get_status([repo], verbosity)
    assert matches_expected_output('even-clean', output[repo], verbosity)


def test_even_dirty(mock_repo, verbosity):
    # repo is even with remote and working tree is dirty
    repo = mock_repo('even-dirty.cfg')
    output = get_status([repo], verbosity)
    assert matches_expected_output('even-dirty', output[repo], verbosity)


def test_commits_ahead(mock_repo, verbosity):
    # repo is some number of commits ahead of remote
    repo = mock_repo('commits-ahead.cfg')
    output = get_status([repo], verbosity)
    assert matches_expected_output('commits-ahead', output[repo], verbosity)


def test_commits_behind(mock_repo, verbosity):
    # repo is some number of commits behind remote
    repo = mock_repo('commits-behind.cfg')
    output = get_status([repo], verbosity)
    assert matches_expected_output('commits-behind', output[repo], verbosity)


def test_commits_ahead_behind(mock_repo, verbosity):
    # repo is both ahead of and behind remote by some number of commits
    repo = mock_repo('commits-ahead-behind.cfg')
    output = get_status([repo], verbosity)
    assert matches_expected_output('commits-ahead-behind', output[repo], verbosity)


def test_no_remote_clean(mock_repo, verbosity):
    # repo has no remote and working tree is clean
    repo = mock_repo('no-remote-clean.cfg')
    output = get_status([repo], verbosity)
    assert matches_expected_output('no-remote-clean', output[repo], verbosity)


def test_no_remote_dirty(mock_repo, verbosity):
    # repo has no remote and working tree is dirty
    repo = mock_repo('no-remote-dirty.cfg')
    output = get_status([repo], verbosity)
    assert matches_expected_output('no-remote-dirty', output[repo], verbosity)


def test_head_detached_even_clean(mock_repo, verbosity):
    # repo's HEAD is detached with no new commits or uncommitted changes
    # made on detached HEAD
    repo = mock_repo('head-detached-even-clean.cfg')
    output = get_status([repo], verbosity)
    assert matches_expected_output('head-detached-even-clean',
                                   output[repo],
                                   verbosity)


def test_head_detached_even_dirty(mock_repo, verbosity):
    # repo's HEAD is detached with no new commits made on detached HEAD,
    # but with uncommitted changes
    repo = mock_repo('head-detached-even-dirty.cfg')
    output = get_status([repo], verbosity)
    assert matches_expected_output('head-detached-even-dirty',
                                   output[repo],
                                   verbosity)


def test_head_detached_ahead_clean(mock_repo, verbosity):
    # repo's HEAD is detached with new commits made on detached HEAD, but
    # no uncommitted changes
    repo = mock_repo('head-detached-ahead-clean.cfg')
    output = get_status([repo], verbosity)
    assert matches_expected_output('head-detached-ahead-clean',
                                   output[repo],
                                   verbosity)


def test_head_detached_ahead_dirty(mock_repo, verbosity):
    # repo's HEAD is detached with new commits and uncommitted changes
    # made on detached HEAD
    repo = mock_repo('head-detached-ahead-dirty.cfg')
    output = get_status([repo], verbosity)
    assert matches_expected_output('head-detached-ahead-dirty',
                                   output[repo],
                                   verbosity)


def test_empty(mock_repo, verbosity):
    # EXPECTED FAILURE: repo is newly initialized and has no commit history
    repo = mock_repo('empty.cfg')
    message = "GitTracker currently doesn't support tracking newly " \
              "initialized repositories"
    with pytest.raises(InvalidGitRepositoryError, match=message):
        output = get_status([repo], verbosity)


# =========================== SUBMODULE TESTS ===========================
def test_submodule_even_clean(mock_repo, verbosity, submodules):
    # submodule is even with its remote and working tree is clean
    repo = mock_repo('submodule-even-clean.cfg')
    output = get_status([repo], verbosity, submodules)
    assert matches_expected_output('head-detached-ahead-dirty',
                                   output[repo],
                                   verbosity,
                                   submodules)
