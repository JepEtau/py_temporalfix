from dataclasses import dataclass
from pprint import pprint
import re
import sys

from .media import (
    ChannelOrder,
    FShape,
    MediaInfo,
    str_to_video_codec,
    VideoCodec,
    VideoInfo,
    vcodec_to_extension,
)
from .p_print import red
from .path_utils import get_extension
from .pxl_fmt import PIXEL_FORMAT
from .tools import ffmpeg_exe



def generate_ffmpeg_decoder_cmd(
    in_vi: VideoInfo,
    out_vi: VideoInfo,
) -> list[str]:

    in_h, in_w = in_vi['shape'][:2]
    fps: str = ""

    f_rate = in_vi['frame_rate_r']
    if isinstance(f_rate, tuple | list):
        fps = ":".join(map(str, f_rate))
    else:
        fps = str(f_rate)

    ffmpeg_command: list[str] = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "warning",
        "-stats",
        '-f', 'rawvideo',
        '-pixel_format', out_vi['pix_fmt'],
        '-video_size', f"{in_w}x{in_h}",
        "-r", fps,
        '-i', 'pipe:0'
    ]

    return ffmpeg_command


