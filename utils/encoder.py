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


@dataclass
class FFv1Settings:
    level: int = 1
    coder: int = 1
    context: int = 1
    g: int = 1
    threads: int = 8


@dataclass
class H264Settings:
    pass


@dataclass
class H265Settings:
    pass


@dataclass
class DNxHRSettings:
    profile: str | None = None

CodecSettings = FFv1Settings | H264Settings | H265Settings | DNxHRSettings

@dataclass
class ColorSettings:
    colorspace: str | None = 'bt709'
    color_primaries: str | None = 'bt709'
    color_trc: str | None = 'bt709'
    color_range: str | None = 'tv'


@dataclass(slots=True)
class VideoEncoderParams:
    filepath: str
    # Complex filters
    keep_sar: bool = True
    size: tuple[int, int] | None = None
    resize_algo: str = ''
    add_borders: bool = False
    # Encoder
    vcodec: VideoCodec = VideoCodec.H264
    pix_fmt: str | None = 'yuv420p'
    preset: str | None = 'medium'
    tune: str | None = None
    crf: int | None = None
    overwrite: bool = True
    codec_settings: CodecSettings | None = None
    color_settings: ColorSettings | None = None
    ffmpeg_args: str = ''
    # Audio
    copy_audio: bool = False
    # Debug
    benchmark: bool = False
    verbose: bool = False



def arguments_to_encoder_params(
    arguments,
    video_info: VideoInfo,
) -> VideoEncoderParams:
    """Parse the command line to set the encoder parameters
    """
    # Copy from input
    params: VideoEncoderParams = VideoEncoderParams(
        filepath='',
        vcodec=str_to_video_codec[video_info['codec']],
        keep_sar=True,
        pix_fmt=video_info['pix_fmt'],
    )

    # Encoder: codec, settings
    if arguments.vcodec:
        params.vcodec = str_to_video_codec[arguments.vcodec]

    if arguments.preset:
        params.preset = arguments.preset
    if arguments.tune:
        params.tune = arguments.tune
    if arguments.crf:
        params.crf = arguments.crf

    vcodec: VideoCodec = params.vcodec
    if vcodec == VideoCodec.FFV1:
        params.codec_settings = FFv1Settings()

    elif vcodec == VideoCodec.DNXHD:
        params.codec_settings = DNxHRSettings(
            profile=video_info['profile']
        )
        params.preset = params.tune = params.crf = None

    # Extract pix_fmt from ffmpeg_args
    if (
        not arguments.pix_fmt
        and (re_match := re.search(re.compile(r"-pix_fmt\s([a-y0-9]+)"), arguments.ffmpeg_args))
    ):
        params.pix_fmt = re_match.group(1)

    elif arguments.pix_fmt:
        params.pix_fmt = arguments.pix_fmt

    if params.pix_fmt not in PIXEL_FORMAT.keys():
        sys.exit(red(f"Error: pixel format \"{params.pix_fmt}\" is not supported"))

    # Colorspace
    params.color_settings = ColorSettings(
        colorspace=video_info.get('color_space', None),
        color_primaries=video_info.get('color_primaries', None),
        color_trc=video_info.get('color_transfer', None),
        color_range=video_info.get('color_range', None),
    )

    # Set the output extension depending on the codec
    out_fp: str = video_info['filepath']
    if get_extension(out_fp) == '.$$$':
        out_fp = out_fp.replace('.$$$', vcodec_to_extension[vcodec])
    params.filepath = out_fp

    # Modify the encoder settings used by the encoder node
    params.ffmpeg_args = arguments.ffmpeg_args
    params.benchmark = arguments.benchmark

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

    ffmpeg_command.extend(["-map", "0:v"])

    # Encoder
    if (
        "-vcodec" not in params.ffmpeg_args
        and "-c:v" not in params.ffmpeg_args
    ):
        ffmpeg_command.extend(["-vcodec", f"{params.vcodec.value}"])

    if "-pix_fmt" not in params.ffmpeg_args:
        ffmpeg_command.extend(["-pix_fmt", f"{params.pix_fmt}"])

    # Settings
    if "-preset" not in params.ffmpeg_args and params.preset:
        ffmpeg_command.extend(["-preset", f"{params.preset}"])

    if "-tune" not in params.ffmpeg_args and params.tune:
        ffmpeg_command.extend(["-tune", f"{params.tune}"])

    if (
        "-crf" not in params.ffmpeg_args
        and params.crf is not None
        and params.crf > 0
    ):
        ffmpeg_command.extend(["-crf", f"{params.crf}"])

    if params.codec_settings is not None:
        for k, v in params.codec_settings.__dict__.items():
            ffmpeg_command.extend([f"-{k}", v])

    # Color space
    color_settings: ColorSettings = params.color_settings
    _tmp_array: list[str] = []
    for k, v in color_settings.__dict__.items():
        if k == 'color_range':
            continue
        if (
            k not in params.ffmpeg_args
            and v is not None
        ):
            _tmp_array.append(f"{k}={v}")
    if _tmp_array:
        ffmpeg_command.extend([
            "-vf",  f"setparams={':'.join(_tmp_array)}"
        ])

    k, v = 'color_range', color_settings.color_range
    if (
        k not in params.ffmpeg_args
        and v is not None
        and v.lower() not in ("unknown", "unspecified")
    ):
        limited: tuple[str] = ("tv", "mpeg", "limited")
        # full: tuple[str] = ("pc", "jpeg", "full")
        ffmpeg_command.extend([f"-{k}", "limited" if v.lower() in limited else "full"])

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
    codec_params: str = params.ffmpeg_args
    if not codec_params and params.vcodec == VideoCodec.H265:
        # Add default if no custom params for H265
        codec_params = "-profile:v main422-10 -x265-params sao=0"
    ffmpeg_command.extend(codec_params.split(" "))

    # Add metadata
    if get_extension(params.filepath) == ".mkv":
        ffmpeg_command.extend(["-movflags", "use_metadata_tags"])
        metadata: dict[str, str]
        for metadata in (video_info['metadata'], in_vi['metadata']):
            if metadata is not None and len(metadata.keys()):
                for k, meta in metadata.items():
                    ffmpeg_command.extend(["-metadata:s:v:0", f"{k}={meta}"])

    # Output filepath
    ffmpeg_command.append(params.filepath)
    if params.overwrite:
        ffmpeg_command.append('-y')


    # _tmp: str = "A:\\py_temporalfix\\external\\ffmpeg\\ffmpeg.exe -hide_banner -loglevel error -stats -f rawvideo -pixel_format yuv444p16le -video_size 1488x1128 -r 25:1 -i pipe:0 -vf setdar=62/47 -vcodec libx264 -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1 -pix_fmt yuv420p -colorspace 1 -color_primaries 1 -color_trc 1 -color_range tv N:\\cache\\g_fin\\eval\\g_fin_005__j_ep99_hr_st_fixed_6_400_x264.mkv -y"
    # ffmpeg_command = _tmp.split(" ")

    return ffmpeg_command
