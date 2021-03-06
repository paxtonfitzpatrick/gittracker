import os
from datetime import datetime as dt
from functools import wraps
from os.path import expanduser, expandvars, isdir, realpath
from pathlib import Path
from sys import exit, platform
from traceback import print_exception
from .exceptions import BugIdentified, RepoNotFoundError, NoGitdirError

LOG_DIR = Path(__file__).resolve().parents[1].joinpath('log')
LOGFILE_PATH = Path(LOG_DIR, 'logfile')
GITHUB_URL = "https://github.com/paxtonfitzpatrick/gittracker/issues/new"
BUG_MSG = "\n\nUh oh! Looks like you might have encountered a bug, please " \
          f"consider posting an issue at:\n\t{GITHUB_URL}\n\nwith the " \
          f"contents of the logfile, found at:\n\t{LOGFILE_PATH}\n\n"


def cleanpath(path):
    return realpath(expanduser(expandvars(path)))


def clear_display():
    if is_windows():
        os.system('cls')
    else:
        os.system('clear')


def is_windows():
    return platform.startswith('win')


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
                tb = e.__traceback__
                curr_time = dt.now().ctime()
                with open(LOGFILE_PATH, 'a') as logfile:
                    # logfile formatting for readability
                    logfile.write(f"{curr_time}\n\n")
                    print_exception(type(e), e, tb=tb, file=logfile)
                    logfile.write(f"\n\n{'='*60}\n\n")
                    if show:
                        print_exception(type(e), e, tb=tb, file=None)
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
    :param possible_bug: bool
            if True, an input option is added for the user to
            identify a bug.
    :return: bool
            True for affirmative response, False for negative
    """
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
        prompt += "\n(or, if you think you've encountered a bug, please " \
                  "enter 'b')"
        opts += '/b'
        bad_input_msg = "Please respond with either 'yes' (or 'y'), 'no' " \
                        "(or 'n'), or 'b' if you think you've encountered a bug"
    else:
        bad_input_msg = "Please respond with either 'yes' (or 'y') or 'no' " \
                        "(or 'n')"

    opts = f"[{opts}]"
    response = input(f"\n{prompt}\n{opts}\n").lower()
    while True:
        # if user hits return without typing, return default response
        if (default is not None) and (not response):
            return valid_responses[default]
        elif response in valid_responses:
            return valid_responses[response]
        elif possible_bug and response == 'b':
            raise BugIdentified
        else:
            response = input(f"\n{bad_input_msg}\n{opts}\n").lower()


def validate_repo(repo_path):
    cleaned_path = cleanpath(repo_path)
    # check directory exists
    if not isdir(cleaned_path):
        raise RepoNotFoundError(cleaned_path)
    # check that directory is a git repository
    if '.git' not in os.listdir(cleaned_path):
        raise NoGitdirError(cleaned_path)

    return cleaned_path


def validate_writable_path(path):
    # checks that a file path is valid and writable,
    # and converts it to a pathlib.Path object
    if path is None:
        return
    full_path = Path(cleanpath(path))
    parent_dir = full_path.parent
    err_msg = f"\nunable to write to {full_path}"
    if not parent_dir.is_dir():
        exit(f"\033[31m{err_msg}\ndirectory {parent_dir} does not exist\033[0m")
    if not os.access(parent_dir, mode=os.W_OK):
        exit(f"\033[31m{err_msg}\nlacking write permission for parent "
             f"directory: {parent_dir}\033[0m")
    return full_path
