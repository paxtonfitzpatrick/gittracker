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
        else:
            self.repo_template = SINGLE_REPO_COMPLEX
            self.repo_format_func = self._format_complex

        # holds completed outer template to display
        self.full_template = None
        # skip formatting if plain style was requested or writing to file
        self._dont_apply_style = self.plain or self.outfile is not None

    @property
    def display_width(self):
        return get_terminal_size().columns

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

    def _format_simple(self, repo_info):
        # repo_info is a tuple of (key, value) from self.repos
        repo_path, status = repo_info
        repo_name = basename(repo_path)
        if any(status[k] for k in ('is_detached', 'n_commits_ahead',
                                   'n_commits_behind', 'n_staged',
                                   'n_not_staged', 'n_untracked')):
            is_clean = False
            style = 'red'
        else:
            is_clean = True
            style = 'green'
        repo_name_fmt = self.apply_style(repo_name, style=style)
        template_mapping = {'repo_name': repo_name_fmt}
        filled_template = self.repo_template.safe_substitute(template_mapping)
        return filled_template, is_clean

    def _format_complex(self, repo_info):
        # repo_info is a tuple of (key, value) from self.repos
        repo_path, status = repo_info
        repo_name = basename(repo_path)
        if status['is_detached']:
            branch_info = self._format_branch_detached(status)
        else:
            branch_info = self._format_branch_standard(status)

    def _format_branch_detached(self, repo_status):
        mapping = dict()
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

        mapping['detached_at'] = self.apply_style(sha_msg, 'red')
        mapping['from_branch'] = self.apply_style(from_branch, 'bold')
        mapping['new_commits'] = new_commits
        full_branch_template = BRANCH_INFO_DETACHED.safe_substitute(mapping)
        return full_branch_template








    def _format_v2(self):
        # formatting function if self.verbose == 2
        full_repo_templates = []
        n_good = 0
        n_bad = 0
        for repo_path, repo_status in self.repos.items():
            template_mapping = dict()
            template_mapping['repo_path'] = repo_path
            if isinstance(repo_status, str):
                # HEAD is detached, use alternate template...
                template = SINGLE_REPO_DETACHED
                template_mapping['detached_head_msg'] = self.apply_style(
                    value=repo_status,
                    style='red'
                )
                name_color = 'red'
                n_bad += 1
            else:
                # ...otherwise, use standard template and get further info
                template = self.repo_template
                template_mapping['local_branch'] = self.apply_style(
                    repo_status['local_branch'],
                    style='bold'
                )
                template_mapping['remote_branch'] = self.apply_style(
                    repo_status['remote_branch'],
                    style='bold'
                )
                n_ahead = repo_status['n_commits_ahead']
                n_behind = repo_status['n_commits_behind']
                n_ahead_fmt = self.apply_style(value=n_ahead, style='bold')
                n_behind_fmt = self.apply_style(value=n_behind, style='bold')

                if n_ahead is n_behind is None:
                    # local repository isn't tracking a remote
                    compare_msg = ''
                    good_vs_remote = True
                elif n_ahead == n_behind == 0:
                    # local branch is even with remote tracking branch
                    compare_msg = 'even with'
                    good_vs_remote = True
                elif n_ahead > 0 and n_behind > 0:
                    # local branch is some commits ahead, some behind
                    compare_msg = f"{n_behind_fmt} commits behind, " \
                                  f"{n_ahead_fmt} ahead of"
                    good_vs_remote = False
                elif n_ahead > 0:
                    # local branch is ahead of remote, but not behind
                    compare_msg = f"{n_ahead_fmt} commits ahead of"
                    good_vs_remote = False
                else:
                    # local branch behind remote, but not ahead
                    assert n_behind > 0
                    compare_msg = f"{n_behind_fmt} commits behind"
                    good_vs_remote = False

                if len(compare_msg) > 0:
                    template_mapping['local_branch'] += ':'

                template_mapping['compared_to_remote'] = compare_msg
                n_uncommitted = (
                        repo_status['n_staged']
                        + repo_status['n_not_staged']
                        + repo_status['n_untracked']
                )

                uncommitted_color = 'green' if n_uncommitted == 0 else 'red'
                if good_vs_remote and n_uncommitted == 0:
                    name_color = 'green'
                    n_good += 1
                else:
                    name_color = 'red'
                    n_bad += 1

                template_mapping['n_uncommitted'] = self.apply_style(
                    value=n_uncommitted,
                    style=('bold', uncommitted_color)
                )

            template_mapping['repo_name'] = self.apply_style(
                value=basename(repo_path),
                style=('bold', name_color)
            )
            full_repo_template = template.safe_substitute(template_mapping)
            full_repo_templates.append(full_repo_template)
        return full_repo_templates, n_good, n_bad

    def _format_v3(self):
        # TODO: this is a lot of redundant code with _format_v2... refactor
        # formatting function if self.verbose == 3
        full_repo_templates = []
        n_good = 0
        n_bad = 0
        for repo_path, repo_status in self.repos.items():
            template_mapping = dict()
            template_mapping['repo_path'] = repo_path
            # default to color for local even with remote -- it may get
            # changed under various conditions below
            name_color = 'green'
            if isinstance(repo_status, str):
                # HEAD is detached, use alternate template...
                template = SINGLE_REPO_DETACHED
                template_mapping['detached_head_msg'] = self.apply_style(
                    value=repo_status,
                    style='red'
                )
                template_mapping['change_states'] = ''
                name_color = 'red'
                n_bad += 1
            else:
                # ...otherwise, use standard template and get further info
                template = self.repo_template
                template_mapping['local_branch'] = self.apply_style(
                    repo_status['local_branch'],
                    style='bold'
                )
                template_mapping['remote_branch'] = self.apply_style(
                    repo_status['remote_branch'],
                    style='bold'
                )
                n_ahead = repo_status['n_commits_ahead']
                n_behind = repo_status['n_commits_behind']
                n_ahead_fmt = self.apply_style(value=n_ahead, style='bold')
                n_behind_fmt = self.apply_style(value=n_behind, style='bold')

                if n_ahead is n_behind is None:
                    # local repository isn't tracking a remote
                    compare_msg = ''
                    good_vs_remote = True
                elif n_ahead == n_behind == 0:
                    # local branch is even with remote tracking branch
                    compare_msg = 'even with'
                    good_vs_remote = True
                elif n_ahead > 0 and n_behind > 0:
                    # local branch is some commits ahead, some behind
                    compare_msg = f"{n_behind_fmt} commits behind, " \
                                  f"{n_ahead_fmt} ahead of"
                    good_vs_remote = False
                    name_color = 'red'
                elif n_ahead > 0:
                    # local branch is ahead of remote, but not behind
                    compare_msg = f"{n_ahead_fmt} commits ahead of"
                    good_vs_remote = False
                    name_color = 'red'
                else:
                    # local branch behind remote, but not ahead
                    assert n_behind > 0
                    compare_msg = f"{n_behind_fmt} commits behind"
                    good_vs_remote = False
                    name_color = 'red'
                if len(compare_msg) > 0:
                    template_mapping['local_branch'] += ':'

                template_mapping['compared_to_remote'] = compare_msg
                full_state_templates = []
                state_change_msgs = {
                    'staged': 'files staged for commit',
                    'not_staged': 'files not staged for commit',
                    'untracked': 'untracked files'
                }
                for state, style in zip(
                        ['staged', 'not_staged', 'untracked'],
                        ['green', 'red', 'red']
                ):
                    if repo_status[f"n_{state}"] > 0:
                        name_color = 'red'
                        msg = state_change_msgs[state]
                        if repo_status[f"n_{state}"] == 1:
                             msg = msg.replace('files', 'file')
                        state_template = SINGLE_CHANGE_STATE
                        state_mapping = dict()
                        state_mapping['n_changed'] = repo_status[f'n_{state}']
                        state_mapping['change_state_msg'] = msg
                        changed_files = []
                        for file in repo_status[f'files_{state}']:
                            file_template = SINGLE_FILE_CHANGE
                            file_template_mapping = dict()

                            if state == 'staged':
                                change_code, a_path, b_path = file
                            elif state == 'not_staged':
                                change_code, a_path = file
                                # dummy values
                                b_path = None
                            else:
                                # remaining condition is state == 'untracked'
                                a_path = file
                                # dummy values
                                change_code, b_path = None, None

                            if change_code == 'R':
                                fpath = f"{a_path} -> {b_path}"
                                change_type = 'renamed:'
                            elif change_code == 'D':
                                fpath = a_path
                                # intentional leading space for horizonal alignment
                                change_type = ' deleted'
                            elif change_code == 'M':
                                fpath = a_path
                                change_type = 'modified'
                            else:
                                fpath = a_path
                                change_type = 'new file'

                            file_template_mapping['change_type'] = self.apply_style(
                                value=change_type,
                                style=style
                            )
                            file_template_mapping['filepath'] = self.apply_style(
                                value=fpath,
                                style=style
                            )
                            f_t = file_template.safe_substitute(file_template_mapping)
                            changed_files.append(f_t)

                        state_mapping['changed_files'] = '\n\t'.join(changed_files)
                        full_state_template = state_template.safe_substitute(
                            state_mapping
                        )
                        full_state_templates.append(full_state_template)

                repo_submodules = repo_status['submodules']
                if repo_submodules is not None:
                    full_sm_templates, submodules_clean = self._format_submodules(
                        repo_submodules
                    )
                    full_state_templates.append("submodules:")
                    full_state_templates.append('\n'.join(full_sm_templates))
                    if not submodules_clean:
                        good_vs_remote = False

                template_mapping['change_states'] = '\n    '.join(
                    full_state_templates
                )
                if name_color == 'green' and good_vs_remote:
                    n_good += 1
                else:
                    n_bad += 1
            template_mapping['repo_name'] = self.apply_style(
                value=basename(repo_path),
                style=('bold', name_color)
            )
            full_repo_template = template.safe_substitute(template_mapping)
            full_repo_templates.append(full_repo_template)
        return full_repo_templates, n_good, n_bad

    def _format_submodules(self, submodules):
        full_sm_templates = []
        sm_template = SINGLE_SUBMODULE
        all_good = True
        for sm_path, sm_status in submodules.items():
            sm_template_mapping = {'submodule_path': sm_path}
            # format should be (standard info, alternate info)
            assert isinstance(sm_status, tuple) and len(sm_status) == 2
            sm_dict, sm_msg = sm_status
            if isinstance(sm_msg, str):
                if sm_msg.startswith('HEAD'):
                    # submodule is in a detatched HEAD state
                    sm_info = self.apply_style(value=sm_msg, style='red')
                    all_good = False
                else:
                    # submodule is not initialized
                    sm_info = sm_msg

            elif sm_dict is None:
                # everything is up-to-date
                sm_info = self.apply_style(
                    value="working tree is clean",
                    style='green'
                )
            else:
                # sm_dict is a dict of all None's; working tree is dirty
                sm_info = self.apply_style(
                    value="working tree is dirty",
                    style='red'
                )
                all_good = False

            sm_template_mapping['submodule_info'] = sm_info
            full_sm_template = sm_template.safe_substitute(sm_template_mapping)
            full_sm_templates.append(full_sm_template)

        return full_sm_templates, all_good

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

