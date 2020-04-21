from gittracker.tracker.tracker import get_status
from ..helpers.functions import matches_expected_output


def test_even_clean(mock_repo):
    # most simple case: repo is even with remote with no local changes
    repo = mock_repo('even-clean.cfg')
    output = get_status([repo])
    assert matches_expected_output('even-clean', output[repo])
