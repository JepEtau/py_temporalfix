import os
from pathlib import Path
import tempfile
from typing import Literal


pathAccess: dict = {
    'r': os.R_OK,
    'w': os.W_OK,
    'rw': os.O_RDWR,
}


def is_access_granted(path: str | Path, access: Literal['r', 'w', 'rw']):
    return os.access(str(path), mode=pathAccess[access])


def path_split(fp: str | Path) -> tuple[str, str, str]:
    """Returns the [directory, basename, extension]
    of the given filepath.
    """
    base, extension = os.path.splitext(str(fp))
    directory, basename = os.path.split(base)
    return directory, basename, extension.lower()


def os_path_basename(fp: str | Path) -> str:
    """Return the basename without extension"""
    return os.path.splitext(os.path.basename(fp))[0]


def get_extension(fp: str) -> str:
    """Returns the extensions in lower case"""
    return os.path.splitext(fp)[1].lower()


def absolute_path(path: str | Path) -> str:
    if path is not None and path != "":
        return os.path.abspath(os.path.expanduser(str(path)))
    return path


def get_app_tempdir() -> str:
    tmp_dirname: str = os.path.join(
        tempfile.gettempdir(),
        os.path.split(
            absolute_path(
                os.path.join(os.path.dirname(__file__), os.pardir)
            )
        )[-1]
    )
    return tmp_dirname
