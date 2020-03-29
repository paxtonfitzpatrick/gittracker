class GitTrackerError(Exception):
    pass


class RepoNotFoundError(GitTrackerError):
    def __init__(self, repo_path):
        msg = f"{repo_path} does not appear to be a directory"
        super().__init__(msg)


class NoGitdirError(GitTrackerError):
    def __init__(self, repo_path):
        msg = f"{repo_path} does not appear to be a git repository " \
              "(no .git directory found)"

