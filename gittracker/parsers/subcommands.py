from .commandparser import CommandParser
from ..gittracker import track
from ..repofile.repofile import auto_find_repos, manual_init, manual_add, manual_remove, show_tracked


def _track_wrapper(verbose, submodules):
    # wrapper around track function to allow a non-zero
    # default verbosity with argparse's "count" action
    _verbose = 1 if verbose is None else verbose
    track(verbose=_verbose, submodules=submodules)

status_parser = CommandParser(
    name='status',
    aliases=['track', 'show'],
    py_function=_track_wrapper,
    description='show "git-status"-like output for each tracked repository',
    short_description='show the states of tracked repositories [default command]'
)
status_parser.add_argument(
    '--verbose',
    '-v',
    action='count',
    help='the verbosity level for the output. Level 1 shows minimal condensed '
         'info, level 2 [default] shows some more info, level 3 shows full '
         '"git-status" output'
)
status_parser.add_argument(
    '--submodules',
    default=0,
    type=int,
    help='maximum recursion depth for analyzing nested submodules. 0 ignores all submodules, 1 includes only the '
)