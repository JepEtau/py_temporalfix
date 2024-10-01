from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from importlib import metadata
import os
from pprint import pprint
import re
import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
import subprocess
import time
from urllib.parse import unquote

from .ext_packages import ExtPackage, download_package
from .logger import logger
from ..path_utils import get_app_tempdir
from ..p_print import *


@dataclass
class PyPackage:
    pretty_name: str
    name: str
    version: str = ""
    index_url: str = ""
    extra: str = ""
    wheel: str = ""
    url: str = ""
    size: int = 0
    supported: bool = True
    installed: bool = False
    installed_version: str = ""
    uninstall_before: bool = False
    delay_install: bool = False

    def is_installed(self) -> bool:
        # print(lightcyan(f"[{self.installed_version}] vs [{self.version}]"))
        return bool(self.version == self.installed_version)



def update_pip(python_exe: str) -> bool:
    pip_command: str = f"{python_exe} -m pip install --upgrade pip"
    try:
        subprocess.run(
            pip_command.split(' '),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=True
        )
    except:
        return False
    return True



def update_package_info(package: PyPackage, retry: int = 3) -> None:
    installed_version: str = ""
    try:
        installed_version = metadata.metadata(package.name).json['version']
        logger.debug(f"[V] {package.pretty_name}: {installed_version}")
        package.installed_version = installed_version
    except:
        logger.info(f"[I] Package {package.pretty_name} is not installed")



