# tests for command line interface
from os import listdir
from os.path import isdir
from gittracker import __version__ as init_version
from gittracker.parsers.subcommands import SUBCOMMANDS
from ..helpers.functions import run_command


def test_entrypoint():
    # is the app accessible via its entrypoint?
    retcode, _, stderr = run_command("gittracker --help")
    assert retcode == 0, stderr


def test_module():
    # can the package still be run as a module?
    retcode, _, stderr = run_command("python -m gittracker --help")
    assert retcode == 0, stderr


def test_subcommands_available():
    # test availability of each subsubcommand
    for subcommand in SUBCOMMANDS:
        # test regular name and aliased names
        for name in subcommand.all_names:
            full_command = f"gittracker {name} --help"
            retcode, _, stderr = run_command(full_command)
            assert retcode == 0, stderr


def test_all_args_in_help():
    # test whether each argument is shown in help output for given command
    for subcommand in SUBCOMMANDS:
        cmd = subcommand.name
        full_command = f"gittracker {cmd} --help"
        _, help_msg, _ = run_command(full_command)
        for action in subcommand._actions:
            if not any(action.option_strings):
                arg = action.metavar
            else:
                # longest option string is full arg name
                arg = max(action.option_strings, key=len)
            assert arg in help_msg, f"`{arg}` arg for `{cmd}` command not " \
                                    "listed in `--help` output"


def test_bad_arg():
    # test failure on unsupported argument passed
    for subcommand in [''] + SUBCOMMANDS:
        full_command = f"gittracker {subcommand} foo"
        retcode, _, stderr = run_command(full_command)
        assert retcode != 0


def test_version():
    # test whether version info was set/updated correctly
    retcode, stdout, stderr = run_command("gittracker --version")
    assert retcode == 0, stderr
    cli_version = stdout.split(': ')[1].strip()
    assert cli_version == init_version, "versions from CLI command and " \
                                        "__init__.py not equal"
    assert cli_version.count('.') == init_version.count('.') == 2, "version string malformed"


def test_log_dir():
    retcode, stdout, stderr = run_command("gittracker --log-dir")
    assert retcode == 0, stderr
    log_dir = stdout.splitlines()[-1].strip()
    assert isdir(log_dir), f"logfile directory doesn't exist, expected at: {log_dir}"
    assert 'logfile' in listdir(log_dir), "missing logfile"
    assert 'tracked-repos' in listdir(log_dir), "missing tracked repositories file"
