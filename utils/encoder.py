from dataclasses import dataclass
from enum import Enum
import math
from pprint import pprint
import re
import numpy as np
import sys

from utils.path_utils import get_extension

from .p_print import red
from .media import (
    ChannelOrder,
    FShape,
    MediaInfo,
    VideoInfo
)
from .pxl_fmt import PIXEL_FORMAT
from .tools import ffmpeg_exe


class VideoEncoder(Enum):
    H264 = "libx264"
    H265 = "libx265"
    VP9 = "libvpx-vp9"
    FFV1 = "ffv1"


str_to_video_encoder: dict[str, VideoEncoder] = {
    'h264': VideoEncoder.H264,
    'h265': VideoEncoder.H265,
    'ffv1': VideoEncoder.FFV1,
    'vp9': VideoEncoder.VP9,
}


@dataclass
class FFv1Settings:
    level: int = 1
    coder: int = 1
    context: int = 1
    g: int = 1
    threads: int = 8


@dataclass(slots=True)
class H264Settings:
    # bpp 8/10
    pass


@dataclass(slots=True)
class H265Settings:
    # bpp: 8/10/12
    pass


EncoderSettings = FFv1Settings | H264Settings | H265Settings



@dataclass(slots=True)
class VideoEncoderParams:
    filepath: str
    # Complex filters
    keep_sar: bool = True
    size: tuple[int, int] | None = None
    resize_algo: str = ''
    add_borders: bool = False
    # Encoder
    encoder: VideoEncoder = VideoEncoder.H264
    pix_fmt: str = 'yuv420p'
    preset: str = 'medium'
    tune: str = ''
    crf: int = 15
    overwrite: bool = True
    encoder_settings: EncoderSettings | None = None
    # color_settings: ColorSettings | None = None
    ffmpeg_args: str = ''
    # Audio
    copy_audio: bool = False
    # Debug
    benchmark: bool = False
    verbose: bool = False



def encoder_frame_prop(
    shape: FShape,
    pix_fmt: str,
    fp32: bool = False,
) -> tuple[FShape, np.dtype, ChannelOrder, int, np.dtype] | None:
    """Returns the shape, input dtype, channel order
        size in bytes and output dtype of a frame to be encoded
        fp32: force input dtype to float32, and channel order to bgr
    """

    # Encoder: pixel format
    pixel_format = None
    try:
        pixel_format = PIXEL_FORMAT[pix_fmt]
    except:
        pass

    # TODO: remove test of 'supported'
    if (
        pixel_format is None
        or not pixel_format['supported']
        or pixel_format['c_order'] == ''
    ):
        sys.exit(f"[E] {pix_fmt} is not a supported pixel format")

    out_bpp, c_order = pixel_format['bpp'], pixel_format['c_order']
    if out_bpp > 16:
        sys.exit(f"[E] {pix_fmt} is not a supported pixel format (bpp>16)")
    c_order = 'bgr' if 'bgr' in c_order or fp32 else 'rgb'

    if 'f' in pixel_format:
        sys.exit(f"[E] {pix_fmt} is not a supported pixel format (floating point)")
    out_dtype: np.dtype = np.uint16 if out_bpp > 8 else np.uint8
    in_dtype = np.float32 if fp32 else out_dtype

    return (
        shape,
        in_dtype,
        c_order,
        math.prod(shape) * np.dtype(in_dtype).itemsize,
        out_dtype
    )



def arguments_to_encoder_params(
    arguments,
    video_info: VideoInfo,
) -> VideoEncoderParams:
    """Parse the command line to set the encoder parameters
    """
    # Encoder: encoder, settings
    encoder: VideoEncoder = str_to_video_encoder[arguments.encoder]
    encoder_settings: EncoderSettings | None = None
    if encoder == VideoEncoder.FFV1:
        encoder_settings = FFv1Settings()

    # Extract pixfmt from ffmpeg_args
    pix_fmt: str = arguments.pix_fmt
    if (re_match := re.search(
        re.compile(r"-pix_fmt\s([a-y0-9]+)"), arguments.ffmpeg_args)
    ):
        pix_fmt = re_match.group(1)
    if pix_fmt not in PIXEL_FORMAT.keys():
        sys.exit(red(f"Error: pixel format \"{pix_fmt}\" is not supported"))

    # Encoder: colorspace
    # removed for this application

    # Create the encoder settings used by the encoder node
    params: VideoEncoderParams = VideoEncoderParams(
        filepath=video_info['filepath'],
        encoder=encoder,
        pix_fmt=pix_fmt,
        preset=arguments.preset,
        tune=arguments.tune,
        crf=arguments.crf,
        encoder_settings=encoder_settings,
        ffmpeg_args=arguments.ffmpeg_args,
        benchmark=arguments.benchmark,
    )

    # Copy audio stream if no video clipping
    if (
        arguments.ss == ''
        and arguments.to == ''
        and arguments.t == ''
    ):
        params.copy_audio = True

    return params



