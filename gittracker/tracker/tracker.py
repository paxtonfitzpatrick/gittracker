from shutil import get_terminal_size
from git import Repo, InvalidGitRepositoryError
from tqdm import tqdm


def get_status(repo_paths, verbose=2, follow_submodules=0):
    """
    Determines "git-status"-like information for a set of
    git repositories based on their (absolute) `repo_paths`.

    :param repo_paths: list-like
            Iterable of strings containing absolute paths to
            a predetermined set of local git repositories.
    :param verbose: int (defult 2)
            Verbosity level.  See docs for options and
            descriptions.
    :param follow_submodules: int (default 0)
            Maximum recursion depth for checking statuses
            of nested submodules in a repository. If 0
            [default], no submodule information will be
            included
    :return: dict
            a dictionary of {path: changes} for each local
            repository (in `repo_paths`). Otherwise, it will
            be a dict of set keys whose values depends on the
            `verbose` value. Note: if repository is fully
            up-to-date, `changes` is None. Or, if repository
            is in a detached HEAD state, `changes` will be
            a string instead.
    """
    # show a progress bar if number of repositories parsed is enough to
    # cause an appreciable wait time
    pbar_off = len(repo_paths) < 10
    ncols = get_terminal_size().columns
    changes = dict.fromkeys(repo_paths)
    for path in tqdm(repo_paths,
                     unit=' repo',
                     ncols=ncols,
                     leave=False,
                     disable=pbar_off):
        repo = Repo(path)
        changes[path] = _single_repo_status(repo,
                                            verbose=verbose,
                                            follow_submodules=follow_submodules)

    return changes


def _single_repo_status(repo, verbose, follow_submodules):
    """
    :param repo: git.Repo.base.Repo
            a Repo object referencing a
            local repository
    :param verbose: int
            verbosity level
    :param follow_submodules: bool
            whether or not to include submodules
    :return: dict
            {field: info} pairs.  Fields (keys) are sufficient
            to create a "git-status"-like output for a
            repository, though many are set to None at lower
            `verbose` values
    """
    # TODO (future?): option to get info about branches other than current
    status = {
        # local branch compared to remote tracking branch
        'local_branch': None,
        'remote_branch': None,
        'n_commits_ahead': None,
        'n_commits_behind': None,
        # uncommitted local changes
        'n_staged': None,
        'files_staged': None,
        'n_not_staged': None,
        'files_not_staged': None,
        'n_untracked': None,
        'files_untracked': None,
        # alternate info for repos in a detached HEAD state
        'is_detached': False,
        'hexsha': None,
        'from_branch': None,
        'ref_sha': None,
        'detached_commits': None,
        # info for submodules (if any)
        'submodules': None
    }
    try:
        headcommit = repo.head.commit

    except ValueError as e:
        raise InvalidGitRepositoryError(
            "GitTracker currently doesn't support tracking newly "
            f"initialized repositories (can't track {repo.working_dir}"
        ) from e

    if repo.head.is_detached:
        # if HEAD is detached, report some slightly different information
        status['is_detached'] = True
        status['hexsha'] = headcommit.hexsha[:7]
        from_branch, ref_sha, n_new_commits = _detached_status(repo)
        status['from_branch'] = from_branch
        if ref_sha != status['hexsha']:
            # if commits have been made since detaching HEAD, report hash
            # where initially detached and number of new commits
            status['ref_sha'] = ref_sha
            status['detached_commits'] = n_new_commits

    else:
        local_branch = repo.active_branch
        local_branch_name = local_branch.name
        try:
            remote_branch_name = local_branch.tracking_branch().name
            n_ahead = len(list(repo.iter_commits(
                f"{remote_branch_name}..{local_branch_name}"
            )))
            n_behind = len(list(repo.iter_commits(
                f"{local_branch_name}..{remote_branch_name}"
            )))
        except AttributeError:
            # local branch isn't tracking a remote
            remote_branch_name = ''
            n_ahead = None
            n_behind = None

        status['local_branch'] = local_branch_name
        status['remote_branch'] = remote_branch_name
        status['n_commits_ahead'] = n_ahead
        status['n_commits_behind'] = n_behind

    staged = headcommit.diff()
    unstaged = repo.index.diff(None)
    untracked = repo.untracked_files
    status['n_staged'] = len(staged)
    status['n_not_staged'] = len(unstaged)
    status['n_untracked'] = len(untracked)

    # always computing individual file diff info would make Displayer
    # format methods and unit tests simpler, but skipping when
    # unnecessary saves noticeable time if dealing with many repositories
    if verbose == 3:
        # go through any staged changes & manually to handle renames
        files_staged = []
        for diff in staged:
            a_path = diff.a_path
            change_type = diff.change_type
            # new filepath only matters if file was renamed
            b_path = diff.b_path if change_type == 'R' else None
            files_staged.append((change_type, a_path, b_path))

        status['files_staged'] = files_staged
        status['files_untracked'] = untracked
        status['files_not_staged'] = [
            (diff.change_type, diff.a_path, None) for diff in unstaged
        ]

    if follow_submodules > 0 and any(repo.submodules):
        submodules = {}
        for sm in repo.submodules:
            sm_status = _submodule_status(sm, depth=follow_submodules)
            submodules[sm.path] = sm_status

        status['submodules'] = submodules

    return status


def _detached_status(repo):
    # TODO: add docstring
    # log is listed oldest to newest, so reverse it
    log_entries = repo.head.log()[::-1]
    for n_new, log_entry in enumerate(log_entries):
        # log message for checkout takes the format:
        # "checkout: moving from <old branch> to <new branch/hexsha>"
        # the most recent checkout is the one that detached HEAD
        if log_entry.message.startswith('checkout: moving from'):
            info = log_entry.message.split()
            ref_branch = info[3]
            ref_sha = info[-1][:7]
            break

    else:
        # fallback/failsafe (shouldn't ever get here):
        #   - assume HEAD was detached from master and display assumption
        #   - return the current commit's sha so display excludes other info
        ref_branch = 'master [assumed]'
        ref_sha = log_entries[0].newhexsha[:7]

    return ref_branch, ref_sha, n_new


def _submodule_status(submodule, depth=1):
    """
    Helper function that recursively gets basic
    information about the status of any submodules
    :param submodule: git.objects.submodule.base.Submodule
            the submodule object of a parent repository
    :param depth: int
            the nested submodule depth of the *current* call
    :return: tuple
            2-tuple of (info, alt_message). If submodule behaves
            like a normal git repository, `info` is a status dict
            like that returned for the top-level repository and
            `alt_message` is None. Various misbehaviors result in
            `info` being None and `alt_message` being populated
            with a message instead
    """
    # TODO: Function needs testing
    # TODO: once expandable GUI view is finished, can allow variable verbosity.
    #  For now, pinning to 1 regardless of parent `verbose` value
    try:
        submodule_repo = submodule.module()
        sm_status = _single_repo_status(
            submodule_repo,
            verbose=1,
            follow_submodules=depth - 1
        )
        return sm_status, None

    except TypeError:
        # submodule is in a detached HEAD state
        sm_sha_shortened = submodule.hexsha[:7]
        msg = f'HEAD detached at {sm_sha_shortened}'
        return None, msg

    except InvalidGitRepositoryError:
        # submodule hasn't been initialized
        msg = 'not initialized'
        return None, msg




