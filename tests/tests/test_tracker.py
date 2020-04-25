from gittracker.tracker.tracker import get_status
from ..helpers.functions import matches_expected_output


def test_even_clean(mock_repo):
    # most simple case: repo is even with remote with no local changes
    repo = mock_repo('even-clean.cfg')
    output = get_status([repo])
    assert matches_expected_output('even-clean', output[repo])


def test_commits_ahead(mock_repo):
    # repo is some number of commits ahead of remote
    repo = mock_repo('commits-ahead.cfg')
    output = get_status([repo])
    assert matches_expected_output('commits-ahead', output[repo])


def test_commits_behind(mock_repo):
    # repo is some number of commits behind remote
    repo = mock_repo('commits-behind.cfg')
    output = get_status([repo])
    assert matches_expected_output('commits-behind', output[repo])


def test_commits_ahead_behind(mock_repo):
    # repo is both ahead of and behind remote by some number of commits
    repo = mock_repo('commits-ahead-behind.cfg')
    output = get_status([repo])
    assert matches_expected_output('commits-ahead-behind', output[repo])


def test_no_remote_clean(mock_repo):
    # repo has no remote & working tree is clean
    repo = mock_repo('no-remote-clean.cfg')
    output = get_status([repo])
    assert matches_expected_output('no-remote-clean', output[repo])


def test_head_detached_even_clean(mock_repo):
    # repo is in a detached HEAD state with no commits or local changes
    # on detached HEAD
    repo = mock_repo('head-detached-even-clean.cfg')
    output = get_status([repo])
    assert matches_expected_output('head-detached-even-clean', output[repo])

