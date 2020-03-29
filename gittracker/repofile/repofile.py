from os.path import realpath, join as opj
from pathlib import Path
from ..util.exceptions import RepoNotFoundError, NoGitdirError
from ..util.util import log_error, prompt_input, validate_repo


KNOWN_REPOS_FPATH = opj(Path(__file__).parents[2], 'log', 'known-repos')


def load_known_repos():
    with open(KNOWN_REPOS_FPATH, 'r') as f:
        paths = f.read().splitlines()
    return paths


def manual_add(repo_path):
    path = realpath(repo_path)
    try:
        validate_repo(repo_path)
    except RepoNotFoundError as e:
        prompt =





    with open(KNOWN_REPOS_FPATH, )









# def find_repos(toplevel_dir, ignore_dirs=None, include_submodules=False):
#     repos = []
#
#     for dirpath,