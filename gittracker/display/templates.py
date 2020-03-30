from string import Template


# wrapper template for full output. Applies to all verbosity levels
OUTER_TEMPLATE = Template(
"""\
${pkg_ascii_logo}: 
${n_repos_tracked} tracked repositories: ${repo_summary_msg}
${line_sep}
${repos_status}\
"""
)

# single-repository template: verbosity level 0
SINGLE_REPO_V0 = Template("${repo_name}")

# single-repository template: verbosity level 1
SINGLE_REPO_V1 = Template(
"""\
${repo_name}
    ${repo_path}
    on branch ${local_branch}: ${compared_to_remote} ${remote_branch}
    ${n_uncommitted}\
"""
)

# single-repository template: verbosity level 2
# this one has to be constructed somewhat indirectly in order to accommodate
# different possible states of the repository (e.g., presence or lack of
# staged/unstaged changes). `file_states` gets filled by instances of
# `SINGLE_CHANGE_STATE` (if any)
SINGLE_REPO_V2 = Template(
"""\
${repo_name}
    ${repo_path}
    on branch ${local_branch}: ${compared_to_remote} ${remote_branch}
    ${file_states}
"""
)

# format skeleton for a single change state (e.g., staged, not staged,
# untracked) in verbosity level 2. `changed_files` gets filled by instances
# of `SINGLE_FILE_CHANGE`
SINGLE_CHANGE_STATE = Template(
"""\
${n_changed} ${change_state_msg}:
    ${changed_files}\
"""
)

# format skeleton for a single modified file in verbosity level 2
SINGLE_FILE_CHANGE = Template("${change_type}: ${filepath}")

# mapping of single repository templates by verbosity value
REPO_TEMPLATES = {
    0: SINGLE_REPO_V0,
    1: SINGLE_REPO_V1,
    2: SINGLE_REPO_V2
}

# numeric codes from ANSI escape sequences for text color/formatting
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
    'white': 37,
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