from os.path import basename
from shutil import get_terminal_size
from .ascii import RANDOM_LOGO
from .templates import (ANSI_SEQS,
                        OUTER_TEMPLATE,
                        SINGLE_REPO_SIMPLE,
                        SINGLE_REPO_COMPLEX,
                        BRANCH_INFO_STANDARD,
                        BRANCH_INFO_DETACHED,
                        LOCAL_CHANGES_V2,
                        SINGLE_CHANGE_STATE,
                        SINGLE_FILE_CHANGE,
                        SINGLE_SUBMODULE)
from ..utils.utils import clear_display


class Displayer:
    def __init__(self, repos, verbose=2, outfile=None, plain=False):
        """
        Class that handles formatting and displaying information
        for tracked repositories according to the given
        `verbose` level
        :param repos: dict
                dictionaries of {path: changes} for each repository.
                `changes` typically contains "git-status"-like
                information. See `gittracker.tracker.tracker` for
                further details
        :param verbose: int {1, 2, 3} (default: 2)
                verbosity level of output (1 is least verbose)
        :param outfile: pathlib.Path (optional)
                the file to which the output should be written.
                If None [default], write to sys.stdout with stylized
                formatting (note: plain text file output is not stylized)
        :param plain: bool
                if True, don't color or stylize the displayed output
        """
        self.repos = repos
        self.verbose = verbose
        self.outfile = outfile
        self.plain = plain
        self.outer_template = OUTER_TEMPLATE
        self.logo = RANDOM_LOGO

        if self.verbose == 1:
            self.repo_template = SINGLE_REPO_SIMPLE
            self.repo_format_func = self._format_simple
            self.local_format_func = None
        else:
            self.repo_template = SINGLE_REPO_COMPLEX
            self.repo_format_func = self._format_complex
            if self.verbose == 2:
                self.local_format_func = self._format_local_v2
            else:
                self.local_format_func = self._format_local_v3

        # holds completed outer template to display
        self.full_template = None
        # skip formatting if plain style was requested or writing to file
        self._dont_apply_style = self.plain or self.outfile is not None

    @property
    def display_width(self):
        return get_terminal_size().columns

    def apply_style(self, value, style=None):
        """
        Returns a string-formatted value to be inserted into
        a template, surrounded by the ANSI escape sequences
        to set and unset the stylization
        :param value: str
                they value to be formatted
        :param style: str or iterable of str
                the styles (keys in self.ansi_seqs) to apply
                to the given `value` that will determine
                how it appears on-screen when displayed
        :return: str
                The string-formatted value, surrounded by
                ANSI escape sequences
        """
        if self._dont_apply_style or style is None:
            return value

        if isinstance(style, str):
            ansi_val = ANSI_SEQS[style]
        else:
            ansi_val = ";".join((str(ANSI_SEQS[s]) for s in style))

        style_code = f"\033[{ansi_val}m"
        reset_code = "\033[0m"
        return f"{style_code}{value}{reset_code}"

    def format_status_display(self):
        # fill individual repo templates
        filled_repo_templates = []
        n_clean = 0
        for repo in self.repos.items():
            filled_repo_template, is_clean = self.repo_format_func(repo)
            filled_repo_templates.append(filled_repo_template)
            if is_clean:
                n_clean += 1

        n_total_fmt = self.apply_style(len(filled_repo_templates), 'bold')
        if n_clean == len(filled_repo_templates):
            # no repos have unpushed or uncommitted changes
            summary_msg = "all up-to-date"
            summary_msg_fmt = self.apply_style(summary_msg, 'green')
        elif n_clean == 0:
            # all repos have unpushed and/or uncommitted changes
            summary_msg = "all with changes"
            summary_msg_fmt = self.apply_style(summary_msg, 'red')
        else:
            # standard case (mix of repos with & without changes):
            # color "good"/"bad" counts separately
            n_dirty = len(filled_repo_templates) - n_clean
            n_clean_fmt = self.apply_style(n_clean, ('bold', 'green'))
            n_dirty_fmt = self.apply_style(n_dirty, ('bold', 'red'))
            summary_msg_fmt = f"{n_clean_fmt} up-to-date, {n_dirty_fmt} with changes"

        # mapping for self.outer_template
        template_mapping = {
            'ascii_logo': self.logo,
            'n_repos_tracked': n_total_fmt,
            'summary_msg': summary_msg_fmt,
            'line_sep': '=' * self.display_width,
            'repos_status': '\n'.join(filled_repo_templates)
        }
        full_template = self.outer_template.safe_substitute(template_mapping)

        # cleans up template formatting for verbosity level 3
        # in cases where repos have no uncommitted changes
        full_template = full_template.replace('    \n', '\n')
        self.full_template = full_template.replace('\n\n\n', '\n\n')

    def _format_simple(self, repo_info):
        # repo_info is a tuple of (key, value) from self.repos
        repo_path, status = repo_info
        repo_name = basename(repo_path)
        if any(status[k] for k in ('is_detached', 'n_commits_ahead',
                                   'n_commits_behind', 'n_staged',
                                   'n_not_staged', 'n_untracked')):
            repo_clean = False
            style = 'red'
        else:
            repo_clean = True
            style = 'green'
        repo_name_fmt = self.apply_style(repo_name, style=style)
        template_mapping = {'repo_name': repo_name_fmt}
        filled_template = self.repo_template.safe_substitute(template_mapping)
        return filled_template, repo_clean

    def _format_complex(self, repo_info):
        # repo_info is a tuple of (key, value) from self.repos
        repo_path, status = repo_info
        repo_name = basename(repo_path)
        if status['is_detached']:
            branch_format_func = self._format_branch_detached
        else:
            branch_format_func = self._format_branch_standard
        branch_info, branch_clean = branch_format_func(status)
        local_changes, files_clean = self.local_format_func(repo_info)
        repo_clean = branch_clean and files_clean
        template_mapping = {
            'repo_name': repo_name,
            'repo_path': repo_path,
            'branch_info': branch_info,
            'local_changes': local_changes
        }
        filled_template = self.repo_template.safe_substitute(template_mapping)
        return filled_template, repo_clean

    def _format_branch_detached(self, repo_status):
        sha_msg = f"HEAD detached at {repo_status['hexsha']}"
        ref_sha = repo_status['ref_sha']
        n_commits = repo_status['detached_commits']
        if ref_sha is None:
            from_branch = repo_status['from_branch']
        else:
            from_branch = f"{repo_status['from_branch']}@{ref_sha}"
        if n_commits is None:
            new_commits = ''
        else:
            n_commits_fmt = self.apply_style(n_commits, 'red')
            new_commits = f"{n_commits_fmt} new commits since detached"
        branch_mapping = {
            'detached_at': self.apply_style(sha_msg, 'red'),
            'from_branch': self.apply_style(from_branch, 'bold'),
            'new_commits': new_commits
        }
        filled_template = BRANCH_INFO_DETACHED.safe_substitute(branch_mapping)
        # branch with detached HEAD is considered dirty; return False
        return filled_template, False

    def _format_branch_standard(self, repo_status):
        # default to assuming remote branch exists and is out of sync
        branch_clean = False
        local_branch = self.apply_style(repo_status['local_branch'], 'bold') + ':'
        remote_branch = self.apply_style(repo_status['remote_branch'], 'bold')
        n_ahead = repo_status['n_commits_ahead']
        n_behind = repo_status['n_commits_behind']
        n_ahead_fmt = self.apply_style(n_ahead, 'bold')
        n_behind_fmt = self.apply_style(n_behind, 'bold')
        if n_ahead is n_behind is None:
            # local branch is not tracking a remote branch
            local_branch = local_branch.rstrip(':')
            remote_branch = ''
            vs_remote = ''
            branch_clean = True
        elif n_ahead == n_behind == 0:
            # local branch is even with remote tracking branch
            vs_remote = "even with"
            branch_clean = True
        elif n_ahead > 0 and n_behind > 0:
            # local branch is both ahead of and behind remote
            vs_remote = f"{n_behind_fmt} commits behind, {n_ahead_fmt} ahead of"
        elif n_ahead > 0:
            # local branch is ahead of remote
            vs_remote = f"{n_ahead_fmt} commits ahead of"
        else:
            # local branch is behind remote
            vs_remote = f"{n_behind_fmt} commits behind"

        branch_mapping = {
            'local_branch': local_branch,
            'remote_branch': remote_branch,
            'vs_remote': vs_remote
        }
        filled_template = BRANCH_INFO_STANDARD.safe_substitute(branch_mapping)
        return filled_template, branch_clean

    def _format_local_v2(self, repo_status):
        n_uncommitted = (repo_status['n_staged']
                         + repo_status['n_not_staged']
                         + repo_status['n_untracked'])
        if n_uncommitted == 0:
            files_clean = True
            color = 'green'
        else:
            files_clean = False
            color = 'red'
        n_uncommitted_fmt = self.apply_style(n_uncommitted, (color, 'bold'))
        local_mapping = dict(n_uncommitted=n_uncommitted_fmt)
        filled_template = LOCAL_CHANGES_V2.safe_substitute(local_mapping)
        return filled_template, files_clean

    def _format_local_v3(self, repo_status):
        state_data = {
            'staged': ('files staged for commit', 'green'),
            'not_staged': ('files not staged for commit', 'red'),
            'untracked': ('untracked files', 'red')
        }
        change_codes = {
            'D': 'deleted',
            'M': 'modified',
            'N': 'new file',
            'R': 'renamed'
        }

        def _fill_file_templates(files):
            filled_file_templates = []
            for change_code, a_path, b_path in files:
                change_type = change_codes[change_code]
                if change_code == 'R':
                    filepath = f'{a_path} -> {b_path}'
                else:
                    filepath = a_path
                file_mapping = {'change_type': change_type, 'filepath': filepath}
                filled_file_template = SINGLE_FILE_CHANGE.safe_substitute(file_mapping)
                filled_file_templates.append(filled_file_template)
            return '\n\t'.join(filled_file_templates)

        filled_templates = []
        for state in ('staged', 'not_staged', 'untracked'):
            n_state_files = repo_status[f'n_{state}']
            if n_state_files == 0:
                continue
            message, style = state_data[state]
            state_files = repo_status[f'files_{state}']
            if n_state_files == 1:
                message = message.replace('files', 'file')
            if state == 'untracked':
                changed_files = '\n\t'.join(state_files)
            else:
                changed_files = _fill_file_templates(state_files)
            changed_files_fmt = self.apply_style(changed_files, style)
            state_mapping = {
                'n_changed': n_state_files,
                'change_state_msg': message,
                'changed_files': changed_files_fmt
            }
            filled_template = SINGLE_CHANGE_STATE.safe_substitute(state_mapping)
            filled_templates.append(filled_template)

        # NOTE: state of submodules does NOT affect the "up-to-date"
        # status (i.e., displayed color) of parent repo or contribute to
        # overall count shown by GitTracker
        if len(filled_templates) == 0:
            # if no uncommitted files, replace list of per-state templates
            # with broad message (shown by Git in same situation)
            files_clean = True
            filled_templates = ["nothing to commit, working tree clean"]
        else:
            files_clean = False

        submodules = repo_status['submodules']
        if self.verbose == 3 and submodules is not None:
            # optionally add a section with info for submodules
            submodules_fmt = self._format_submodules(submodules)
            filled_templates.append('submodules:')
            filled_templates.append(submodules_fmt)

        local_changes = '\n    '.join(filled_templates)
        return local_changes, files_clean

    def _format_submodules(self, submodules):
        """
        data for each submodule is a 2-tuple where one item is None
          regular case:
              - item 0 is a dict of same (non-verbose) status-info
                returned for regular repository
              - item 1 is None
          alternate case:
              - item 0 is None because submodule has a detached HEAD or
                hasn't been initialized
              - item 1 is a string with corresponding info
        """
        filled_submodule_templates = []
        for path, (status, err_msg) in submodules.items():
            scenario_1 = isinstance(status, dict) and err_msg is None
            scenario_2 = status is None and isinstance(err_msg, str)
            assert scenario_1 or scenario_2
            if scenario_1:
                if any(status[k] for k in ('is_detached', 'n_commits_ahead',
                                           'n_commits_behind', 'n_staged',
                                           'n_not_staged', 'n_untracked')):
                    info = 'working tree is dirty'
                    style = 'red'
                else:
                    info = 'working tree is clean'
                    style = 'green'
            else:
                info = err_msg
                style = 'red' if err_msg.startswith('HEAD') else 'green'
            info_fmt = self.apply_style(info, style)
            sm_mapping = {'submodule_path': path, 'submodule_info': info_fmt}
            filled_sm_template = SINGLE_SUBMODULE.safe_substitute(sm_mapping)
            filled_submodule_templates.append(filled_sm_template)
        return '\n'.join(filled_submodule_templates)

    def display(self):
        if self.outfile is not None:
            # either write the output to a file...
            self.outfile.write_text(self.full_template)
            confirm_msg = f"GitTracker: output written to file at {self.outfile}"
            confirm_msg = self.apply_style(value=confirm_msg, style='green')
            print(confirm_msg)
        else:
            # ...or print it to the screen
            clear_display()
            print(self.full_template)
