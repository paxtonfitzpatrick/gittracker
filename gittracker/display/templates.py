from string import Template


# Wrapper template for full output; applied at all verbosity levels:
#   -
# =======================================================================
OUTER_TEMPLATE = Template(
"""\
${ascii_logo}
${n_repos_tracked} tracked repositories: ${summary_msg}
${line_sep}
${repos_status}\
"""
)


# Single-repository template: verbosity level 1
# =======================================================================
# Only information shown is the repository's name. The name appears in
# green if 3 conditions are (all) met:
#       1) the working tree is clean
#       2) the active branch is not detached, AND
#       3) the active branch is either up to date with its remote
#          tracking branch or doesn't have one
#   otherwise, it appears in red
SINGLE_REPO_SIMPLE = Template("${repo_name}")


# Single-repository template: verbosity levels 2 & 3
# =======================================================================
# Shows more detailed info; wraps formatting for verbosity levels 2 & 3:
#   - repo_name: repository name (colored by the same rules as above)
#   - repo_path: absolute path to the repository
#   - branch_info: filled by either BRANCH_INFO or BRANCH_INFO_DETACHED,
#     depending on the state of the branch
#   - local_changes: filled by LOCAL_CHANGES_V2 at verbosity level 2 or
#     0-3 instances of SINGLE_CHANGE_STATE templates at verbosity level 3.
#     Can also contain instances of SINGLE_SUBMODULE template (see below)
SINGLE_REPO_COMPLEX = Template(
"""\
${repo_name}
    ${repo_path}
    ${branch_info}
    ${local_changes}\
"""
)


# =========================SUB-TEMPLATES=================================
# fills `branch_info` fields for SINGLE_REPO_COMPLEX in normal case
#   - local_branch: the current local branch
#   - vs_remote: string comparing the local branch to its remote tracking
#     branch (if it has one)
#   - remote_branch: the current local branch's remote tracking branch
#     (if it has one)
BRANCH_INFO_STANDARD = Template(
"""\
on branch ${local_branch} ${vs_remote} ${remote_branch}\
"""
)


# fills `branch_info` fields for SINGLE_REPO_COMPLEX if HEAD is detached
#   - detached_at: takes the form "HEAD detached at <curr_sha>" where
#     <curr_sha> is the *current* commit hash of the detached HEAD
#   - from_branch: the local branch from which the HEAD was detached. If
#     commits have been made on the detached HEAD, the format will be
#     "<local_branch>@<ref_sha>" where <ref_sha> is the commit hash where
#     HEAD was detached from <local_branch> (i.e., the last commit they
#     have in common)
#   - new_commits: if commits have been made on the detached HEAD, takes
#     the format "<n_commits> new commits since detached"
BRANCH_INFO_DETACHED = Template(
"""\
${detached_at} (from branch: ${from_branch}) ${new_commits}\
"""
)


# fills `local_changes` field at verbosity level 2:
#   - n_uncommitted: the total number of uncommitted changes, including
#     staged, tracked-but-not-staged, and untracked files
LOCAL_CHANGES_V2 = Template("${n_uncommitted} uncommitted changes")


# Describes a single "state" of a locally changed file (staged,
# tracked-but-not-staged, untracked); one or multiple instances fill
# `local_changes` field at verbosity level 3 (if any local changes):
#   - n_changed: the number of files in the given state
#   - change_state_msg: a descriptor for the given state
#   - changed_files: filled by instances of `SINGLE_FILE_CHANGE` templates
SINGLE_CHANGE_STATE = Template(
"""\
${n_changed} ${change_state_msg}:
        ${changed_files}\
"""
)


# Describes change to a single file; instances fill the `changed_files`
# field of SINGLE_CHANGE_STATE template at verbosity level 3:
#   - change_type: "modified", "deleted", etc. as shown by Git
#   - filepath: path to the changed file (from the repository root)
SINGLE_FILE_CHANGE = Template("${change_type}:   ${filepath}")


# Describes change to a single submodule from a repository; only used at
# verbosity level 3 if --submodules flag is passed:
#   - submodule_path: path to the submodule (from the repository root)
#   - submodule_info: simple string describing status of submodule.
#     As applicable, one of:
#       + "working tree is clean"
#       + "working tree is dirty"
#       + "HEAD detached at <sha> where <sha> is current commit hash
#       + "not initialized" if the submodule has not been initialized
SINGLE_SUBMODULE = Template(
"""\
\t${submodule_path}: ${submodule_info}\
"""
)


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
