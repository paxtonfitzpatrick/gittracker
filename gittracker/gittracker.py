#!/usr/bin/env python3

from .display.display import Displayer
from .repofile.repofile import load_tracked_repos, validate_tracked
from .tracker.tracker import get_status
from .util.util import log_error


@log_error
def gittracker(verbose=1, submodules=0):
    # validate tracked repositories (if any)
    validate_tracked()
    # load in tracked repositories (has to be done separately from validation)
    tracked = load_tracked_repos()
    # get info for each repository
    # TODO: how many tracked repositories should be minimum for showing progress bar?
    status_info = get_status(tracked, verbose=verbose, follow_submodules=submodules)
    # create Displayer object
    displayer = Displayer(status_info, verbose=verbose)
    # format output for terminal window
    displayer.format_display()
    # display output
    displayer.display()


if __name__ == "__main__":
    # argparse stuff...
    gittracker()
