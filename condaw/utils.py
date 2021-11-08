import os

from condaw import verbose


def print_verbose(*args):
    """
    print only in verbose
    """
    if verbose:
        print(" ".join([str(a) for a in args]))


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