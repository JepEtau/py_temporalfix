import subprocess
from helpers.p_print import lightcyan


def extract_info_from_vs_script(
    vs_command: list[str],
    vs_env: dict[str, str]
) -> tuple[bool, dict[str, str] | None]:
    print("Analyzing script...")
    vs_info_command = vs_command + ["--info"]
    # print(' '.join(vs_info_command))
    vs_subprocess: subprocess.Popen | None = None
    try:
        vs_subprocess = subprocess.Popen(
            vs_info_command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=vs_env,
        )
    except Exception as e:
        print(f"[E] Unexpected error: {type(e)}", flush=True)

    stdout_bytes: bytes
    stderr_bytes: bytes
    stdout_bytes, stderr_bytes = vs_subprocess.communicate()

    info: dict[str, str] = {}
    if stdout_bytes is not None:
        stdout: str = stdout_bytes.decode('utf-8)')

        print("Script info:")
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

    if stderr_bytes is not None:
        stderr: str = stderr_bytes.decode('utf-8)')
        if stderr:
            print(stderr)
            return False, info

    return True, info
