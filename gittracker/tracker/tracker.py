from git import Repo, InvalidGitRepositoryError


def get_status(repo_paths, verbose=2, follow_submodules=0):
    """
    Determines "git-status"-like information for a set of
    git repositories based on their (absolute) `repo_paths`.

    :param repo_paths: list-like
            Iterable of strings containing absolute paths to
            a predetermined set of local git repositories.
    :param verbose: int (defult 2)
            Verbosity level.  See ___ for options and
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
            verbosity level. Note: if repository is fully
            up-to-date, `changes` is None. Or, if repository
            is in a detached HEAD state, `changes` will be
            a string instead.
    """
    changes = dict.fromkeys(repo_paths)
    for path in repo_paths:
        repo = Repo(path)
        # this can either mean repo is up-to-date or HEAD is detached
        if not repo.is_dirty():
            if repo.head.is_detached:
                # if HEAD is detached, just report its commit hash...
                sha_shortened = repo.head.object.hexsha[:7]
                changes[path] = f'HEAD detached at {sha_shortened}'
            else:
                # ...or, if everything is up-to-date, no need to check further
                changes[path] = None
            continue

        raw_changes = _single_repo_status(
            repo,
            verbose=verbose,
            follow_submodules=follow_submodules
        )
        changes[path] = raw_changes

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
            field: info pairs.  Fields (keys) are sufficient
            to create a "git-status"-like output for a
            repository, though many are set to None at lower
            verbosity levels
    """
    # TODO (future): option to get info about branches other than current
    status = {
        # str if verbose == 2
        'local_branch': None,
        # str if verbose == 2
        'remote_branch': None,
        # int if verbose >= 1
        'n_commits_ahead': None,
        # int if verbose >= 1
        'n_commits_behind': None,
        # int if verbose >= 1
        'n_staged': None,
        # list of (change type, old filepath, new filepath) if verbose == 2
        # if change type wasn't a rename, then new filepath is None
        'files_staged': None,
        # int if verbose >= 1
        'n_not_staged': None,
        # list of (change type, filepath) if verbose == 2
        'files_not_staged': None,
        # int if verbose >= 1
        'n_untracked': None,
        # list of filepaths if verbose == 2
        'files_untracked': None,
        # dict of {path: status} pairs if follow_submodules is True and the repo
        # contains any submodules.
        'submodules': None
    }

    if verbose > 0:
        local_branch = repo.active_branch
        local_branch_name = local_branch.name
        remote_branch_name = local_branch.tracking_branch().name
        headcommit = repo.head.commit
        staged = repo.index.diff(headcommit)
        unstaged = repo.index.diff(None)
        untracked = repo.untracked_files
        status['local_branch'] = local_branch_name
        status['remote_branch'] = remote_branch_name
        status['n_commits_ahead'] = len(
            list(repo.iter_commits(f"{remote_branch_name}..{local_branch_name}"))
        )
        status['n_commits_behind'] = len(
            list(repo.iter_commits(f"{local_branch_name}..{remote_branch_name}"))
        )
        status['n_staged'] = len(staged)
        status['n_not_staged'] = len(unstaged)
        status['n_untracked'] = len(untracked)

        if verbose == 2:
            # go through any staged changes manually to handle renames
            files_staged = []
            for diff in staged:
                a_path = diff.a_path
                change_type = diff.change_type
                b_path = diff.b_path if change_type == 'R' else None
                files_staged.append((change_type, a_path, b_path))

            status['files_staged'] = files_staged
            status['files_not_staged'] = list(
                map(lambda d: (d.change_type, d.a_path), unstaged)
            )
            status['files_untracked'] = untracked

        if follow_submodules > 0 and any(repo.submodules):
            submodules = {}
            for sm in repo.submodules:
                sm_status = _submodule_status(sm, depth=follow_submodules)
                submodules[sm.path](sm_status)

            status['submodules'] = submodules

    return status


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
    #  For now, pinning to 1 regardless of parent verbosity levels
    try:
        submodule_repo = submodule.module()
        sm_status = _single_repo_status(
            submodule_repo,
            verbose=1,
            follow_submodules=depth - 1)
        return sm_status, None

    except TypeError:
        sm_sha_shortened = submodule.hexsha[:7]
        msg = f'HEAD detached at {sm_sha_shortened}'
        return None, msg

    except InvalidGitRepositoryError:
        msg = 'not initialized'
        return None, msg



