from .ascii import LOGO
from .templates import (
    ANSI_SEQS,
    OUTER_TEMPLATE,
    REPO_TEMPLATES,
    SINGLE_CHANGE_STATE,
    SINGLE_FILE_CHANGE
)
from ..util.util import get_display_width

class Displayer:
    def __init__(self, repos, verbosity):
        """
        Class that handles formatting and displaying information
        for tracked repositories according to the given
        `verbosity` level
        :param repos: dict
                dictionaries of {path: changes} for each repository.
                `changes` typically contains "git-status"-like
                information. See `gittracker.tracker.tracker` for
                further details
        :param verbosity: int {0, 1, 2}
                verbosity level of output (0 is least verbose)
        """
        self.repos = repos
        self.verbosity = verbosity
        self.n_repos = len(self.repos)
        self.outer_template = OUTER_TEMPLATE
        self.repo_template = REPO_TEMPLATES[self.verbosity]
        self.ansi_seqs = ANSI_SEQS
        self.logo = LOGO
        self.display_width = get_display_width()

        if self.verbosity == 0:
            self.format_func = self._format_v0
        elif self.verbosity == 1:
            self.format_func = self._format_v1
        else:
            self.format_func = self._format_v2

        # completed outer template to display
        self.full_template = None
        # stores list of filled single-repo templates
        self.full_repo_templates = None
        # stores filled `SINGLE_CHANGE_STATE` templates if self.verbosity == 2
        self.full_state_templates = None
        # stores filled `SINGLE_FILE_CHANGE` templates if self.verbosity == 2
        self.full_file_templates = None


    def format_display(self):
        # fill individual repo templates
        full_repo_templates, n_good, n_bad = self.format_func()
        n_total = n_good + n_bad
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
            'n_repos_tracked': self.format_value_text(value=n_total, style='bold'),
            'summary_msg': summary_msg_fmt,
            'line_sep': '=' * get_display_width(),
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
        reset_code = "\033[0m"
        if style is None:
            ansi_val = 0
        elif isinstance(style, str):
            ansi_val = self.ansi_seqs[style]
        else:
            ansi_val = ";".join((self.ansi_seqs[s] for s in style))

        style_code = f"\033[{ansi_val}m"
        return f"{style_code}{value}{reset_code}"

    def _format_v0(self):
        filled_repo_templates = []


        for repo in self.repos:



        # formatting function for verbosity level 0
        pass

    def _format_v1(self):
        # formatting function for verbosity level 1
        pass

    def _format_v2(self):
        # formatting function for verbosity level 2
        pass

    def display(self):
        # print the full output to the screen
        print(self.filled_template)





# # change_codes = {
# #     'A': 'new file',
# #     'D': 'deleted',
# #     'R': 'renamed',
# #
# # }