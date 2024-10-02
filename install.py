import logging
import os
import signal
import subprocess
import sys
import time

python_exe: str = "python"
minimum_py_packages: list[str] = [
    "requests",
    "rich",
]

def _install_minimum_py_packages() -> None:
    # Update pip
    pip_update_command: str = f"{python_exe} -m pip install --upgrade pip -v"
    try:
        subprocess.run(
            pip_update_command.split(' '),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=True
        )
    except Exception as e:
        sys.exit(f"Failed updating pip. {type(e)}")
        return False

    print("Pip module is up-to-date")

    # Install minimum python packages
    for package in minimum_py_packages:
        pip_command: str = (
            f"{python_exe} -m pip install {package}"
        )
        print(f"\033[96mInstalling {package}:\033[00m")
        install_subprocess: subprocess.Popen
        timeout: float = 20
        retry: int = 5
        _retry: int = retry
        try:
            install_subprocess = subprocess.Popen(
                pip_command.split(' '),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except Exception as e:
            sys.exit(f"Failed installing package {package}. {type(e)}")
            return False

        line: str = ''
        start_time = time.time()
        while (
            (time.time() - start_time) < timeout + (retry - _retry) * 5
            and install_subprocess.poll() is None
        ):
            start_time = time.time()
            line = ''
            try:
                line = install_subprocess.stdout.readline().decode('utf-8').strip()
            except:
                break
            if (
                line
                # and "Requirement already satisfied:" not in line
            ):
                print(line)

        stdout_b: bytes = install_subprocess.communicate()[0]
        try:
            line = stdout_b.decode('utf-8')
            if line:
                print(line)
        except:
            pass

    return True

if len(sys.argv) > 1 and sys.argv[1] != "continue":
    os.execv(sys.executable, ['python'] + sys.argv.append("continue"))

elif len(sys.argv) == 1 and not _install_minimum_py_packages():
    sys.exit("Error: failed installing minimum python packages.")


from utils.deps import logger
from utils.p_print import *
from utils.deps import (
    ExtPackage,
    install_ext_packages,
    install_py_packages,
    PyPackage,
    update_pip,
)


# Hardcoded because I'm too lazy to code parsing functions
def py_packages() -> tuple[PyPackage]:
    packages: tuple[PyPackage] = (
        PyPackage(
            pretty_name="NumPy",
            name="numpy",
            version="1.26.4",
        ),
    )
    return packages


def external_packages() -> tuple[ExtPackage]:
    packages: tuple[ExtPackage] = (
        ExtPackage(
            name="FFmpeg",
            dirname='ffmpeg',
            filename=(
                "ffmpeg_win32_x64.zip"
                if sys.platform == "win32"
                else "ffmpeg_linux_amd64.zip"
            )
        ),
        ExtPackage(
            name="VS python",
            dirname="vspython",
            filename=(
                "vspython.zip"
                if sys.platform == "win32"
                else ""
            )
        ),
    )
    return packages



def main():
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel("WARNING")

    success: bool = update_pip(python_exe)
    if success:
        logger.info("[I] pip is up-to-date")
    else:
        logger.warning("[W] Failed updating pip")

    install_py_packages(
        python_exe=python_exe,
        packages=py_packages(),
        threads=4
    )

    installed: bool = install_ext_packages(
        external_packages(),
        rehost_url_base="https://github.com/JepEtau/external_rehost/releases/download/external",
        threads=1,
    )
    if installed:
        print(lightgreen("All packages installed"))
    else:
        print(red("Error: missing package(s)"))


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
