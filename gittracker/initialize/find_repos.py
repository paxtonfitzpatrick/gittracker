import os


def find_repos(toplevel_dir, ignore_dirs=None, include_submodules=False):
    repos = []

    for dirpath,