import os
import shutil
from pathlib import Path


def task_compile():
    """
    compile the condaw module into 1 file
    """

    build_dir = Path("build")

    def mkdir_build():
        if build_dir.exists():
            shutil.rmtree(build_dir)
        build_dir.mkdir()

    def copy():
        shutil.copy(Path("condaw.bat"), build_dir / "condaw.bat")

    return {
        "actions": [
            mkdir_build,
            copy,
            "stickytape condaw/__init__.py --add-python-path . > build/condaw"
        ],
        "verbosity": 2
    }