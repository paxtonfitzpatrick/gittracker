from .commandparser import CommandParser
from ..gittracker import track
from ..repofile.repofile import auto_find_repos, manual_init, manual_add, manual_remove, show_tracked

status_parser = CommandParser(
    name='status',
    aliases=['track', 'show'],
    py_function=track,
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
    help="maximum recursion depth for analyzing nested submodules. 0 [default] "
         "ignores all submodules, 1 includes only the outer repository's "
         "submodules, etc. NOTE: this option only applies to verbosity level 3."
)
status_parser.add_argument(
    '--file',
    '-f',
    type=str,
    dest='outfile',
    help='optional filepath to which the output will be written, rather than stdout'
)
status_parser.add_argument(
    '--plain',
    action='store_true',
    help='pass to disable output stylization'
)

################################################################################

