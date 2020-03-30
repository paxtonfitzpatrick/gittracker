from string import Template


# SINGLE_REPO_V0 = Template(
# # """\033[${repo_name_fmt}m${repo_name}\033[0m"""
# # )
# #
# # SINGLE_REPO_V1 = Template(
# # """\033[${repo_path_fmt}m${repo_name}\033[0m
# #     on branch ${local_branch_fmt}${local_branch}\033[0m: ${vs_remote_fmt}${n_commits_ahead} ${ahead_behind}\033[0m ${remote_branch}
# # """)

SINGLE_REPO_V0 = Template(
"${repo_name}"
)

SINGLE_REPO_V1 = Template(
"""\
${repo_name}
    ${repo_path}
    on branch ${local_branch}: ${compared_to_remote} ${remote_branch}
    ${n_uncommitted} 
"""
)

SINGLE_REPO_V2 = Template(
"""\
${repo_name}
    ${repo_path}
    on branch ${local_branch}: ${compared_to_remote} ${remote_branch}
    
    ${n_staged} staged files:
        ${files_staged}
        
    $
    
"""
)


class Displayer:
    def __init__(self, repos, verbosity):
        """
        Class that handles formatting and displaying information
        for tracked repositories according to the given
        `verbosity` level
        :param repos: list of dicts
                dictionaries of "git-status"-like information
                for each repository
        :param verbosity: int {0, 1, 2}
                verbosity level of output (0 is least verbose)
        """
        self.repos = repos
        self.verbosity = verbosity

    def format_text(self):
        pass

    def display(self):
        pass


ANSI_SEQS = {
    'reset_all': 0,
    # INTENSITY/BRIGHTNESS
    'bold': 1,
    # FOREGROUND
    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37
    # 'reset_fg': 39,
    # # BACKGROUND
    # 'black': 40,
    # 'red': 41,
    # 'green': 42,
    # 'yellow': 43,
    # 'blue': 44,
    # 'magenta': 45,
    # 'cyan': 46,
    # 'white': 47
    # 'reset_bg': 49,
}