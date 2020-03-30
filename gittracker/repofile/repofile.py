from os import getcwd, walk
from os.path import basename, isdir, join as opj
from pathlib import Path
from sys import exit
from ..util.exceptions import RepoNotFoundError, NoGitdirError
from ..util.util import (
    cleanpath,
    clear_display,
    log_error,
    prompt_input,
    GITHUB_URL,
    validate_repo
)


KNOWN_REPOS_FPATH = opj(Path(__file__).parents[1], 'log', 'known-repos')


@log_error(show=True)
def auto_find_repos(
        toplevel_dir=None,
        ignore_hidden=True,
        ignore_dirs=None,
        quiet=False,
        permission_err='show'
):

    # default to searching under current working directory
    if toplevel_dir is None:
        toplevel_dir = getcwd()

    toplevel_dir = cleanpath(toplevel_dir)
    if not isdir(toplevel_dir):
        exit(f"{toplevel_dir} does not appear to be a directory")

    # prioritize `quiet` arg over permission_err (`quiet=True` silences OSErrors)
    if quiet:
        permission_err = 'ignore'

    # set behavior when trying to search directory raises PermissionError
    if permission_err == 'ignore':
        _onerr_func = None
    elif permission_err == 'show':
        def _onerr_func(e): print(f"\033[31mpermission denied for {e.filename}\033[0m")
    elif permission_err == 'raise':
        def _onerr_func(e): raise e
    else:
        raise ValueError("permission_err must be one of: 'ignore', 'show', or "
                         f"'raise'. Got {permission_err}")

    if ignore_hidden:
        if basename(toplevel_dir).startswith('.'):
            exit("top-level directory cannot be hidden if hidden directories "
                 "are excluded from search")

        def _hidden_filter(x): return not x.startswith('.')
    else:
        def _hidden_filter(x): return True

    if ignore_dirs is None:
        def _dir_filter(x): return True
    else:
        if isinstance(ignore_dirs, str):
            ignore_dirs = [ignore_dirs]
        else:
            ignore_dirs = list(ignore_dirs)

        if toplevel_dir in ignore_dirs:
            exit("top-level directory was passed as a directory to be ignored")

        def _dir_filter(x): return x not in ignore_dirs

    def _filter_func(x): return _dir_filter(x) and _hidden_filter(x)

    # walk directory structure from outermost level
    repos_found = []
    print("searching for git repositories...")
    for dirpath, dirs, files in walk(toplevel_dir):
        print(f"{len(repos_found)} repositories found", end='\r')
        # if the directory contains a .git folder, we're probably found one
        if '.git' in dirs:
            if not quiet:
                print(dirpath)
            repos_found.append(dirpath)
            # don't recurse further into identified git repositories
            dirs[:] = []
        # don't recurse into directories excluded by argument options
        dirs[:] = list(filter(_filter_func, dirs))

    clear_display()
    n_found = len(repos_found)
    if n_found == 0:
        exit(f"\033[31mNo repositories found\033[0m under {toplevel_dir}.\n"
              "If you think GitTracker missed something, you can try manually "
              "adding repositories with:\n\t`gittracker add repo/path/one "
              "repo/path/two ...\nAlso please consider posting an issue at:\n\t"
              f"{GITHUB_URL}")
    else:
        print(f"\033[32mfound {n_found} git repositories:\033[0m", end='\n\t')
        print('\n\t'.join(repos_found))
        add_confirmed = prompt_input(
            "Do you want GitTraacker to track these repositories?",
            default='yes',
            possible_bug=True
        )
        if add_confirmed:
            with open(KNOWN_REPOS_FPATH, 'a') as f:
                f.write('\n'.join(repos_found))
            exit(f"\033[32mGitTracker: {n_found} repositories stored for "
                 f"tracking in logfile at {KNOWN_REPOS_FPATH}\033[0m")


def load_known_repos():
    # loads in known-repos file as a list of paths (strings)
    with open(KNOWN_REPOS_FPATH, 'r') as f:
        paths = f.read().splitlines()
    return paths


@log_error
def manual_add(repo_path):
    full_path = cleanpath(repo_path)
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
            exit(f"\033[31m{full_path} is already tracked by GitTracker\033[0m")
        else:
            with open(KNOWN_REPOS_FPATH, 'a') as f:
                f.write(f"{full_path}\n")
            exit(f"GitTracker: repository '{basename(full_path)}' stored for "
                 f"tracking in logfile at {KNOWN_REPOS_FPATH}")


def manual_remove(repo_path):
    # manually remove a repository from
    # known-repos file and stop tracking it
    full_path = cleanpath(repo_path)
    tracked_repos = load_known_repos()
    try:
        tracked_repos.remove(full_path)
        with open(KNOWN_REPOS_FPATH, 'w') as f:
            f.write('\n'.join(tracked_repos))
            # always leave newline at end for simplicity
            f.write('\n')
    except ValueError:
        exit(f"\033[31m{full_path} is not currently tracked by GitTracker.\033[0m"
             "\nYou can view the currently tracked repositories with:"
             "\n\tgittracker ls")


def show_tracked(quiet=False):
    # output a list of currently tracked
    # repositories to the screen. If quiet
    # is True, show directory names only.
    # Otherwise, show full paths.
    tracked = load_known_repos()
    if quiet:
        tracked = list(map(lambda p: basename(p), tracked))
    print(
        f"\033[032mGitTracker: tracking {len(tracked)} repositories:\033[0m",
        end='\n\t'
    )
    print('\n\t'.join(tracked))
    if not quiet:
        exit(f"")
