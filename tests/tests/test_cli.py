# tests for command line interface
from gittracker.parsers.subcommands import SUBCOMMANDS
from .helpers import test_input


def test_entrypoint():
    # is the app accessible via its entrypoi?
    retcode, stderr = test_input("gittracker --help")
    assert retcode == 0, stderr


def test_module():
    # can the package still be run as a module?
    retcode, stderr = test_input("python -m gittracker --help")
    assert retcode == 0, stderr


def test_subcommands_available():
    # test availability of each subsubcommand
    for subcommand in SUBCOMMANDS:
        # test regular name and aliased names
        for name in subcommand.all_names:
            full_command = f"gittracker {name} --help"
            retcode, stderr = test_input(full_command)
            assert retcode == 0, stderr


def test_bad_arg():
    # test failure on unsupported argument passed
    for subcommand in [''] + SUBCOMMANDS:
        full_command = f"gittracker {subcommand} foo"
        retcode, stderr = test_input(full_command)
        assert retcode != 0
