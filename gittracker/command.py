# handles command, sub-command, and argument parsing
import sys
from argparse import RawDescriptionHelpFormatter
from gittracker import __version__
from gittracker.parsers.commandparser import CommandParser
from gittracker.parsers.subcommands import SUBCOMMANDS
from gittracker.utils.utils import LOG_DIR

DEFAULT_COMMAND = 'status'
VERSION_FMT = f"GitTracker version: {__version__}"


def base_pyfunc(**kwargs):
    # basic function that returns correct output
    # based on options passed to main executable
    if kwargs.get('log_dir'):
        print(f"GitTracker logfile directory:\n\t{LOG_DIR}")


def main():
    git_tracker = CommandParser(
        prog='gittracker',
        usage='%(prog)s [--help | --version | --log-dir | command]',
        description='GitTracker: keep track of all your git repositories with '
                    'a single command',
        epilog="commands are run with `gittracker [cmd] [args]`.\nFor more "
               "information on a given 'cmd', enter `gittracker [cmd] --help`"
               "\nNOTE: simply running `gittracker [args]` will run "
               f"`gittracker {DEFAULT_COMMAND} [args]`\nunless 'args' contains "
               "any of the above base options",
        formatter_class=RawDescriptionHelpFormatter,
        py_function=base_pyfunc,
        subcommands=SUBCOMMANDS,
        add_help=False
    )
    base_commands = git_tracker.add_mutually_exclusive_group(required=False)
    base_commands.add_argument(
        '-h',
        '--help',
        action='help',
        help='show this help message and exit'
    )
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
