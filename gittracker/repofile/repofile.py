from os import getcwd, stat, walk
from os.path import basename, isdir
from pathlib import Path
from sys import exit
from ..display.ascii import DEFAULT_LOGO
from ..util.exceptions import (
    BugIdentified,
    GitTrackerError,
    NoGitdirError,
    RepoNotFoundError
)
from ..util.util import (
    cleanpath,
    clear_display,
    log_error,
    prompt_input,
    GITHUB_URL,
    validate_repo
)


TRACKED_REPOS_FPATH = Path(Path(__file__).resolve().parents[1], 'log', 'tracked-repos')


@log_error(show=True)
def auto_find_repos(
        toplevel_dir=None,
        ignore_hidden=True,
        ignore_dirs=None,
        quiet=False,
        permission_err='show'
):
    already_tracked = load_tracked_repos()
    # default to searching under current working directory
    if toplevel_dir is None:
        toplevel_dir = getcwd()

    toplevel_dir = cleanpath(toplevel_dir)
    if not isdir(toplevel_dir):
        exit(f"{toplevel_dir} does not appear to be a directory")
    elif toplevel_dir in already_tracked:
        exit(f"already tracking top-level directory: {toplevel_dir}")

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
        raise exit("permission_err must be one of: 'ignore', 'show', or "
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
    if not quiet:
        print("searching for git repositories...")
    for dirpath, dirs, files in walk(toplevel_dir, onerror=_onerr_func):
        print(f"{len(repos_found)} repositories found", end='\r')
        # if the directory contains a .git folder, we're probably found one
        if '.git' in dirs:
            if dirpath in already_tracked:
                # skip previously added repos and their subdirectories
                print(f"skipping {dirpath} (already tracked)")
                dirs[:] = []
                continue
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
        exit("\033[31mNo untracked repositories found\033[0m under "
             f"{toplevel_dir}.\nIf you think GitTracker missed something, you "
             "can try manually adding repositories with:\n\t`gittracker add "
             "repo/one/path repo/two/path ...\nAlso please consider posting an "
             f"issue at:\n\t{GITHUB_URL}")
    else:
        suff1, suff2 = ('y', 'is') if n_found == 1 else ('ies', 'ese')
        print(f"\033[32mfound {n_found} git repositor{suff1}:\033[0m", end='\n\t')
        print('\n\t'.join(repos_found))
        add_confirmed = prompt_input(
            f"Do you want GitTracker to track th{suff2} repositor{suff1}?",
            default='yes',
            possible_bug=True
        )
        if add_confirmed:
            with open(TRACKED_REPOS_FPATH, 'a') as f:
                f.write('\n'.join(repos_found))
                # always leave newline at end for simplicity
                f.write('\n')
            exit(f"\033[32mGitTracker: {n_found} new repositor{suff1} stored "
                 f"for tracking in logfile at {TRACKED_REPOS_FPATH}\033[0m")


def manual_init():
    print(DEFAULT_LOGO)
    _initialize_file(internal=False)


def _initialize_file(internal=True):
    if internal:
        print("GitTracker isn't currently tracking any repositories")

    prompt = "Would you like to initialize GitTracker by:\n - [a]utomatically " \
             "searching for local repositories? Or\n - [m]anually entering " \
             "repository paths?\n(enter 'q' to quit)\n[a/m/q]\n"
    response = input(prompt).lower()
    while True:
        if response == 'q':
            exit()

        elif response == 'a':
            toplevel_dir = input("Enter the path to the outermost directory "
                                 "you'd like to search under\n")
            while True:
                if toplevel_dir == 'q':
                    return

                auto_find_repos(toplevel_dir)
                toplevel_dir = input("Enter another directory to search under, "
                                     "or 'q' if you're done\n")

        elif response == 'm':
            repo_path = input("Enter the path to a repository you'd like to track\n")
            while True:
                if repo_path == 'q':
                    return

                manual_add(repo_path)
                repo_path = input("Enter another repository path, or 'q' if "
                                  "you're done\n")


def load_tracked_repos(init_on_fail=True):
    # loads in tracked-repos file as a list of paths (strings)
    # situation-dependent, either prompts to initialize file
    # or returns an empty list
    try:
        with open(TRACKED_REPOS_FPATH, 'r') as f:
            paths = f.read().splitlines()
            assert len(paths) > 0
    except (AssertionError, FileNotFoundError):
        if init_on_fail:
            _initialize_file()
            with open(TRACKED_REPOS_FPATH, 'r') as f:
                paths = f.read().splitlines()
        else:
            paths = []

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
        if full_path in load_tracked_repos(init_on_fail=False):
            # don't add a duplicate if the repository is already being tracked
            print(f"\033[31m{full_path} is already tracked by GitTracker\033[0m")
        else:
            with open(TRACKED_REPOS_FPATH, 'a') as f:
                f.write(f"{full_path}\n")
            print(f"GitTracker: repository '{basename(full_path)}' stored for "
                  f"tracking in logfile at {TRACKED_REPOS_FPATH}")


def manual_remove(repo_path):
    # manually remove a repository from
    # tracked-repos file and stop tracking it
    full_path = cleanpath(repo_path)
    tracked_repos = load_tracked_repos(init_on_fail=False)
    try:
        tracked_repos.remove(full_path)
        with open(TRACKED_REPOS_FPATH, 'w') as f:
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
    tracked = load_tracked_repos(init_on_fail=True)
    if quiet:
        tracked = list(map(lambda p: basename(p), tracked))
    print(
        f"\033[032mGitTracker: tracking {len(tracked)} repositories:\033[0m",
        end='\n\t'
    )
    print('\n\t'.join(tracked))


@log_error
def validate_tracked():
    def _update_repofile(tracked_paths, replacements, removals):
        # helper function that takes care of updating/removing
        # user-specified repo paths in the logfile, either after
        # checking all existing paths or as cleanup before raising
        # exception
        if len(replacements) == 0 and len(removals) == 0:
            return
        # replace updated paths
        for old, new in replacements:
            ix = tracked_paths.index(old)
            tracked_paths[ix] = new
        # remove deleted paths
        for removal in removals:
            tracked_paths.remove(removal)
        with open(TRACKED_REPOS_FPATH, 'w') as f:
            f.write('\n'.join(tracked_paths))
            # always leave newline at end of file for convenience
            f.write('\n')

    tracked = load_tracked_repos(init_on_fail=False)
    # list of tuples (old path, new path)
    to_replace = []
    # list of paths to be removed
    to_remove = []
    for repo_path in tracked:
        try:
            validate_repo(repo_path)
        except GitTrackerError as e:
            if isinstance(e, RepoNotFoundError):
                error_info = "\033[31mPreviously tracked repository at " \
                             f"{repo_path} appears to no longer exist\033[0m. " \
                             "Has the repository been moved or deleted?"

            elif isinstance(e, RepoNotFoundError):
                error_info = "\033[31mPreviously tracked directory at " \
                             f"{repo_path} appears to no longer be a git " \
                             "repository (no .git directory found)\033[0m/. " \
                             "Has the repository been moved or deleted?"
            else:
                # unexpected exception - should never get here, but it's a failsafe
                _update_repofile(tracked, to_replace, to_remove)
                raise e

            options_info = "- Enter 'u' to update the repository's path\n" \
                           "- Enter 'd' to stop tracking the repository\n" \
                           "- Enter 'b' if you think you've encountered a bug " \
                           "in GitTracker\n- Enter 'q' to quit\n"
            options = '[u/d/b/q]'
            response = input(f"{error_info}\n{options_info}\{options}\n").lower()
            while True:
                if response == 'u':
                    update_prompt = f"please enter the updated path for {repo_path}\n"
                    input_path = input(update_prompt)
                    full_path = cleanpath(input_path)
                    try:
                        validate_repo(full_path)
                        replace_confirmed = True
                    except RepoNotFoundError:
                        override_prompt = f"{full_path} does not appear to " \
                                          "be a directory. Add it anyway?"
                        replace_confirmed = prompt_input(
                            override_prompt,
                            default='no',
                            possible_bug=True
                        )
                    except NoGitdirError:
                        override_prompt = f"{full_path} does not appear to " \
                                          "be a git repository. Add it anyway?"
                        replace_confirmed = prompt_input(
                            override_prompt,
                            default='no',
                            possible_bug=True
                        )
                    if replace_confirmed:
                        to_replace.append((repo_path, full_path))
                        break
                elif response == 'd':
                    delete_prompt = f"stop tracking {repo_path}?"
                    delete_confirmed = prompt_input(delete_prompt, default='no')
                    if delete_confirmed:
                        to_remove.append(repo_path)
                        break
                elif response == 'b':
                    _update_repofile(tracked, to_replace, to_remove)
                    raise BugIdentified
                else:
                    # remaining condition: response == 'q'
                    print("exiting...")
                    _update_repofile(tracked, to_replace, to_remove)
                    exit()
                # re-prompt with options if user wants to "go back" (e.g., does
                # not confirm deletion or update to non-repo directory)
                response = input(f"{options_info}\n{options}\n").lower()

    # finally, update file with changes (if any) after all are validated
    _update_repofile(tracked, to_replace, to_remove)
