from os.path import basename
from shutil import get_terminal_size
from .ascii import RANDOM_LOGO
from .templates import (
    ANSI_SEQS,
    OUTER_TEMPLATE,
    REPO_TEMPLATES,
    SINGLE_CHANGE_STATE,
    SINGLE_FILE_CHANGE,
    SINGLE_REPO_DETACHED
)
from ..utils.utils import clear_display


class Displayer:
    def __init__(self, repos, verbose=1, outfile=None, plain=False):
        """
        Class that handles formatting and displaying information
        for tracked repositories according to the given
        `verbose` level
        :param repos: dict
                dictionaries of {path: changes} for each repository.
                `changes` typically contains "git-status"-like
                information. See `gittracker.tracker.tracker` for
                further details
        :param verbose: int {0, 1, 2} (default: 1)
                verbosity level of output (0 is least verbose)
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
        self.n_repos = len(self.repos)
        self.outer_template = OUTER_TEMPLATE
        self.repo_template = REPO_TEMPLATES[self.verbose]
        self.ansi_seqs = ANSI_SEQS
        self.logo = RANDOM_LOGO

        if self.verbose == 0:
            self.repo_format_func = self._format_v0
        elif self.verbose == 1:
            self.repo_format_func = self._format_v1
        else:
            self.repo_format_func = self._format_v2

        # completed outer template to display
        self.full_template = None
        # stores list of filled single-repo templates
        self.full_repo_templates = None
        # stores filled `SINGLE_CHANGE_STATE` templates if self.verbose == 2
        self.full_state_templates = None
        # stores filled `SINGLE_FILE_CHANGE` templates if self.verbose == 2
        self.full_file_templates = None

    @property
    def display_width(self):
        return get_terminal_size().columns

    def format_display(self):
        # fill individual repo templates
        full_repo_templates, n_good, n_bad = self.repo_format_func()
        n_total = n_good + n_bad
        n_total_fmt = self.format_value_text(
            value=n_total,
            style='bold'
        )
        # handle two (probably rare) cases
        if n_bad == 0:
            # if no repos have unpushed changes, report them as "all" up-to-date
            # and color the full message green
            summary_msg = "all up-to-date"
            summary_msg_fmt = self.format_value_text(
                value=summary_msg,
                style='green'
            )
        elif n_good == 0:
            # or, if all repos have unpushed changes, report them as "all"
            # having unpushed changes and color the full message red
            summary_msg = "all with unpushed changes"
            summary_msg_fmt = self.format_value_text(
                value=summary_msg,
                style='red'
            )
        # standard case: if there's a mix, don't color the whole message, and
        # color the good/bad counts separately
        else:
            n_good_fmt = self.format_value_text(
                value=n_good,
                style=('bold', 'green')
            )
            n_bad_fmt = self.format_value_text(
                value=n_bad,
                style=('bold', 'red')
            )
            summary_msg_fmt = f"{n_good_fmt} up-to-date, {n_bad_fmt} with " \
                              "unpushed changes"
        # mapping for self.outer_template
        template_mapping = {
            'pkg_ascii_logo': self.logo,
            'n_repos_tracked': n_total_fmt,
            'summary_msg': summary_msg_fmt,
            'line_sep': '=' * self.display_width,
            'repos_status': '\n'.join(full_repo_templates)
        }
        self.full_template = self.outer_template.safe_substitute(template_mapping)

    def format_value_text(self, value, style=None):
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
        if self.outfile is not None or self.plain:
            # skip formatting if not writing to stdout
            # or non-stylized output was requested
            return value

        reset_code = "\033[0m"
        if style is None:
            ansi_val = 0
        elif isinstance(style, str):
            ansi_val = self.ansi_seqs[style]
        else:
            ansi_val = ";".join((str(self.ansi_seqs[s]) for s in style))

        style_code = f"\033[{ansi_val}m"
        return f"{style_code}{value}{reset_code}"

    def _format_v0(self):
        # repo status formatting function called if self.verbose == 0
        full_repo_templates = []
        n_good = 0
        n_bad = 0
        for repo_path, repo_status in self.repos.items():
            repo_name = basename(repo_path)
            if isinstance(repo_status, (str, dict)):
                # if the HEAD is either dirty or detached
                style = 'red'
                n_bad += 1
            else:
                style = 'green'
                n_good += 1
            repo_name_fmt = self.format_value_text(value=repo_name, style=style)
            template_mapping = {'repo_name': repo_name_fmt}
            full_repo_template = self.repo_template.safe_substitute(template_mapping)
            full_repo_templates.append(full_repo_template)
        return full_repo_templates, n_good, n_bad

    def _format_v1(self):
        # formatting function for verbose level 1
        full_repo_templates = []
        n_good = 0
        n_bad = 0
        for repo_path, repo_status in self.repos.items():
            template_mapping = dict()
            template_mapping['repo_path'] = repo_path
            if isinstance(repo_status, str):
                # HEAD is detached, use alternate template...
                template = SINGLE_REPO_DETACHED
                template_mapping['detached_head_msg'] = self.format_value_text(
                    value=repo_status,
                    style='red'
                )
                name_color = 'red'
                n_bad += 1
            else:
                # ...otherwise, use standard template and get further info
                template = self.repo_template
                template_mapping['local_branch'] = self.format_value_text(
                    repo_status['local_branch'],
                    style='bold'
                )
                template_mapping['remote_branch'] = self.format_value_text(
                    repo_status['remote_branch'],
                    style='bold'
                )
                n_ahead = repo_status['n_commits_ahead']
                n_behind = repo_status['n_commits_behind']
                n_ahead_fmt = self.format_value_text(value=n_ahead, style='bold')
                n_behind_fmt = self.format_value_text(value=n_behind, style='bold')

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

                template_mapping['n_uncommitted'] = self.format_value_text(
                    value=n_uncommitted,
                    style=('bold', uncommitted_color)
                )

            template_mapping['repo_name'] = self.format_value_text(
                value=basename(repo_path),
                style=('bold', name_color)
            )
            full_repo_template = template.safe_substitute(template_mapping)
            full_repo_templates.append(full_repo_template)
        return full_repo_templates, n_good, n_bad

    def _format_v2(self):
        # TODO: this is a lot of redundant code with _format_v1... refactor pls
        # formatting function for verbose level 2
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
                template_mapping['detached_head_msg'] = self.format_value_text(
                    value=repo_status,
                    style='red'
                )
                template_mapping['change_states'] = ''
                name_color = 'red'
            else:
                # ...otherwise, use standard template and get further info
                template = self.repo_template
                template_mapping['local_branch'] = self.format_value_text(
                    repo_status['local_branch'],
                    style='bold'
                )
                template_mapping['remote_branch'] = self.format_value_text(
                    repo_status['remote_branch'],
                    style='bold'
                )
                n_ahead = repo_status['n_commits_ahead']
                n_behind = repo_status['n_commits_behind']
                n_ahead_fmt = self.format_value_text(value=n_ahead, style='bold')
                n_behind_fmt = self.format_value_text(value=n_behind, style='bold')

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
                                change_type = 'deleted'
                            elif change_code == 'm':
                                fpath = a_path
                                change_type = 'modified'
                            else:
                                fpath = a_path
                                change_type = 'new file'

                            file_template_mapping['change_type'] = self.format_value_text(
                                value=change_type,
                                style=style
                            )
                            file_template_mapping['filepath'] = self.format_value_text(
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
                        template_mapping['change_states'] = '\n    '.join(
                            full_state_templates
                        )

            if name_color == 'green':
                template_mapping['change_states'] = ''
                n_good += 1
            else:
                n_bad += 1
            template_mapping['repo_name'] = self.format_value_text(
                value=basename(repo_path),
                style=('bold', name_color)
            )
            full_repo_template = template.safe_substitute(template_mapping)
            full_repo_templates.append(full_repo_template)
        return full_repo_templates, n_good, n_bad

    def display(self):
        if self.outfile is not None:
            # either write the output to a file...
            self.outfile.write_text(self.full_template)
            confirm_msg = f"GitTracker: output written to file at {self.outfile}"
            confirm_msg = self.format_value_text(value=confirm_msg, style='green')
            print(confirm_msg)
        else:
            clear_display()
            # ...or print it to the screen
            print(self.full_template)

