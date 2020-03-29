from datetime import datetime as dt
from functools import wraps
from os import listdir
from os.path import isdir, realpath, join as opj
from pathlib import Path
from sys import exit
from traceback import print_exception
from .exceptions import BugIdentified, RepoNotFoundError, NoGitdirError

LOGFILE_PATH = opj(Path(__file__).parents[1], 'log', 'logfile')
GITHUB_URL = "https://github.com/paxtonfitzpatrick/gittracker/issues/new"
BUG_MSG = "\n\nUh oh! Looks like you might have encountered a bug, please " \
          f"consider posting an issue at:\n\t{GITHUB_URL}\nincluding the " \
          f"contents of the logfile, found at:\n\t{LOGFILE_PATH}"


def log_error(func=None, show=False):
    """
    decorator function that logs any exceptions at
    `gittracker/log/logfile`.
    :param func: callable (never passed)
            the decorated function
    :param show: bool (optional)
            whether or not to print the stack trace to the
            screen, in addition to logging it in the logfile
    :return:
    """
    def decorated_func(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                curr_time = dt.now().ctime()
                with open(LOGFILE_PATH, 'a') as logfile:
                    # logfile formatting for readability
                    logfile.write(f"{curr_time}\n\n")
                    print_exception(type(e), e, tb=None, file=logfile)
                    logfile.write(f"\n\n{'='*60}\n\n")
                    if show:
                        print_exception(type(e), e, tb=None, file=None)
                    exit(BUG_MSG)
        return wrapper
    # some magic to allow decorator to be used with or without kwargs
    if func is not None:
        # if decorator was used alone
        return decorated_func(func)
    # if decorator was called with kwargs
    return decorated_func


def prompt_input(prompt, default=None, possible_bug=False):
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
        opts = "y/n"
    elif default == 'yes':
        opts = "Y/n"
    else:
        opts = "y/N"

    if possible_bug:
        prompt += "\n(if you think you've encountered a bug, please enter 'b')"
        opts += '/b'
        bad_input_msg = "Please respond with either 'yes' (or 'y'), 'no' (or " \
                        "'n'), or 'b' if you think this is a bug\n"
    else:
        bad_input_msg = "Please respond with either 'yes' (or 'y') or 'no' " \
                        "(or 'n')\n"

    opts = f"[{opts}]"
    while True:
        print(f"{prompt}\n{opts}")
        response = input().lower()
        # if user hits return without typing, return default response
        if (default is not None) and (not response):
            return valid_responses[default]
        elif response in valid_responses:
            return valid_responses[response]
        elif possible_bug and response == 'b':
            raise BugIdentified
        else:
            print(bad_input_msg)


def validate_repo(repo_path):
    # check directory exists
    if not isdir(repo_path):
        raise RepoNotFoundError(repo_path)
    # check that directory is a git repository
    if '.git' not in listdir(repo_path):
        raise NoGitdirError(repo_path)

    return repo_path
