"""
hold logic for preparing conda installation
"""
import os
import re
import subprocess

from condaw import verbose
from condaw.file_constants import path_to_conda, CONDAW_LOCAL_CONDA_BINARY, CONDAW_LOCAL_INSTALLER_PATH, \
    CONDAW_LOCAL_INSTALLER_URL, CONDAW_LOCAL_INSTALL_ARGS, CONDAW_LOCAL_CONDA_FOLDER
from condaw.utils import print_verbose, download_from_url


def prepare_conda_installation():
    """
    try to find a conda environment, and install one if not found
    :rtype: str
    :return: path to conda installation folder
    """
    folder = detect_system_conda()
    if folder:
        print_verbose("system conda found")
    else:
        print_verbose("system conda not found, trying local conda")
        folder = setup_local_conda()

    print("using conda at", folder)
    if verbose:
        print("details:")
        result = subprocess.run([path_to_conda(folder), "info"], capture_output=True, text=True)
        print(result.stdout)

    return folder


def detect_system_conda():
    """
    try to find system conda
    returns path to the folder if exists, None if not
    :rtype: str | None
    """
    try:
        result = subprocess.run(["conda", "info"], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        result = None  # this will happen on windows if you don't have conda in PATH

    if result is not None and result.returncode == 0:
        match = re.findall(r"base environment : (?P<folder>.*)", result.stdout)
        assert len(match) == 1, "only expecting one base environment from conda info, got " + str(len(match)) + "!"
        folder = match[0]
        # get rid of the (writable)
        if folder.endswith("(writable)"):
            folder = folder[:-len("(writable)")].strip()
        return folder
    else:
        return None


def setup_local_conda():
    """
    try to use local conda, install one if not found
    returns path to the folder
    :rtype: str
    """
    if not os.path.exists(CONDAW_LOCAL_CONDA_BINARY):
        print("local conda unavailable, installing one")

        if os.path.exists(CONDAW_LOCAL_INSTALLER_PATH):
            os.remove(CONDAW_LOCAL_INSTALLER_PATH)
        download_from_url(CONDAW_LOCAL_INSTALLER_URL, CONDAW_LOCAL_INSTALLER_PATH)

        args = list(CONDAW_LOCAL_INSTALL_ARGS)
        args.insert(CONDAW_LOCAL_INSTALLER_PATH, 0)
        subprocess.run(
            args,
            capture_output=True, text=True, check=True
        )

        if os.path.exists(CONDAW_LOCAL_CONDA_BINARY):
            print("successfully installed local conda")
    else:
        print_verbose("local conda found")

    return CONDAW_LOCAL_CONDA_FOLDER