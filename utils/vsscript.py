import subprocess
import sys
from .p_print import lightcyan
from .logger import logger


def extract_info_from_vs_script(
    vs_command: list[str],
    vs_env: dict[str, str]
) -> tuple[bool, dict[str, str] | None]:
    logger.debug("Analyzing script...")
    vs_info_command = vs_command + ["--info"]
    logger.debug(' '.join(vs_info_command))
    vs_subprocess: subprocess.Popen | None = None
    try:
        vs_subprocess = subprocess.Popen(
            vs_info_command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=vs_env,
        )
    except Exception as e:
        sys.exit(f"[E] Unexpected error: {type(e)}", flush=True)

    stdout_bytes: bytes = vs_subprocess.communicate()[0]

    info: dict[str, str] = {}
    if stdout_bytes is not None:
        stdout: str = stdout_bytes.decode('utf-8)')

        logger.debug("Script info:")
        print(lightcyan("Script info:"))
        for l in stdout.split('\n'):
            try:
                k, v = l.split(':')
            except:
                continue
            v = v.strip().replace('\t', '')
            k = k.strip().replace('\t', '')
            print(f"  {lightcyan(k)}: {v}")
            dv: int | str = ""
            try:
                dv = int(v)
            except:
                dv = v.lower()
            info[k.replace(' ', '_').lower()] = dv
    else:
        return False, None

    if stdout_bytes is not None:
        stdout: str = stdout_bytes.decode('utf-8)')
        logger.debug(stdout)
        if 'failed' in stdout or 'not supported' in stdout:
            sys.exit(f"Error while evaluating script:\n{stdout}")
            return False, info

    return True, info
