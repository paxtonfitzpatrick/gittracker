# tests for command line interface
import subprocess
from gittracker.parsers.subcommands import SUBCOMMANDS


def run_command(cmd):
    # replacement for os.system that works with windows
    cmd = cmd.split()
    retcode = subprocess.run(cmd, shell=True).returncode
    return retcode


def test_entrypoint():
    # did the entrypoint get correctly installed?
    exit_status = run_command("gittracker --help")
    assert exit_status == 0


def test_module():
    # can the package still be run as a module?
    exit_status = run_command("python -m gittracker --help")
    assert exit_status == 0


def test_subcommands_available():
    # test availability of each subsubcommand
    for subcommand in SUBCOMMANDS:
        # test regular name and aliased names
        for name in subcommand.all_names:
            full_command = f"gittracker {name} --help"
            exit_status = run_command(full_command)
            assert exit_status == 0, f"{full_command} failed"
