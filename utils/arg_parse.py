from argparse import (
    ArgumentParser,
    ArgumentTypeError,
    Namespace,
    RawTextHelpFormatter,
)


class BoundedInteger:
    def __init__(self, min_value: int, max_value: int) -> None:
        self.min_value: int = min_value
        self.max_value: int = max_value

    def __call__(self, value) -> int:
        try:
            value = int(value)
        except:
            raise ArgumentTypeError(f"Value is not a valid argument.")
        if self.min_value <= value <= self.max_value:
            return value
        raise ArgumentTypeError(
            f"Value is not a valid argument, allowed range: {self.min_value}..{self.max_value}"
        )



def arg_parse() -> Namespace:
    parser = ArgumentParser(
        description="Python wrapper for vs_temporal_fix script",
        formatter_class=RawTextHelpFormatter
    )
    parser = ArgumentParser(
        description="Python wrapper of vs_temporal_fix",
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="""Input video file.
"""
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=False,
        help="""Output video file. If not specified, it will append a suffix to the input filename.
"""
    )

    parser.add_argument(
        "--suffix",
        type=str,
        default="_fixed",
        required=False,
        help="""Suffix used when no output filename is specified.
"""
    )

    parser.add_argument(
        "-tr",
        "--t_radius",
        type=BoundedInteger(1, 10),
        metavar="[1..10]",
        default=6,
        required=False,
        help="""Temporal radius sets the number of frames to average over. Higher means more stable.
If you get blending/ghosting on small movements or blocky artifacts, reduce this.
\n"""
    )

    parser.add_argument(
        "-s",
        "--strength",
        type=BoundedInteger(1, 400),
        metavar="[1..400]",
        default=300,
        required=False,
        help="""Suppression strength of temporal inconsistencies.
Higher means more aggressive.
\n"""
    )


    # Seeking
    parser.add_argument(
        "-ss",
        "--ss",
        type=str,
        required=False,
        default='',
        help="""Seeks in this input file to position.
HOURS:MM:SS.MILLISECONDS
Refer to https://ffmpeg.org//ffmpeg.html#Main-options
and https://ffmpeg.org//ffmpeg-utils.html#time-duration-syntax
\n"""
    )
    parser.add_argument(
        "-t",
        "--t",
        type=str,
        required=False,
        default='',
        help="""Limit the duration of data read from the input file.
HOURS:MM:SS.MILLISECONDS
Refer to https://ffmpeg.org//ffmpeg.html#Main-options
\n"""
    )
    parser.add_argument(
        "-to",
        "--to",
        type=str,
        required=False,
        default='',
        help="""Stop reading the input at position.
HOURS:MM:SS.MILLISECONDS
--to and --t are mutually exclusive and --t has priority.
Refer to https://ffmpeg.org//ffmpeg.html#Main-options"
\n"""
    )

    # Encoder
    parser.add_argument(
        "-vcodec",
        "--encoder",
        choices=['h264', 'h265', 'ffv1', 'vp9'],
        default='h264',
        required=False,
        help="""Video encoder
\n"""
    )
    parser.add_argument(
        "-pix_fmt",
        "--pix_fmt",
        default='yuv420p',
        required=False,
        help="""FFMpeg pix_fmt. rgb/yuv only.
recommended: yuv420p, yuv420p10le, yuv420p12le
\n"""
    )

    parser.add_argument(
        "-preset",
        "--preset",
        choices=[
            'ultrafast',
            'superfast',
            'veryfast',
            'faster',
            'fast',
            'medium',
            'slow',
            'slower',
            'veryslow',
        ],
        default='',
        required=False,
        help="""FFmpeg video preset
\n"""
    )

    parser.add_argument(
        "-crf",
        "--crf",
        type=int,
        default=-1,
        required=False,
        help="""FFmpeg CRF
\n"""
    )

    parser.add_argument(
        "-tune",
        "--tune",
        choices=[
            'film',
            'animation',
            'grain',
            'stillimage',
            'fastdecode',
            'zerolatency',
        ],
        default='',
        help="""FFmpeg tune setting
\n"""
    )

    parser.add_argument(
        "-ffmpeg_args",
        "--ffmpeg_args",
        type=str,
        default="",
        help="""FFmpeg custom options.
\n"""
    )


    # Benchmark
    parser.add_argument(
        "--benchmark",
        action="store_true",
        required=False,
        help="""FFmpeg benchmark
\n"""
    )

    # Logger
    parser.add_argument(
        "--log",
        action="store_true",
        required=False,
        default=False,
        help="""(DEV) log in ./logs
\n"""
    )

    # Just for debug
    parser.add_argument(
        "--debug",
        action="store_true",
        required=False,
        default=False,
        help="""(DEV) display additionnal info
\n"""
    )

    arguments: Namespace = parser.parse_args()

    return arguments
