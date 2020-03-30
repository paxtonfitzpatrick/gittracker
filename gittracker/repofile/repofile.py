from os import getcwd, walk
from os.path import basename, isdir, join as opj
from pathlib import Path
from sys import exit
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


TRACKED_REPOS_FPATH = opj(Path(__file__).parents[1], 'log', 'tracked-repos')


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
              "adding repositories with:\n\t`gittracker add repo/one/path "
              "repo/two/path ...\nAlso please consider posting an issue at:\n\t"
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
            with open(TRACKED_REPOS_FPATH, 'a') as f:
                f.write('\n'.join(repos_found))
            exit(f"\033[32mGitTracker: {n_found} repositories stored for "
                 f"tracking in logfile at {TRACKED_REPOS_FPATH}\033[0m")


def load_tracked_repos():
    # loads in tracked-repos file as a list of paths (strings)
    with open(TRACKED_REPOS_FPATH, 'r') as f:
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
        if full_path in load_tracked_repos():
            # don't add a duplicate if the repository is already being tracked
            exit(f"\033[31m{full_path} is already tracked by GitTracker\033[0m")
        else:
            with open(TRACKED_REPOS_FPATH, 'a') as f:
                f.write(f"{full_path}\n")
            exit(f"GitTracker: repository '{basename(full_path)}' stored for "
                 f"tracking in logfile at {TRACKED_REPOS_FPATH}")


def manual_remove(repo_path):
    # manually remove a repository from
    # tracked-repos file and stop tracking it
    full_path = cleanpath(repo_path)
    tracked_repos = load_tracked_repos()
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
    tracked = load_tracked_repos()
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

    tracked = load_tracked_repos()
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
