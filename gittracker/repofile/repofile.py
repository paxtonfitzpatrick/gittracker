from os.path import basename, realpath, join as opj
from pathlib import Path
from ..util.exceptions import RepoNotFoundError, NoGitdirError
from ..util.util import log_error, prompt_input, validate_repo


KNOWN_REPOS_FPATH = opj(Path(__file__).parents[1], 'log', 'known-repos')


def load_known_repos():
    # loads in known-repos file as a list of paths (strings)
    with open(KNOWN_REPOS_FPATH, 'r') as f:
        paths = f.read().splitlines()
    return paths


@log_error
def manual_add(repo_path):
    full_path = realpath(repo_path)
    try:
        validate_repo(full_path)
        valid = True
    except RepoNotFoundError:
        # if directory doesn't exist at given path, ask for confirmation
        prompt = f"{full_path} does not appear to be a directory. Add it " \
                 "anyway?"
        valid = prompt_input(prompt, default='no')
    except NoGitdirError:
        # if directory exists but isn't a git repository, ask for confirmation
        prompt = f"{full_path} does not appear to be a git repository. Add " \
                 "it anyway?"
        valid = prompt_input(prompt, default='no')

    if valid:
        if full_path in load_known_repos():
            # don't add a duplicate if the repository is already being tracked
            print(f"{full_path} is already tracked by GitTracker")
        else:
            with open(KNOWN_REPOS_FPATH, 'a') as f:
                f.write(f"{full_path}\n")


def manual_remove(repo_path):
    # manually remove a repository from
    # known-repos file and stop tracking it
    full_path = realpath(repo_path)
    tracked_repos = load_known_repos()
    try:
        tracked_repos.remove(full_path)
        with open(KNOWN_REPOS_FPATH, 'w') as f:
            f.write('\n'.join(tracked_repos))
    except ValueError:
        print(f"{full_path} is not currently tracked by GitTracker")


def show_tracked(quiet=False):
    # output a list of currently tracked
    # repositories to the screen. If quiet
    # is True, show directory names only.
    # Otherwise, show full paths.
    tracked = load_known_repos()
    if quiet:
        tracked = list(map(lambda p: basename(p), tracked))
    print(f"Tracking {len(tracked)} repositories:", end='\n\t')
    print('\n\t'.join(tracked))











# def find_repos(toplevel_dir, ignore_dirs=None, include_submodules=False):
#     repos = []
#
#     for dirpath,