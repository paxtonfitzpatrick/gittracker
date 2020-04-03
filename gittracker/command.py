# handles command, sub-command, and argument parsing
import sys
from gittracker import __version__
from gittracker.parsers.commandparser import CommandParser
from gittracker.parsers.subcommands import SUBCOMMANDS
from gittracker.util.util import LOG_DIR

DEFAULT_COMMAND = 'status'
VERSION_FMT = f"GitTracker version: {__version__}"


def base_pyfunc(kwarg_dict):
    # basic function that returns correct output
    # based on options passed to main executable
    if kwarg_dict['log_dir']:
        return LOG_DIR


def main():
    git_tracker = CommandParser(
        description='GitTracker: keep track of all your git repositories with '
                    'a single command',
        epilog="commands are run with `gittracker [cmd] [args].\nFor more "
               "information on a given 'cmd', enter `gittracker [cmd] --help`"
               "\nNOTE: simply running `gittracker [args]` will run "
               f"`gittracker {DEFAULT_COMMAND} [args]` unless 'args' contains "
               "any of the above base options",
        py_function=base_pyfunc,
        subcommands=SUBCOMMANDS
    )
    base_commands = git_tracker.add_mutually_exclusive_group(required=False)
    base_commands.add_argument(
        '--version',
        '-V',
        action='version',
        version=VERSION_FMT,
        help='show the installed GitTracker version'
    )
    base_commands.add_argument(
        '--log-dir',
        action='store_true',
        help='show path to directory with tracked repo and error logs'
    )

    git_tracker.default_subcommand = DEFAULT_COMMAND
    git_tracker.run(sys.argv[1:])
