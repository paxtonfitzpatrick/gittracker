#!/usr/bin/env python3

def gittracker("kwargs here"):
    # if logfile of expected locations exists,
        #  load it in
    # else
        # prompt user to run manually input paths and run now
        #  or run auto-initialization and quit after it's done

    # check that locations exist -- _check_repos_exist
    # get changes for each
    # format them for display in terminal window
    pass


def _check_repos_exist(repo_paths):
    """
    Quick check to make sure provided `repo_paths` A) are
    directories (i.e., a directory exists at each path)
    and B) are git repositories (i.e., a `.git` directory
    exists in each directory).  If a repository doesn't
    exist at an expected path, prompts the user with a number
    of options, potentially updating the logfile of known
    repository locations.
    :param repo_paths: list (length: number-of-repositories)
            (absolute) paths to expected repository locations
    :return: good_paths: list
            (absolute) paths to confirmed repository locations,
            potentially with changes to or deletions of items in
            `repo paths`
    """
    pass





if __name__ == "__main__":
    # argparse stuff...
    gittracker("kwargs here")
