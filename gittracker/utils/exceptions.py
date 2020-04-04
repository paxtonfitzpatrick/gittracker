from inspect import currentframe, getouterframes


class GitTrackerError(Exception):
    pass


class BugIdentified(GitTrackerError):
    # handles exception info logging for bugs identified by users via the
    # `utils.prompt_input` function
    def __init__(self):
        input_caller = getouterframes(currentframe())[2].function
        msg = f"Bug identified via user input from function: {input_caller}"
        super().__init__(msg)


class NoGitdirError(GitTrackerError):
    def __init__(self, repo_path):
        msg = f"{repo_path} does not appear to be a git repository " \
              "(no .git directory found)"
        super().__init__(msg)


class RepoNotFoundError(GitTrackerError):
    def __init__(self, repo_path):
        msg = f"{repo_path} does not appear to be a directory"
        super().__init__(msg)