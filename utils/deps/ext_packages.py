from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import os
import requests
import shutil
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from ..p_print import *
from ..path_utils import get_app_tempdir, get_extension
from ..tools import external_dir
from ..time_conversions import reformat_datetime
from .logger import logger



@dataclass
class ExtPackage:
    name: str
    dirname: str
    filename: str
    size: int = 0
    host: str = ''
    response: requests.Response | None = None
    last_modified: str = ''
    downloaded: bool = False
    installed: bool = False
    install_dir: str = ''
    tmp_file: str = ''
    skip: bool = False

    def __post_init__(self):
        self.skip = bool(self.filename == '')



def download_package(
    package: ExtPackage,
    retry: int = 3,
    progress: Progress| None = None,
    task_id: TaskID | None = None,
) -> bool:
    tmp_dir: str = os.path.dirname(package.tmp_file)
    os.makedirs(tmp_dir, exist_ok=True)

    logger.debug(f"Download package: {package.filename}")

    _retry: int = retry
    while _retry:
        logger.debug(f"Downloading: {package.name} to {tmp_dir}")
        if progress is not None:
            progress.update(task_id, total=package.size)
            progress.start_task(task_id)

        with open(package.tmp_file, "wb") as f:
            try:
                for data in package.response.iter_content(chunk_size=1024):
                    f.write(data)
                    if progress is not None:
                        progress.update(task_id, advance=len(data))
            except Exception as e:
                logger.info("[W] Retry download, error: type(e)")
                _retry -= 1
                continue

        if _retry == 0:
            logger.info(f"[E] failed downloading {package.filename}")
            return False

        _retry = 0

    if package.last_modified:
        open(os.path.join(tmp_dir, package.last_modified), 'w').close()

    return  True



def install_ext_package(package: ExtPackage) -> bool:
    logger.info(lightgrey(f"  install"))
    install_dir: str = package.install_dir

    extension: str = get_extension(package.tmp_file)
    if os.path.exists(install_dir):
        shutil.rmtree(install_dir)
    if extension == '.zip':
        import zipfile
        with zipfile.ZipFile(package.tmp_file, "r") as f:
            f.extractall(install_dir)

    else:
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)
        os.makedirs(install_dir)
        shutil.move(package.tmp_file, install_dir)

    package.installed = True
    open(os.path.join(install_dir, package.last_modified), 'w').close()
    try:
        shutil.rmtree(os.path.dirname(package.tmp_file))
    except:
        pass
    logger.info(lightgrey(f"  {package.name} installed"))

    return True



def download_install_ext_package(
    package: ExtPackage,
    progress: Progress| None = None,
    retry: int = 3,
) -> bool:
    temp_dir: str = get_app_tempdir()
    if package.skip:
        return True
    logger.info(f"Package: {package.name}")

    # Get info from host and update package info
    url: str = f"{package.host}/{package.filename}"
    response: requests.Response
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        if str(e).startswith('404'):
            logger.error(f"File {url} not found")
        return False
    last_modified: str = reformat_datetime(response.headers['Last-Modified'])
    package.size=int(response.headers.get('Content-length', 0))
    package.response=response
    package.last_modified=last_modified
    package.tmp_file=os.path.join(temp_dir, package.dirname, package.filename)

    # Check if installed
    package.install_dir = os.path.join(external_dir, package.dirname)
    if os.path.exists(os.path.join(package.install_dir, last_modified)):
        package.installed = True
        logger.info(lightgrey(f"  already installed"))
        try:
            shutil.rmtree(os.path.dirname(package.tmp_file))
        except:
            pass
        return True

    # Download package
    if (
        os.path.exists(os.path.join(temp_dir, package.dirname, last_modified))
        and os.path.exists(package.tmp_file)
        and os.path.getsize(package.tmp_file) == package.size
    ):
        package.downloaded = True
        logger.info(lightgrey(f"  already downloaded"))

    else:
        package.downloaded = download_package(
            package,
            progress=progress,
            task_id=progress.add_task(
                "[green] Installing...",
                name=package.name,
                start=False
            ),
            retry=retry
        )

    if not package.downloaded:
        return False

    # Install package
    return install_ext_package(package)




def install_ext_packages(
    packages: tuple[ExtPackage],
    rehost_url_base: str,
    retry: int = 3,
    threads: int = 1,
) -> bool:
    threads = min(max(threads, 1), len(packages))
    progress = Progress(
        TextColumn("[bold cyan]{task.fields[name]}", justify="right"),
        BarColumn(bar_width=40),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
    )

    for package in packages:
        package.host = rehost_url_base

    packages = [package for package in packages if not package.skip]
    if threads == 1:
        with progress:
            for package in packages:
                success = download_install_ext_package(package, progress, retry)
                if not success:
                    return False
    else:
        success: bool = True
        with progress:
            with ThreadPoolExecutor(max_workers=threads) as executor:
                for result in executor.map(
                    lambda args: download_install_ext_package(*args),
                    [(package, progress, retry) for package in packages]
                ):
                    success = success and result
        return success

    return True
