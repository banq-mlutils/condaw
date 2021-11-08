#!/usr/bin/env python
"""
the condaw command line utility
its like gradlew, but for conda!
"""

import os.path
import sys

from condaw.file_constants import CONDAW_FOLDER
from condaw.logging import verbose
from condaw.prep_install import prepare_conda_installation
from condaw.run_task import run_task
from condaw.setup_environment import setup_conda_environment


# global configs #


def setup_condaw_folder():
    """
    make sure CONDAW_FOLDER exists
    """
    if not os.path.exists(CONDAW_FOLDER):
        os.mkdir(CONDAW_FOLDER)


def main():
    setup_condaw_folder()
    conda_folder = prepare_conda_installation()
    env_name = setup_conda_environment(project_folder=os.getcwd(), conda_folder=conda_folder)
    run_task(env_name=env_name, conda_folder=conda_folder, arguments=sys.argv[1:])


if __name__ == '__main__':
    verbose = 1
    main()
