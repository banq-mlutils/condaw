
def task_compile():
    """
    compile the condaw module into 1 file
    """
    return {
        "actions": ["stickytape condaw/__init__.py --add-python-path . > condaw.py"],
        "verbosity": 2
    }