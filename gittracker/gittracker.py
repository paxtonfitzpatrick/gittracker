#!/usr/bin/env python3

from .display.display import Displayer
from .repofile.repofile import load_tracked_repos, validate_tracked
from .tracker.tracker import get_status
from .utils.utils import log_error, validate_writable_path


@log_error
def track(verbose, submodules=0, outfile=None, plain=False):
    # first, tweak the verbose arg as a way of allowing a non-zero
    # default value with argparse's "count" action
    verbose = 1 if verbose is None else verbose
    # validate filepath before running
    outfile = validate_writable_path(outfile)
    # validate tracked repositories (if any)
    validate_tracked()
    # load in tracked repositories (has to be done separately from validation)
    tracked = load_tracked_repos()
    # get info for each repository
    # TODO: how many tracked repositories should be minimum for showing progress bar?
    status_info = get_status(tracked, verbose=verbose, follow_submodules=submodules)
    # create Displayer object
    displayer = Displayer(status_info, verbose=verbose, outfile=outfile, plain=plain)
    # format output for terminal window
    displayer.format_display()
    # display output
    displayer.display()
