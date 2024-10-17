from pprint import pprint
import subprocess
import sys
from threading import Thread
from queue import Queue
import time
from typing import IO, Any, BinaryIO
from .p_print import lightcyan, purple
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





class VsThread(Thread):
    def __init__(
        self,
        in_queue: Queue,
        out_queue: Queue,
        vs_command: list[str],
        vs_env
    ) -> None:
        super().__init__()
        self.in_queue: Queue = in_queue
        self.out_queue: Queue = out_queue
        self.vs_command: list[str] = vs_command
        self.vs_env = vs_env
        self._stdout: BinaryIO | None = None
        self._is_ready: bool = False
        self._ended: bool = False
        self.remaining_frames: bytes | None = None


    def run(self) -> None:
        vs_subprocess: subprocess.Popen | None = None
        try:
            vs_subprocess = subprocess.Popen(
                self.vs_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self.vs_env,
                bufsize=20*10070784
            )
        except Exception as e:
            print(f"[E] Unexpected error: {type(e)}", flush=True)

        self._stdout = vs_subprocess.stdout
        print(purple(f"vs thread started:"), f"{' '.join(self.vs_command)}")
        no: int = 0
        self._is_ready = True
        self.on_going = 0
        while True:
            in_frame = self.in_queue.get()
            if in_frame is None:
                break
            print(purple(f"sending {no}"))
            vs_subprocess.stdin.write(in_frame)
            self.on_going += 1
            # if self.on_going > 14:
            #     time.sleep(2)
            no += 1
        time.sleep(10)
        self.remaining_frames, std_err = vs_subprocess.communicate()
        pprint(std_err)
        # print(purple("vs thread ended"))
        # print(purple(f"remaining: {len(self.remaining_frames)}"))
        # time.sleep(0.2)
        self._ended = True


    @property
    def stdout(self) -> BinaryIO:
        return self._stdout


    def is_ready(self) -> bool:
        return self._is_ready


    def remaining_bytes(self) -> bytes:
        return self.remaining_frames

    def ended(self) -> bool:
        return self._ended
