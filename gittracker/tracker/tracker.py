from git import Repo


def get_changes(repo_paths, verbose=2):
    """
    Determines "git-status"-like information for a set of
    git repositories based on their (absolute) `repo_paths`.
    :param repo_paths: list-like
            Iterable of strings containing absolute paths to
            a predetermined set of local git repositories.
    :param verbose: int
            Verbosity level.  See ___ for options and
            descriptions.
    :return: list
            a list of {path: changes} dicts with an entry for
            each local repository (in `repo_paths`).  Format of
            `changes` depends on verbosity level.
    """
    changes = []
    for path in repo_paths:
        repo = Repo(path)
        # if there are no changes, move onto the next one
        if not repo.is_dirty():
            continue

        raw_changes = get_repo_changes(repo)












def get_repo_changes(repo, verbose=False):
    """

    :param repo: a git.Repo.base.Repo object
    :param verbose:
    :return:
    """
    # get changes for a single repo
    # returns a dict of {

    pass

