from datetime import datetime as dt
from os import listdir
from os.path import isdir, join as opj
from pathlib import Path
from traceback import print_exception
from .exceptions import RepoNotFoundError, NoGitdirError

LOGFILE_PATH = opj(Path(__file__).parents[2], 'log', 'logfile')


def log_error(exception, show=False):
    # record current time
    curr_time = dt.now().ctime()
    with open(LOGFILE_PATH, 'a') as logfile:
        # formatting for readability
        logfile.write(f"{curr_time}\n\n")
        print_exception(type(exception), exception, tb=None, file=logfile)
        logfile.write(f"\n\n{'='*60}\n\n")
    if show:
        # print traceback to screen
        print_exception(type(exception), exception, tb=None, file=None)


def prompt_input(prompt, default=None):
    """
    prompts user for command line input
    returns True for 'yes'/'y' and False for 'no'/'n' responses
    :param prompt: str
            The prompt presented on-screen to the user
    :param default: str or None
            Controls behavior if user presses return without
            entering a response. Default is reflected in casing
            of options (e.g., "[Y/n]" for default "yes"). If a
            string, must be "yes", "no". If None, user is
            re-prompted to enter a response if one is not given.
    :return: bool
            True for affirmative response, False for negative
    """
    assert default in ('yes', 'no', None), \
        "Default response must be either 'yes', 'no', or None"

    valid_responses = {
        'yes': True,
        'y': True,
        'no': False,
        'n': False
    }

    if default is None:
        opts = "[y/n]"
    elif default == 'yes':
        opts = "[Y/n]"
    else:
        opts = "[y/N]"

    while True:
        print(f"{prompt}\n{opts}")
        response = input().lower()
        # if user hits return without typing, return default response
        if (default is not None) and (not response):
            return valid_responses[default]
        elif response in valid_responses:
            return valid_responses[response]
        else:
            print("Please respond with either 'yes' (or 'y') or 'no' (or 'n')\n")


def validate_repo(repo_path):
    # check directory exists
    if not isdir(repo_path):
        raise RepoNotFoundError(repo_path)
    # check that directory is a git repository
    if '.git' not in listdir(repo_path):
        raise NoGitdirError(repo_path)
    return


