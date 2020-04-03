from .commandparser import CommandParser
from ..gittracker import track
from ..repofile.repofile import (
    auto_find_repos,
    manual_add,
    manual_init,
    manual_remove,
    show_tracked
)

status_parser = CommandParser(
    name='status',
    aliases='show',
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

find_parser = CommandParser(
    name='find',
    aliases='search',
    py_function=auto_find_repos,
    description='let GitTracker search (a section of) the filesystem for '
                'untracked repositories to start tracking. NOTE: the runtime '
                'of this command can scale quickly with the scope of the '
                "search. If you're searching a large direcotry structure, "
                'consider passing --ignore/--skip and --verbose.',
    short_description='search for untracked repositories to add to GitTracker',
    add_help=False
)
pos_group = find_parser.add_argument_group(
    title='positional optional arguments',
    description='(passed positionally but not required)'
)
pos_group.add_argument(
    'topdir',
    nargs='?',
    default='.',
    dest='toplevel_dir',
    help='the outermost directory to search under'
)
opt_group = find_parser.add_argument_group(
    title='optional arguments',
)
opt_group.add_argument(
    '--help',
    '-h',
    action='help',
    help='show this help message and exit'
)
opt_group.add_argument(
    '--ignore',
    '-i',
    nargs='*',
    dest='ignore_dirs',
    help='directories to exclude from the search (useful to avoid recursing '
         'into a large directory that contains no git repositories)'
)
opt_group.add_argument(
    '--search-hidden',
    '-h',
    action='store_true',
    help='pass to include hidden directories in the search'
)
opt_group.add_argument(
    '--verbose',
    '-v',
    action='store_true',
    help='pass to show live output of directories searched (can be useful for '
         'very large directory structures)'
)
opt_group.add_argument(
    'permission-err',
    '-p',
    choices=('ignore', 'show', 'raise'),
    help='how to handle read permission errors encountered while walking the '
         'filesystem. "ignore" [default] silently skips direectories with read '
         'restrictions. "show" will print a message to stdout and continue. '
         '"raise" will print a message to stderr, log it in the logfile, and quit.'
)

################################################################################

add_parser = CommandParser(
    name='add',
    aliases='track',
    py_function=manual_add,
    description='add new repositories to GitTracker'
)
add_parser.add_argument(
    'repo-path',
    nargs='+',
    help='path(s) to repositories to add'
)

################################################################################

init_parser = CommandParser(
    name='init',
    py_function=manual_init,
    description='initialize GitTracker for the first time. Using this is '
                'optional, as the `add` or `find/search` commands will achieve '
                'the same effect, but `init` will guide you through adding '
                'manually and/or automatically adding your local repositories '
                'to the tracker.',
    short_description='initialize GitTracker for the first time'
)

################################################################################

remove_parser = CommandParser(
    name='remove',
    aliases='rm',
    py_function=manual_remove,
    description='',
    short_description='stop tracking a repository with GitTracker'
)
remove_parser.add_argument(
    'repo-path',
    nargs='+',
    help='repository path(s) to stop tracking'
)
remove_parser.add_argument(
    '--yes',
    '-y',
    action='store_true',
    dest='confirm',
    help='auto-confirm removal of each repository'
)

################################################################################

list_parser = CommandParser(
    name='list',
    aliases='ls',
    py_function=show_tracked,
    description='list the currently tracked repositories'
)
list_parser.add_argument(
    '--quiet',
    '-q',
    action='store_true',
    help='show only the repository name rather than the full path'
)