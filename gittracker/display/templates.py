from string import Template


# Wrapper template for full output. Applies to all verbosity levels
# =======================================================================
OUTER_TEMPLATE = Template(
"""\
${pkg_ascii_logo}
${n_repos_tracked} tracked repositories: ${summary_msg}
${line_sep}
${repos_status}\
"""
)


# Single-repository template: verbosity level 1
# =======================================================================
#   only information shown is the repository's name.  The name is
#   colored green if:
#       1) the working tree is clean
#       2) the active branch is not detached, AND
#       3) the active branch is either up to date with its remote
#          tracking branch or doesn't have one
#   otherwise, it appears in red
SINGLE_REPO_V1 = Template("${repo_name}")


# Single-repository template: verbosity level 2
# =======================================================================
# Default output format; shows more detailed (but not extensive) info:
#   - repo_name: repository name (colored by the same rules as above)
#   - repo_path: absolute path to the repository
#   - branch_info: filled by either BRANCH_INFO or BRANCH_INFO_DETACHED,
#     depending on the state of the branch
#   - n_uncommitted: the total number of uncommitted changes, including
#     staged, unstaged, and untracked files
SINGLE_REPO_V2 = Template(
"""\
${repo_name}
    ${repo_path}
    ${branch_info}
    ${n_uncommitted} uncommitted changes\
"""
)


# Single-repository template: verbosity level 3
# =======================================================================
# Verbose output format; shows full information given by the `git-status`
# command for each tracked repository
#   - repo_name: repository name (colored by the same rules as above)
#   - repo_path: absolute path to the repository
#   - branch_info: filled by either BRANCH_INFO or BRANCH_INFO_DETACHED,
#     depending on the state of the branch
#   - change_states: filled by up to 3 instances of SINGLE_CHANGE_STATE,
#   corresponding to staged, unstaged, and untracked files (if any)
SINGLE_REPO_V3 = Template(
"""\
${repo_name}
    ${repo_path}
    ${branch_info}
    ${change_states}
"""
)


BRANCH_INFO = Template(
"""\
on branch: ${local_branch} ${compared_to_remote} ${remote_branch}
"""
)


BRANCH_INFO_DETACHED = Template(
"""\
${detached_at} (from branch: ${ref_branch}${ref_sha}) ${new_commits}\
"""
)

# format skeleton for a single change state (e.g., staged, not staged,
# untracked) in verbosity level 3. `changed_files` gets filled by instances
# of `SINGLE_FILE_CHANGE`
SINGLE_CHANGE_STATE = Template(
"""\
${n_changed} ${change_state_msg}:
        ${changed_files}\
"""
)

# format skeleton for a single modified file in verbosity level 3
SINGLE_FILE_CHANGE = Template("${change_type}:   ${filepath}")

# replacement skeleton for repositories in detached HEAD states for verbosity
# levels 2 & 3
SINGLE_REPO_DETACHED = Template(
"""\
${repo_name}
    ${repo_path}
    ${detached_head_msg}
"""
)

# format skeleton for submodules
# (analogous to SINGLE_REPO_V2 template; only used with SINGLE_REPO_V3)
SINGLE_SUBMODULE = Template(
"""\
\t${submodule_path}: ${submodule_info}\
"""
)

# mapping of single repository templates by verbosity value
REPO_TEMPLATES = {
    1: SINGLE_REPO_V1,
    2: SINGLE_REPO_V2,
    3: SINGLE_REPO_V3
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