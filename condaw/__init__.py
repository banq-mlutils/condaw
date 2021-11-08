#!/usr/bin/env python
"""
the condaw command line utility
its like gradlew, but for conda!
"""
import codecs
import hashlib
import json
import os.path
import re
import subprocess

# global constants #
import sys

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

# global configs #


verbose = False


# utils #


def print_verbose(*args):
    """
    print only in verbose
    """
    if verbose:
        print(*args)


def is_windows():
    """
    is this a windows machine?
    :rtype: bool
    """
    return os.name == "nt"


def download_from_url(url, path):
    """
    download a file into path
    :type url: str
    :type path: str
    """
    # try to import urlretrive, 2 & 3 compatible
    try:
        from urllib import urlretrive
    except ImportError:
        from urllib.request import urlretrieve

    # download the file
    # noinspection PyUnboundLocalVariable
    urlretrieve(url, path)


# main logic #


def setup_condaw_folder():
    """
    make sure CONDAW_FOLDER exists
    """
    if not os.path.exists(CONDAW_FOLDER):
        os.mkdir(CONDAW_FOLDER)


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

        subprocess.run(
            [CONDAW_LOCAL_INSTALLER_PATH, *CONDAW_LOCAL_INSTALL_ARGS],
            capture_output=True, text=True, check=True
        )

        if os.path.exists(CONDAW_LOCAL_CONDA_BINARY):
            print("successfully installed local conda")
    else:
        print_verbose("local conda found")

    return CONDAW_LOCAL_CONDA_FOLDER


def setup_conda_environment(project_folder, conda_folder):
    """
    setup conda environment
    :param project_folder: folder of the project
    :type project_folder: str
    :param conda_folder: file to conda
    :type conda_folder: str
    :return: name of the environment to activate into
    :rtype: str

    note on environment caching:
        since even there is nothing to update, conda install is still going to take a while to run
        we are saving the hash of the environment file(called file_hash),
            and conda install will be skipped if hash is not changed at all
        we are also saving the hash of conda list(called installed_hash)
            this is to prevent unexpected skipping when the hash file is accidentally copied to another machine
            (possibly by accidentally committing the hash file into repo)
    """
    # get yaml file
    yaml_path = detect_environment_yaml(project_folder)
    print_verbose("found yaml at", yaml_path)

    # give warning on requirements.txt
    requirements = detect_requirements_txt(project_folder)
    if requirements:
        print(
            "warning: found requirements.txt %s, but they are ignored as we are a conda tool(so far)"
            % str(requirements)
        )

    # get environment name
    env_name = get_environment_name_from_yaml(yaml_path)
    print_verbose("resolved environment name", env_name)

    # check should update
    if not environment_exists(conda_folder, env_name):
        print_verbose("could not find conda environment, running install")
        should_conda_install = True
    else:
        print_verbose("found conda environment, computing hash")
        file_hash = compute_file_hash(yaml_path)
        installed_hash = compute_installed_hash(conda_folder, env_name)
        fi_hash = file_hash, installed_hash

        if fi_hash == load_fi_hash():
            print_verbose("hash matched, skipping install")
            should_conda_install = False
        else:
            print_verbose("hash mismatch, running install")
            should_conda_install = True

    # run it
    if should_conda_install:
        extra_paths = [
            os.path.join(conda_folder, "Scripts"),
            os.path.join(conda_folder, "Library", "bin")
        ]
        environs = os.environ.copy()
        environs["PATH"] = environs["PATH"] + os.path.pathsep + os.path.pathsep.join(extra_paths)
        subprocess.run(
            [
                path_to_conda(conda_folder), "env", "update",
                "--name", env_name,
                "--file", yaml_path,
                "--prune"
            ],
            env=environs
        )

        file_hash = compute_file_hash(yaml_path)
        installed_hash = compute_installed_hash(conda_folder, env_name)
        store_fi_hash(file_hash, installed_hash)

    return env_name


def detect_environment_yaml(folder):
    """
    detect environment.yaml from current folder
    :raises ValueError: if file not exists or multiple is found
    :rtype: str
    :return: path to the yaml
    """
    files = os.listdir(folder)

    # support .yaml or .yml
    selected = [f for f in files if re.match("environment.ya?ml", f)]

    if len(selected) == 0:
        raise ValueError("could not find environment.yaml in folder!")
    elif len(selected) > 1:
        raise ValueError("found more than one environment.yaml! found: %s" % (str(selected)))
    else:
        return os.path.join(folder, selected[0])


def detect_requirements_txt(folder):
    """
    detect requirements.txt from current folder
    :rtype: List[str]
    :return: path tot the requirements.txt
    """
    files = os.listdir(folder)

    # support requirement & requirements
    selected = [f for f in files if re.match("requirements?.txt", f)]

    return [os.path.join(folder, f) for f in selected]