def update_package_url(
    python_exe: str,
    package: PyPackage,
    retry: int = 3
) -> bool:
    timeout: float = 5
    _retry: int = retry
    if package.index_url:
        regex: re.Pattern = re.compile(rf".*Downloading\s*(https:\/\/.*\/.*\.whl)")
    else:
        regex: re.Pattern = re.compile(rf".*{package.name}.*(https:\/\/.*\/.*\.whl)\.metadata")

    already_installed_regex = re.compile(rf".*Requirement\s*already\s*satisfied:\s*{package.name}")
    url: str = ""

    start_time: float = time.time()
    index_url: list[str] = ["--index-url", package.index_url] if package.index_url else []
    version = f"=={package.version}" if package.version != '' else ''
    pip_command: list[str] = [
        f"{python_exe}",
        "-m", "pip", "download",
        # "--no-deps",
        "--no-cache-dir",
        f"{package.name}{version}",
        *index_url,
        "--progress-bar=off",
        "-vvv"
    ]
    pip_command = list([x for x in pip_command if x != '' and x is not None])
    logger.info(' '.join(pip_command))
    while _retry > 0 and url == '' and not package.installed and package.supported:
        sub_process = subprocess.Popen(
            pip_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        start_time = time.time()
        while (
            (time.time() - start_time) < timeout + (retry - _retry) * 5
            and sub_process.poll() is None
        ):
            try:
                line = sub_process.stdout.readline().decode('utf-8').strip()
            except:
                break
            if package.name == 'torch':
                # and line.startswith("Obtaining dependency information"):
                print(lightcyan(line))

            # if _retry < retry:
            #     logger.debug(line)

            if (result := re.search(regex, line)):
                sub_process.terminate()
                url = result.group(1)
                break

            if (result := re.search(already_installed_regex, line)):
                sub_process.terminate()
                package.installed = True
                break

            if "No matching distribution found" in line:
                sub_process.terminate()
                package.supported = False
                logger.warning(f"[W] {package.pretty_name} is not supported on this platform")
                break

        if url == '' or package.installed:
            if sub_process.poll() is None:
                sub_process.terminate()
            while sub_process.poll() is None and (time.time() - start_time) > 2:
                time.sleep(0.5)

            if not package.installed and package.supported:
                _retry -= 1
                timeout += (retry - _retry) * 5
                logger.warning(f"retry: {_retry}, new timeout: timeout")

    package.url = url
    if package.url == '' and not package.installed and package.supported:
        logger.error(red(f"[E] Failed  to fetch url for {package.name}"))

    elif package.installed:
        logger.info(f"[I] {package.pretty_name} already installed")

    elif package.url != '':
        package.wheel = unquote(package.url.split('/')[-1])
        package.version = unquote(package.wheel.split('-')[1])
        response: requests.Response
        try:
            response = requests.get(package.url, stream=True)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if str(e).startswith('404'):
                logger.error(f"File {package.url} not found")
            return False
        package.size=int(response.headers.get('Content-length', 0))

    return True


def uninstall_py_package(package: PyPackage) -> bool:
    logger.debug(f"[V] uninstall {package.name}")
    pip_command: str = f"python -m pip uninstall -y {package.name}"
    try:
        subprocess.run(
            pip_command.split(' '),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except:
        return False
    return True


def install_py_package(
    python_exe: str,
    package: PyPackage,
    ext_package: ExtPackage
) -> bool:
    logger.debug(lightgrey(f"  install {ext_package.tmp_file}"))

    if package.uninstall_before:
        uninstall_py_package(package)

    pip_command: list[str] = [
        python_exe,
        "-m", "pip", "install",
        "--no-cache-dir",
        ext_package.tmp_file,
        "--progress-bar=off",
        "-v"
    ]

    sub_process = subprocess.Popen(
        pip_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    while sub_process.poll() is None:
        try:
            line = sub_process.stdout.readline().decode('utf-8').strip()
        except:
            break
        print(line)


    package.installed = True
    # try:
    #     shutil.rmtree(os.path.dirname(ext_package.tmp_file))
    # except:
    #     pass
    logger.debug(lightgrey(f"  {package.name} installed"))

    return True



def download_install_py_package(
    python_exe: str,
    package: PyPackage,
    progress: Progress| None = None,
    retry: int = 3
) -> bool:
    url: str = package.url
    temp_dir: str = get_app_tempdir()

    response: requests.Response
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        if str(e).startswith('404'):
            logger.error(f"File {url} not found")
        else:
            logger.error(f"Error with url {url}: {type(e)}")
        return False

    # Use the external package download procedure
    ext_package = ExtPackage(
        name=package.pretty_name,
        filename=package.wheel,
        size=package.size,
        response=response,
        dirname="wheels",
        tmp_file=os.path.join(temp_dir, "wheels", package.wheel)
    )

    # Download package
    if (
        os.path.exists(ext_package.tmp_file)
        and os.path.getsize(ext_package.tmp_file) == ext_package.size
    ):
        ext_package.downloaded = True
        logger.debug(lightgrey(f"  already downloaded"))

    else:
        ext_package.downloaded = download_package(
            ext_package,
            progress=progress,
            task_id=progress.add_task(
                "[green] Installing...",
                name=ext_package.name,
                start=False
            ),
            retry=retry
        )

    if not ext_package.downloaded:
        return False

    if not package.delay_install:
        print("install non delayed")
        package.installed = install_py_package(python_exe, package, ext_package)
        return package.installed
    return True




def install_py_packages(
    python_exe: str,
    packages: tuple[PyPackage],
    retry: int = 3,
    threads: int = 1,
) -> bool:
    threads = min(max(threads, 1), len(packages))
    progress = Progress(
        TextColumn("[bold cyan]{task.fields[name]}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
    )

    def _get_info(package: PyPackage) -> None:
        update_package_info(package)
        update_package_url(python_exe, package)
        logger.debug(f"[V] {package.pretty_name}: {package.url}")
        if package.supported:
            if not package.is_installed():
                logger.info(orange(
                    f"[I] {package.pretty_name} has to be updated: "
                    + f"{package.installed_version} -> {package.version}"
                ))
            else:
                logger.info(lightgreen(
                    f"[I] {package.pretty_name} is already installed: {package.version}"
                ))


    with ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(_get_info, packages)

    packages = [package for package in packages if not package.is_installed()]
    if not packages:
        logger.info(f"[I] No packages to update")
        return True

    logger.info(f"[I] {len(packages)} packages to update")
    success: bool = True
    if threads == 1:
        with progress:
            for package in packages:
                success = download_install_py_package(
                    python_exe,
                    package,
                    progress=progress,
                    retry=retry
                )
                if not success:
                    logger.info(f"Failed installing {package.name}")
                    break

    else:
        with progress:
            with ThreadPoolExecutor(max_workers=threads) as executor:
                for result in executor.map(
                    lambda args: download_install_py_package(*args),
                    [(python_exe, package, progress, retry) for package in packages]
                ):
                    success = success and result

    if not success:
        return False

    # Install remaining packages
    print("remaining packages")
    for package in packages:
        if package.delay_install and not package.installed:
            package.delay_install = False
            download_install_py_package(python_exe, package)


    return True
