from collections import namedtuple
from configparser import ConfigParser
from pathlib import Path
from git import InvalidGitRepositoryError
from .functions import CONVERTERS, add_config


class MockRepo:
    """patch for git.Repo"""
    def __init__(self, repo_path):
        self.repo_path = self._validate_repo(repo_path)
        self.config = self._load_config()

        self.untracked_files = self.config.getlist('repo', 'untracked_files')

        self.active_branch = self.MockActiveBranch(self.config['active_branch'])
        self.head = self.MockHead(self.config['head'])
        self.index = self.MockIndex(self.config['index'])
        self.submodules = self._setup_submodules(self.config['submodules'])

    def _load_config(self):
        config_path = self.repo_path.joinpath(f"{self.repo_path.name}.cfg")
        config = ConfigParser(converters=CONVERTERS)
        with open(config_path, 'r') as f:
            config.read_file(f)
        return config

    def _setup_submodules(self, submodules_config):
        submodules_dict = submodules_config.getdict('paths_configs')
        submodules = []
        for sm_path, sm_config in submodules_dict.items():
            # get the absolute path for the submodule directory
            full_path = self.repo_path.joinpath(sm_path)
            # create the new directory and any parents
            full_path.mkdir(parents=True)
            # add a .git directory (needed for creating MockRepo from submodule)
            full_path.joinpath('.git').mkdir()
            # copy in the submodule's config file
            add_config(sm_config, full_path)
            # create a MockSubmodule object
            submodules.append(MockSubmodule(sm_path, self.repo_path))
        return submodules

    def _validate_repo(self, repo_path):
        """
        converts path to a pathlib.Path object and ensures that:
            - repository path is absolute and platform-independent
            - mock repository was created at the given path
            - the correct config file was copied there during setup
            - a .git subdirectory was created during setup
        """
        repo_path = Path(repo_path).resolve()
        # make sure it exists
        assert repo_path.is_dir()
        # correct config file shares name with repository
        assert repo_path.joinpath(f'{repo_path.name}.cfg').is_file()
        # necessary to pass some checks in main module
        assert repo_path.joinpath('.git').is_dir()
        return repo_path

    def iter_commits(self, comparison_str):
        """
        immitates accepted args and functionality of
        git.Repo.iter_commits. Patched method returns a generator of
        git.objects.Commit instances, but it's simpler to mock the output
        by passing the task onto self.MockActiveBranch, which contains
        the attributes we need to access
        """
        return self.active_branch._compare_to_remote(comparison_str)

    class MockActiveBranch:
        """patch for git.refs.Head"""
        def __init__(self, branch_config):
            self.name = branch_config.get('name')
            self.remote_branch = branch_config.get('remote_branch')
            self.n_commits_ahead = branch_config.getint('n_commits_ahead')
            self.n_commits_behind = branch_config.getint('n_commits_behind')

        def _compare_to_remote(self, local_remote_str):
            """see MockRepo.iter_commits()"""
            comparator, reference = local_remote_str.split('..')
            # ensure string is formatted properly
            assert self.name in (comparator, reference)
            assert self.remote_branch in (comparator, reference)
            if reference == self.name:
                n_commits = self.n_commits_ahead
            else:
                n_commits = self.n_commits_behind
            # arbitrary generated value (we only care about the number)
            for _ in range(n_commits):
                yield "dummy_commit_object"

        def tracking_branch(self):
            """
            patched method returns a git.refs.RemoteReference instance,
            but since we need to access a single property of the
            returned object, it's simpler to just mock it with a
            namedtuple than an entire extra internal class
            """
            RemoteBranch = namedtuple('RemoteBranch', 'name')
            return RemoteBranch(name=self.remote_branch)

    class MockHead:
        """
        patch for git.refs.HEAD (note this is different from
        git.refs.Head, which is patched by the MockActiveBranch class)
        """
        def __init__(self, head_config):
            self.is_detached = head_config.getboolean('is_detached')
            self._is_empty = head_config.getboolean('_is_empty')
            self._hexsha = head_config.get('hexsha')

        @property
        def commit(self):
            """
            patch for .commit property, which returns a git.objects.Commit
            instance. We only ever use this to get the commit hash of a
            detached HEAD, so it's again simpler to mock with a namedtuple
            than a whole separate class
            """
            if self._is_empty:
                raise ValueError("This is raised intentionally to test "
                                 "behavior with empty repositories")
            HeadCommit = namedtuple('HeadCommit', 'hexsha')
            return HeadCommit(hexsha=self._hexsha)

    class MockIndex:
        """patch for git.index.IndexFile"""
        def __init__(self, index_config):
            self.staged_changes = index_config.getdifflist('staged_changes')
            self.unstaged_changes = index_config.getdifflist('unstaged_changes')

        def diff(self, other):
            """
            patched method returns a list of git.Diff objects, but
            similar to above, we only need to access 3 of their
            properties, so mocking them with namedtuples (via the custom
            `getdifflist` converter) is preferable to adding yet another
            nested class
            """
            if other is None:
                # passing None to git.index.IndexFile.diff() returns
                # diffs for tracked-but-not-staged files
                return self.unstaged_changes
            else:
                # quick spot check to make sure this is a HeadCommit
                # object (a bit hacky, but can't use `isinstance` on
                # types locally defined in different namespace)
                assert type(other).__name__ == 'HeadCommit'
                return self.staged_changes


class MockSubmodule:
    """
    patch for git.objects.Submodule

    Apart from the abaility to instantiate `git.Repo` object, we only
    need to patch the `path` and `hexsha` attributes from `git.Submodule`.
    Other attrs are used to mock behavior of submodules that are either
    in a detached HEAD state or not yet initialized.
    """
    def __init__(self, path, parent_path):
        self.path = path
        self._full_path = parent_path.joinpath(self.path)

        config = self._load_config()
        self.hexsha = config.get('head', 'hexsha')
        self._is_detached = config.getboolean('head', 'is_detached')
        self._is_initialized = not config.getboolean('head', '_is_empty')

    def _load_config(self):
        config_path = self._full_path.joinpath(f"{self._full_path.name}.cfg")
        config = ConfigParser(converters=CONVERTERS)
        with open(config_path, 'r') as f:
            config.read_file(f)
        return config

    def module(self):
        if self._is_detached:
            raise TypeError("This is raised intentionally to test behavior of "
                            "submodules with detached HEAD")
        elif self._is_initialized:
            raise InvalidGitRepositoryError("This is raised intentionally to "
                                            "test behavior of submodules that "
                                            "haven't been initialized")
        return MockRepo(self._full_path)