def get_environment_name_from_yaml(env_yaml_path):
    """
    get name of environment from yaml
    :rtype: str
    :return: name of environment
    """
    matches = []  # line number and matched content of the file
    with codecs.open(env_yaml_path, "r", encoding="UTF-8") as f:
        for idx, line in enumerate(f):
            matched = re.match(r"name: *(?P<name>.*)", line)
            if matched:
                matches.append((idx+1, matched["name"].strip()))
    if len(matches) == 0:
        raise ValueError("could not determine name from yaml: %s" % env_yaml_path)
    elif len(matches) > 1:
        raise ValueError("got multiple name definition in yaml: %s" % str(matches))
    else:
        return matches[0][1]


def environment_exists(conda_folder, env_name):
    """
    returns whether the environment exists
    :rtype: bool
    :return: True if does, False if not
    """
    result = subprocess.run(
        [path_to_conda(conda_folder), "list", "--name", env_name],
        capture_output=True, text=True, check=False
    )

    if result.returncode == 0:
        return True
    elif result.stderr.strip().startswith("EnvironmentLocationNotFound"):
        return False
    else:
        print("error running conda list:")
        print("stdout:")
        print(result.stdout)
        print("stderr:")
        print(result.stderr)
        result.check_returncode()


def store_fi_hash(file_hash, installed_hash):
    """
    store "fi_hash" => file_hash, installed_hash
    """
    with codecs.open(CONDAW_FI_HASH_FILE, "w") as f:
        d = {"file_hash": file_hash, "installed_hash": installed_hash}
        json.dump(d, f, indent=4)


def load_fi_hash():
    """
    load "fi_hash" => file_hash, installed_hash
    """
    file = codecs.open(CONDAW_FI_HASH_FILE, "r")
    with file as f:
        d = json.load(f)
    return d["file_hash"], d["installed_hash"]


def compute_installed_hash(conda_folder, env_name):
    """
    compute installed_hash given conda to use and name of the environment
    :returns: None if environment does not exists
    :rtype: str | None
    """
    result = subprocess.run(
        [path_to_conda(conda_folder), "list", "--name", env_name],
        capture_output=True, text=True
    )

    return hashlib.sha256(result.stdout.encode(encoding="UTF-8")).hexdigest()


def compute_file_hash(env_file):
    """
    compute file_hash given the file
    :returns: hash of the file
    :rtype: str
    """
    with codecs.open(env_file, "r", encoding="UTF-8") as f:
        return hashlib.sha256(f.read().encode(encoding="UTF-8")).hexdigest()


def run_task(env_name, conda_folder, arguments):
    """
    run doit if installed, and run python if not
    """
    if detect_doit(env_name, conda_folder):
        print_verbose("doit detected")
        command = "doit"
    else:
        print_verbose("doit not detected, running python instead")
        command = "python"

    script_path = compile_trampoline_script(conda_folder, env_name, command, arguments)
    print_verbose("trampoline script compiled", script_path)

    print_verbose("jumping into trampoline, wee!")
    os.system(script_path)


def compile_trampoline_script(conda_folder, env_name, command, arguments):
    """
    compile a trampoline script to run in conda environment
    :rtype: str
    :returns: path to trampoline script
    """
    content = ""

    # add activation line
    if os.name == "nt":
        content += "@echo off" + os.linesep
        content += " ".join(["call", '"'+path_to_activate(conda_folder)+'"', env_name]) + os.linesep
    else:
        content += "#!/bin/bash" + os.linesep
        content += " ".join(["source", '"'+path_to_activate(conda_folder)+'"', env_name]) + os.linesep

    # add content line
    if command == "python":
        content += " ".join([path_to_python(conda_folder), *arguments]) + os.linesep
    elif command == "doit":
        content += " ".join([path_to_python(conda_folder), "-m", "doit", *arguments]) + os.linesep
    else:
        raise AssertionError("unknown command: %s" % command)

    # write to file
    with codecs.open(CONDAW_TRAMPOLINE_SCRIPT_FILE, "w", encoding="UTF-8") as f:
        f.write(content)

    return CONDAW_TRAMPOLINE_SCRIPT_FILE


def detect_doit(env_name, conda_folder):
    """
    detect whether doit is installed
    :rtype: bool
    """
    res = subprocess.run(
        [path_to_conda(conda_folder), "list", "--name", env_name],
        capture_output=True, text=True
    )

    found = re.findall(r"doit +\d+\.\d+\.\d+", res.stdout)

    return len(found) != 0

# main #


def main():
    setup_condaw_folder()
    conda_folder = prepare_conda_installation()
    env_name = setup_conda_environment(project_folder=os.getcwd(), conda_folder=conda_folder)
    run_task(env_name=env_name, conda_folder=conda_folder, arguments=sys.argv[1:])


if __name__ == '__main__':
    verbose = 1
    main()
