from os.path import realpath, join as opj
from pathlib import Path
from ..util.exceptions import RepoNotFoundError, NoGitdirError
from ..util.util import log_error, prompt_input, validate_repo


KNOWN_REPOS_FPATH = opj(Path(__file__).parents[1], 'log', 'known-repos')


def load_known_repos():
    with open(KNOWN_REPOS_FPATH, 'r') as f:
        paths = f.read().splitlines()
    return paths


@log_error
def manual_add(repo_path):
    full_path = realpath(repo_path)
    try:
        validate_repo(full_path)
        valid = True
    except RepoNotFoundError as e:
        # if directory doesn't exist at given path, ask for confirmation
        prompt = f"{full_path} does not appear to be a directory. Add it anyway?"
        valid = prompt_input(prompt, default='no')
    except NoGitdirError as e:
        # if directory exists but isn't a git repository, ask for confirmation
        prompt = f"{full_path} does not appear to be a git repository. Add it anyway?"
        valid = prompt_input(prompt, default='no')

    if valid:
        if _is_tracked(full_path):
            # don't add a duplicate if the repository is already being tracked
            print(f"{full_path} is already tracked by GitTracker")
        else:
            with open(KNOWN_REPOS_FPATH, 'a') as f:
                f.write(f"{full_path}\n")


def _is_tracked(repo_path):
    tracked = load_known_repos()
    if repo_path in tracked:
        return True
    else:
        return False










# def find_repos(toplevel_dir, ignore_dirs=None, include_submodules=False):
#     repos = []
#
#     for dirpath,