def generate_ffmpeg_encoder_cmd(
    video_info: VideoInfo,
    params: VideoEncoderParams,
    in_media_info: MediaInfo
) -> list[str]:
    """Generate a FFmpeg command line from parameters and info
    video_info: info of the stream sent to the stdin pipe of FFmpeg
    in_media_info: info of the original media. Used to copy characteristics
    and audio/subtitles tracks to the output file.
    """
    in_vi: VideoInfo = in_media_info['video']
    fps: str = ""

    f_rate = video_info['frame_rate_r']
    if isinstance(f_rate, tuple | list):
        fps = ":".join(map(str, f_rate))
    else:
        fps = str(f_rate)

    h, w = video_info['shape'][:2]

    ffmpeg_command = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "error",
        "-stats",
        '-f', 'rawvideo',
        '-pixel_format', video_info['pix_fmt'],
        '-video_size', f"{w}x{h}",
        "-r", fps,
        '-i', 'pipe:0'
    ]

    if params.copy_audio and in_media_info['audio']['nstreams'] > 0:
        ffmpeg_command.extend(['-i', in_vi['filepath']])

    if params.benchmark:
        ffmpeg_command.extend(["-benchmark", "-f", "null", "-"])
        return ffmpeg_command

    # Aspect ratio
    sar_dar: list[str] = []
    if 'sar' in in_vi:
        sar : str = '/'.join(map(str, in_vi['sar']))
        if sar != "1/1":
            sar_dar.append(f"setsar={sar}")

    if 'dar' in in_vi:
        dar : str = '/'.join(map(str, in_vi['dar']))
        if dar != "1/1":
            sar_dar.append(f"setdar={dar}")

    if sar_dar:
        ffmpeg_command.extend(["-vf", ','.join(sar_dar)])

    ffmpeg_command.extend([
        "-map", "0:v"
    ])

    # Color
    color_to_option: dict[str, str] = {
        'color_space': 'colorspace',
        'color_transfer': 'color_trc',
        'color_primaries': 'color_primaries',
        'color_range': 'range',
        'color_matrix': 'colormatrix',
    }
    for k, v in color_to_option.items():
        if in_vi[k] is not None and v not in params.ffmpeg_args:
            ffmpeg_command.extend([f"-{v}={in_vi[k]}"])

    # Encoder
    if "-vcodec" not in params.ffmpeg_args:
        ffmpeg_command.extend(["-vcodec", f"{params.encoder.value}"])

    if "-pix_fmt" not in params.ffmpeg_args:
        ffmpeg_command.extend(["-pix_fmt", f"{params.pix_fmt}"])

    if "-preset" not in params.ffmpeg_args and params.preset:
        ffmpeg_command.extend(["-preset", f"{params.preset}"])

    if "-tune" not in params.ffmpeg_args and params.tune:
        ffmpeg_command.extend(["-tune", f"{params.tune}"])

    if "-crf" not in params.ffmpeg_args and params.crf != -1:
        ffmpeg_command.extend(["-crf", f"{params.crf}"])

    # Audio/subtitles
    if params.copy_audio and True:
        if in_media_info['audio']['nstreams'] > 0:
            ffmpeg_command.extend([
                "-map", "1:a", "-acodec", "copy"
            ])
        if in_media_info['subtitles']['nstreams'] > 0:
            ffmpeg_command.extend([
                "-map", "2:s", "-scodec", "copy"
            ])

    # Custom params
    if params.ffmpeg_args:
        ffmpeg_command.extend(params.ffmpeg_args.split(" "))

    # Add metadata
    if get_extension(params.filepath) == ".mkv":
        ffmpeg_command.extend(["-movflags", "use_metadata_tags"])
        metadata: dict[str, str]
        for metadata in (video_info['metadata'], in_vi['metadata']):
            if len(metadata.keys()):
                for k, meta in metadata.items():
                    ffmpeg_command.extend(["-metadata:s:v:0", f"{k}={meta}"])

    # Output filepath
    ffmpeg_command.append(params.filepath)
    if params.overwrite:
        ffmpeg_command.append('-y')

    return ffmpeg_command
