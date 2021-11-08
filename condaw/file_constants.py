"""
hold all the constant for files
"""
import os

CONDAW_FOLDER = os.path.join(os.getcwd(), ".condaw")

CONDAW_FI_HASH_FILE = os.path.join(CONDAW_FOLDER, ".hashes.json")

if os.name == "nt":
    CONDAW_TRAMPOLINE_SCRIPT_FILE = os.path.join(CONDAW_FOLDER, "trampoline.bat")
else:
    CONDAW_TRAMPOLINE_SCRIPT_FILE = os.path.join(CONDAW_FOLDER, "trampoline.sh")

if os.name == "nt":
    # this is for easier usage with WSL
    CONDAW_LOCAL_CONDA_FOLDER = os.path.join(CONDAW_FOLDER, "conda-win")
    CONDAW_LOCAL_INSTALLER_URL = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    CONDAW_LOCAL_INSTALLER_PATH = os.path.join(CONDAW_FOLDER, "Miniconda3-latest-Windows-x86_64.exe")
    CONDAW_LOCAL_INSTALL_ARGS = (
        "/InstallationType=JustMe",
        "/AddToPath=0",
        "/S",
        "/D=" + os.path.abspath(CONDAW_LOCAL_CONDA_FOLDER)
    )
else:
    CONDAW_LOCAL_CONDA_FOLDER = os.path.join(CONDAW_FOLDER, "conda-linux")
    CONDAW_LOCAL_INSTALLER_URL = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    CONDAW_LOCAL_INSTALLER_PATH = os.path.join(CONDAW_FOLDER, "Miniconda3-latest-Linux-x86_64.sh")
    CONDAW_LOCAL_INSTALL_ARGS = (
        "-b",
        "-p", os.path.abspath(CONDAW_LOCAL_CONDA_FOLDER)
    )


def path_to_conda(conda_folder):
    if os.name == "nt":
        return os.path.join(conda_folder, "Scripts", "conda.exe")
    else:
        return os.path.join(conda_folder, "bin", "conda")


def path_to_activate(conda_folder):
    if os.name == "nt":
        return os.path.join(conda_folder, "Scripts", "activate.bat")
    else:
        return os.path.join(conda_folder, "bin", "activate")


def path_to_python(conda_folder):
    if os.name == "nt":
        return os.path.join(conda_folder, "python.exe")
    else:
        return os.path.join(conda_folder, "bin", "python")


CONDAW_LOCAL_CONDA_BINARY = path_to_conda(CONDAW_LOCAL_CONDA_FOLDER)
CONDAW_LOCAL_PYTHON_BINARY = path_to_python(CONDAW_LOCAL_CONDA_FOLDER)