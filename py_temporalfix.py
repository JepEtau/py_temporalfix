from argparse import Namespace
from copy import deepcopy
import logging
from queue import Queue
import time
import numpy as np
import os
from pprint import pformat, pprint
import signal
import subprocess
import sys

from utils.arg_parse import arg_parse
from utils.decoder import DecoderThread, generate_ffmpeg_decoder_cmd
from utils.encoder import (
    EncoderThread,
    arguments_to_encoder_params,
    generate_ffmpeg_encoder_cmd,
    VideoEncoderParams,
)
from utils.logger import logger
from utils.media import (
    MediaInfo,
    VideoInfo,
    extract_media_info,
    get_media_info,
)
from utils.path_utils import (
    absolute_path,
    is_access_granted,
    os_path_basename,
    path_split,
)
from utils.pxl_fmt import PIXEL_FORMAT
from utils.p_print import *
from utils.time_conversions import frame_rate_to_str
from utils.tools import check_missing_tools
from utils.vsscript import VsThread, extract_info_from_vs_script


def main():
    # Verify the installation
    root_dir: str = os.path.dirname(os.path.abspath(__file__))
    vspipe_exe: str = absolute_path(
        os.path.join(root_dir, "external", "vspython", "VSPipe.exe")
    )
    if sys.platform == "linux":
        vspipe_exe = "/usr/bin/vspipe"

    missing_tools: list[str] = check_missing_tools(
        tools={"VSPipe": vspipe_exe}
    )
    if missing_tools:
        sys.exit(red(f"""
Error: missing tools: {', '.join(missing_tools)}.
Please install these dependencies (refer to the documentation).
        """))

    # Parse arguments
    arguments: Namespace = arg_parse()

    # Check arguments validity
    in_media_path: str = absolute_path(arguments.input)
    if not os.path.isfile(in_media_path):
        sys.exit(red(f"Error: missing input file {in_media_path}"))

    # Use output filepath before verification because it uses the
    #   output directory to store the log file
    out_media_path: str = absolute_path(arguments.output)
    if not arguments.output:
        dirname, basename, extension = path_split(in_media_path)
        out_media_path: str = os.path.join(
            dirname, f"{basename}{arguments.suffix}_{arguments.t_radius}_{arguments.strength}{extension}"
        )
    if out_media_path == in_media_path:
        sys.exit(red(f"Error: output file must be different from input file: {out_media_path}"))

    out_dir: str = path_split(out_media_path)[0]
    if not os.path.isdir(out_dir):
        out_dir_parent = absolute_path(os.path.join(out_dir, os.pardir))
        try:
            os.makedirs(out_dir, exist_ok=True)
        except:
            sys.exit(red(f"Error: no write access to {out_dir_parent}"))
    if not is_access_granted(out_dir, 'w'):
        sys.exit(red(f"Error: no write access to {out_dir}"))

    debug: bool = arguments.debug

    if arguments.log:
        log_dir, log_basename = path_split(out_media_path)[:2]
        log_filepath: str = os.path.join(out_dir, f"{log_basename}.log")
        logger.addHandler(
            logging.FileHandler(log_filepath, mode="w")
        )
        logger.setLevel("DEBUG")
        print(
            lightcyan(f"Log saved in"), log_dir,
            lightcyan("as:"), f"{log_basename}.log"
        )
    else:
        logger.setLevel("WARNING")

    logger.debug(f"Python executable dir: {sys.executable}")
    logger.debug(f"arguments: {sys.argv}")

    print(lightcyan(f"Input video file:"), f"{in_media_path}")
    logger.debug(f"input: {in_media_path}")

    # Open media file
    in_media_path: str = absolute_path(arguments.input)
    in_media_info: MediaInfo | None = None
    try:
        in_media_info = extract_media_info(in_media_path)
    except:
        sys.exit(f"[E] {in_media_path} is not a valid input media file")
    if debug:
        print(lightcyan("FFmpeg media info:"))
        pprint(get_media_info(in_media_path))
        print(lightcyan("Input media info:"))
        pprint(in_media_info)
    logger.debug(f"FFmpeg media info:\n{pformat(get_media_info(in_media_path))}")
    logger.debug(f"Input media info:\n{pformat(in_media_info)}")
    in_video_info: VideoInfo = in_media_info['video']
    in_video_info['filepath'] = in_media_path

    frame_count_str: str = f"    {in_video_info['frame_count']} frames"
    in_h, in_w = in_video_info['shape'][:2]
    dim_str: str = f", {in_w}x{in_h}"
    frame_rate_str: str = f", {frame_rate_to_str(in_video_info['frame_rate_r'])} fps"
    pix_fmt_str: str = f", {in_video_info['pix_fmt']}"
    _sar: tuple[int] = in_video_info['sar']
    sar_str: str = f", SAR {':'.join(map(str, _sar))}" if _sar[0] / _sar[1] != 1 else ""
    _dar: tuple[int] = in_video_info['dar']
    dar_str: str = f", DAR {':'.join(map(str, _dar))}" if _dar[0] / _dar[1] != 1 else ""
    in_vi_str: str = "".join((frame_count_str, dim_str, frame_rate_str, pix_fmt_str, sar_str, dar_str))
    print(in_vi_str)
    logger.debug(f"input video format: {in_vi_str}")

    vs_video_info: VideoInfo = deepcopy(in_video_info)
    vs_video_info['filepath'] = out_media_path

    print(lightcyan(f"Output video file:"), f"{out_media_path}")
    logger.debug(f"output: {out_media_path}")

    # Parse arguments and create a dict of params
    e_params: VideoEncoderParams = arguments_to_encoder_params(
        arguments=arguments,
        video_info=vs_video_info
    )
    out_media_path = e_params.filepath
    print(lightcyan(f"Output video file:"), f"{out_media_path}")
    logger.debug(f"output: {out_media_path}")
    if debug:
        print(lightcyan("Encoder params:"))
        pprint(e_params)


    # Script output
    vs_out_pix_fmt: str = 'yuv420p'
    if e_params.pix_fmt != 'yuv420p':
        vs_out_pix_fmt = 'yuv444p16le'
    vs_c_order = 'yuv'
    vs_video_info.update({
        'dtype': np.uint8,
        'bpp': PIXEL_FORMAT[vs_out_pix_fmt]['pipe_bpp'],
        'c_order': vs_c_order,
        'pix_fmt': vs_out_pix_fmt,
        'metadata': {
            'vs_temporal_fix': f"tr={arguments.t_radius}, strength={arguments.strength}"
        }
    })

    if debug:
        print(lightcyan("Video info after vs script:"))
        pprint(vs_video_info)
    logger.debug(f"VS video info:\n{pformat(vs_video_info)}")

    # VSpipe command
    in_h, in_w = in_video_info['shape'][:2]
    vs_command: list[str] = [
        vspipe_exe,
        os.path.join(root_dir, "vstf.vpy"),
        # "--arg", f"input_fp=\"{arguments.input}\"",
        "--arg", f"width={in_w}",
        "--arg", f"height={in_h}",
        "--arg", f"tr={arguments.t_radius}",
        "--arg", f"strength={arguments.strength}",
        # "--arg", f"pix_fmt={vs_out_pix_fmt}",
        "-",
    ]
    if debug:
        print(lightcyan("VS command:"))
        print(lightgreen(' '.join(vs_command)))
    logger.debug(f"VS command:\n{' '.join(vs_command)}")


    # Encoder command
    logger.debug(f"Encoder params:\n{pformat(e_params)}")


    # Clean environment for vspython
    # vs_path: list[str] = []
    forbidden_names: tuple[str] = (
        'python',
        'conda',
        'vapoursynth',
        'ffmpeg',
    )

    # Create path used by vs subprocess
    vs_path: list[str] = []
    sep: str = ";"
    if sys.platform == "win32":
        for dir in ("Scripts", "vs-scripts", "vs-plugins", ""):
            vs_path.insert(0, os.path.abspath(
                os.path.join(root_dir, "external", "vspython", dir)
            ))

    elif sys.platform == "linux":
        for dir in (
            "/usr/lib/x86_64-linux-gnu/vapoursynth",
            "/usr/lib/bin"
        ):
            vs_path.insert(0, dir)
        sep = ':'

    vs_path.insert(0, root_dir)

    # Clean environnment for vs
    vs_env = os.environ.copy()
    del vs_env['PATH']
    for k, v in vs_env.copy().items():
        k_lower, v_lower = k.lower(), v.lower()
        for n in forbidden_names:
            if n in k_lower:
                try:
                    del vs_env[k]
                    logger.debug(f"removing: {k}: {v}")
                except:
                    pass

            if n in v_lower:
                try:
                    del vs_env[k]
                    logger.debug(f"removing: {k}: {v}")
                except:
                    pass
    vs_env['PATH'] = sep.join(vs_path)

    logger.debug(f"Environment:\n{pformat(vs_env)}")
    # Environnment
    # if arguments.log or debug:
    #     extract_info_from_vs_script(vs_command=vs_command, vs_env=vs_env)

    # if debug or arguments.log:
    #     print(lightcyan("Encoder command:"))
    #     print(lightgreen(' '.join(encoder_command)))


    # Characteristics of the pipe
    frame_count: int = in_video_info['frame_count']
    in_h, in_w = in_video_info['shape'][:2]
    in_nbytes: int = in_h * in_w * vs_video_info['bpp'] // 8
    if debug:
        print(lightcyan("Pipe in:"))
        print(f"  shape: {in_w}x{in_h}")
        print(f"  nb of bytes: {in_nbytes}")
        print(f"  nb of frames: {frame_count}")


    dec_nbytes: int = in_nbytes
    # if debug or arguments.log:
    print(lightcyan("VS pipe in:"))
    print(f"  shape: {in_w}x{in_h}")
    print(f"  nb of bytes: {dec_nbytes}")
    print(f"  nb of frames: {frame_count}")

    # os.set_blocking(dec_subprocess.stdout.fileno(), False)
    # os.set_blocking(encoder_subprocess.stdout.fileno(), False)
    # os.set_blocking(vs_subprocess.stderr.fileno(), False)
    print(f"Processing:")

    # Decoder
    d_queue: Queue = Queue(maxsize=22)
    e_queue: Queue = Queue(maxsize=22)
    d_thread: DecoderThread = DecoderThread(
        queue=d_queue,
        in_video_info=in_video_info,
        out_video_info=vs_video_info
    )
    vs_thread: VsThread = VsThread(
        in_queue=d_queue,
        out_queue=e_queue,
        vs_command=vs_command,
        vs_env=vs_env
    )
    e_thread: EncoderThread = EncoderThread(
        queue=e_queue,
        params=e_params,
        in_video_info=vs_video_info,
        in_media_info=in_media_info,
    )

    vs_thread.start()
    d_thread.start()
    e_thread.start()

    while not vs_thread.is_ready():
        time.sleep(0.1)

    while True:
        try:
            e_queue.put(vs_thread.stdout.read(in_nbytes))
        except Exception as e:
            print("exception")
            break

    while vs_thread.is_alive() and not vs_thread.ended():
        time.sleep(0.05)

    remaining: bytes = vs_thread.remaining_bytes()
    print(f"remaining: {len(remaining)}")
    # remaining_frame_count: int = len(remaining) // dec_nbytes
    if remaining is not None:
        print(yellow(f"sending:"), len(remaining))
        e_queue.put(remaining)
    else:
        print("nothing to send")
    e_queue.put(None)

    print()



    # For evaluation purpose
    # Enable this after validation
    success: bool = True
    if arguments.debug:
        out_vi: VideoInfo = None
        try:
            out_vi: VideoInfo = extract_media_info(out_media_path)['video']
        except:
            success = False

        if out_vi is None or out_vi['frame_count'] != in_video_info['frame_count']:
            logger.debug(f"Number of frames differs")
            success = False

        if success and arguments.log:
            frame_count_str: str = f"    {out_vi['frame_count']} frames"
            in_h, in_w = out_vi['shape'][:2]
            dim_str: str = f", {in_w}x{in_h}"
            frame_rate_str: str = f", {frame_rate_to_str(out_vi['frame_rate_r'])} fps"
            pix_fmt_str: str = f", {out_vi['pix_fmt']}"
            _sar: tuple[int] = out_vi['sar']
            sar_str: str = f", SAR {':'.join(map(str, _sar))}" if _sar[0] / _sar[1] != 1 else ""
            _dar: tuple[int] = out_vi['dar']
            dar_str: str = f", DAR {':'.join(map(str, _dar))}" if _dar[0] / _dar[1] != 1 else ""
            out_vi_str: str = "".join((frame_count_str, dim_str, frame_rate_str, pix_fmt_str, sar_str, dar_str))
            logger.debug(f"output video format: {out_vi_str}")

    if not os.path.isfile(out_media_path) or not success:
        print(red(f"Error: failed to generate {out_media_path}"))
        return

    print(lightcyan("Done."))



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    if sys.platform != 'win32':
        sys.exit(f"Error: {sys.platform} is not a supported platform")
    main()


