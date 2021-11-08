"""
hold logic for running final task
"""
import codecs
import os
import re
import subprocess

from condaw.file_constants import path_to_activate, path_to_python, CONDAW_TRAMPOLINE_SCRIPT_FILE, path_to_conda
from condaw.utils import print_verbose


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
        args = [path_to_python(conda_folder)]
        args += arguments
        content += " ".join(args) + os.linesep
    elif command == "doit":
        args = [path_to_python(conda_folder), "-m", "doit"]
        args += arguments
        content += " ".join(args) + os.linesep
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