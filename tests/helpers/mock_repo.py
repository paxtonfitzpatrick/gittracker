from collections import namedtuple
from configparser import ConfigParser
from pathlib import Path
from git import InvalidGitRepositoryError
from .functions import CONVERTERS, add_submodule_config


class MockRepo:
    """patch for git.Repo"""
    def __init__(self, repo_path):
        self.repo_path = self._validate_repo(repo_path)
        self._config = self._load_config()

        self._staged_changes = self._config.getdifflist('repo', 'staged_changes')
        self.unstaged_changes = self._config.getdifflist('repo', 'unstaged_changes')
        self.untracked_files = self._config.getlist('repo', 'untracked_files')
        self.head = self.MockHead(self._config['head'], self._staged_changes)
        # if HEAD is detached, we want to fail if trying to access
        # `repo.active_branch`, and also avoid creating a MockActiveBranch
        # without the necessary values in the config
        if self.head.is_detached:
            self.active_branch = property(self._failcase_active_branch)
        else:
            self.active_branch = self.MockActiveBranch(self._config['active_branch'])
        self.submodules = self._setup_submodules(self._config['submodules'])

    def _failcase_active_branch(self):
        """
        This happens if we try to reference the repo's `active_branch`
        attr from a detached HEAD state. TypeError is used to mirror the
        exception type raised by GitPython under the same circumstance.
        """
        raise TypeError("Tried to access the `active_branch` peoperty of a repo "
                        "with HEAD detached")

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
            sm_abspath = self.repo_path.joinpath(sm_path)
            # submodule may already have been set up by previous test
            if not sm_abspath.is_dir():
                sm_abspath.mkdir(parents=True)
                # .git dir needed to create MockRepo from submodule
                sm_abspath.joinpath('.git').mkdir()
                # copy in submodule's config file
                add_submodule_config(sm_config, sm_abspath)

            # create MockSubmodule object
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

    @property
    def index(self):
        """
        patch for git.index.IndexFile
        """
        def _get_staged_changes(none_arg):
            """
            in turn, a patch for the `git.index.IndexFile.diff(None)` method
            """
            # assertion test for my ability to remmeber to update this
            # when I inevitably start using this method for something else
            assert none_arg is None
            return self.unstaged_changes

        Index = namedtuple('index', 'diff')
        return Index(diff=_get_staged_changes)

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
            if self.remote_branch == '':
                self.n_commits_ahead = "THIS SHOULD NOT APPEAR IN OUTPUT"
                self.n_commits_behind = "THIS SHOULD NOT APPEAR IN OUTPUT"
            else:
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
            if self.remote_branch == '':
                raise AttributeError("Raised intentionally to test behavior "
                                     "with local branches not tracking a remote")
            RemoteBranch = namedtuple('RemoteBranch', 'name')
            return RemoteBranch(name=self.remote_branch)

    class MockHead:
        """
        patch for git.refs.HEAD (note this is different from
        git.refs.Head, which is patched by the MockActiveBranch class)
        """
        def __init__(self, head_config, staged_changes):
            self.is_detached = head_config.getboolean('is_detached')
            self._staged_changes = staged_changes
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
                raise ValueError("Raised intentionally to test behavior "
                                 "with empty repositories")

            def _get_staged_changes():
                """in turn, a patch for `git.objects.Commit`'s `diff` method"""
                return self._staged_changes

            HeadCommit = namedtuple('HeadCommit', ('hexsha', 'diff'))
            return HeadCommit(hexsha=self._hexsha, diff=_get_staged_changes)


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
            raise TypeError("Raised intentionally to test behavior of "
                            "submodules with detached HEAD")
        elif not self._is_initialized:
            raise InvalidGitRepositoryError("Raised intentionally to test "
                                            "behavior of submodules that "
                                            "haven't been initialized")
        else:
            return MockRepo(self._full_path)
