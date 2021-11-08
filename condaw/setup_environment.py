"""
hold logic for setting up environment
"""
import codecs
import hashlib
import json
import os
import re
import subprocess

from condaw.file_constants import path_to_conda, CONDAW_FI_HASH_FILE
from condaw.utils import print_verbose


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