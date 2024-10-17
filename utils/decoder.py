from dataclasses import dataclass
from pprint import pprint
import subprocess
import sys
from threading import Thread
from queue import Queue
from .media import (
    ChannelOrder,
    FShape,
    MediaInfo,
    str_to_video_codec,
    VideoCodec,
    VideoInfo,
    vcodec_to_extension,
)
from .p_print import lightcyan, red
from .path_utils import get_extension
from .pxl_fmt import PIXEL_FORMAT
from .tools import ffmpeg_exe



def generate_ffmpeg_decoder_cmd(
    in_vi: VideoInfo,
    out_vi: VideoInfo,
) -> list[str]:

    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-nostats",
        "-i", in_vi['filepath'],
        "-an",
        "-sn",
        "-f", "image2pipe",
        "-pix_fmt", out_vi['pix_fmt'],
        "-vcodec", "rawvideo",
        "-"
    ]

    return ffmpeg_command


class DecoderThread(Thread):
    def __init__(
        self,
        queue: Queue,
        in_video_info: VideoInfo,
        out_video_info: VideoInfo,
    ) -> None:
        super().__init__()
        self.queue: Queue = queue
        self.dec_command: list[str] = generate_ffmpeg_decoder_cmd(
            in_vi=in_video_info,
            out_vi=out_video_info
        )
        self.frame_count: int = in_video_info['frame_count']
        in_h, in_w = in_video_info['shape'][:2]
        self.in_nbytes: int = in_h * in_w * out_video_info['bpp'] // 8


    def run(self) -> None:
        print(lightcyan(" ".join(self.dec_command)))
        dec_subprocess: subprocess.Popen | None = None
        try:
            dec_subprocess = subprocess.Popen(
                self.dec_command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(f"[E] Unexpected error: {type(e)}", flush=True)

        for i in range(self.frame_count):
            print(lightcyan(f"decoding: frame no. {i}"))
            self.queue.put(
                dec_subprocess.stdout.read(self.in_nbytes)
            )

        print(lightcyan(f"decoding: ended"))
        self.queue.put(None)
