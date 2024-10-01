from copy import deepcopy
import os
import sys

from argparse import Namespace
import numpy as np
from pprint import pprint
import signal
import subprocess


from utils.media import MediaInfo, VideoInfo, extract_media_info, get_media_info
from utils.path_utils import absolute_path, is_access_granted, path_split
from utils.p_print import *
from utils.arg_parse import arg_parse
from utils.encoder import VideoEncoderParams, arguments_to_encoder_params, generate_ffmpeg_encoder_cmd
from utils.pxl_fmt import PIXEL_FORMAT



def main():

    # Parse arguments
    arguments: Namespace = arg_parse()


    # Check arguments validity
    in_media_path: str = absolute_path(arguments.input)
    if not os.path.isfile(in_media_path):
        sys.exit(red(f"Error: invalid input file: {in_media_path}"))

    out_media_path: str = absolute_path(arguments.output)
    if not arguments.output:
        dirname, basename, extension = path_split(in_media_path)
        out_media_path: str = os.path.join(
            dirname, f"{basename}{arguments.suffix}{extension}"
        )
    if out_media_path == in_media_path:
        sys.exit(red(f"Error: output file must be different from input file: {out_media_path}"))

    out_dir: str = path_split(out_media_path)[0]
    if not is_access_granted(out_dir, 'w'):
        sys.exit(red(f"Error: no write access to {out_dir}"))

    print(lightcyan(f"Input video file:"), f"{in_media_path}")
    print(lightcyan(f"Output video file:"), f"{out_media_path}")


    # Open media file
    in_media_path: str = absolute_path(arguments.input)
    in_media_info: MediaInfo | None = None
    try:
        in_media_info = extract_media_info(in_media_path)
    except:
        # debug:
        pprint(get_media_info(in_media_path))
        sys.exit(f"[E] {in_media_path} is not a valid input media file")
    if arguments.debug:
        print(lightcyan("FFmpeg media info:"))
        pprint(get_media_info(in_media_path))
        print(lightcyan("Input media info:"))
        pprint(in_media_info)
    in_video_info: VideoInfo = in_media_info['video']
    in_video_info['filepath'] = in_media_path

    vs_video_info: VideoInfo = deepcopy(in_video_info)
    vs_video_info['filepath'] = out_media_path

    # Parse arguments and create a dict of params
    e_params: VideoEncoderParams = arguments_to_encoder_params(
        arguments=arguments,
        video_info=vs_video_info
    )
    if arguments.debug:
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
    })
    if arguments.debug:
        print(lightcyan("Video info after vs script:"))
        pprint(vs_video_info)


    # VSpipe command
    vspipe_exe: str = os.path.join(".", "external", "vspython", "VSpipe.exe")
    vs_command: list[str] = [
        vspipe_exe,
        "vstf.vpy",
        "--arg", f"input_fp=\"{arguments.input}\"",
        "--arg", f"tr={arguments.radius}",
        "--arg", f"strength={arguments.strength}",
        "--arg", f"pix_fmt={vs_out_pix_fmt}",
        "-",
    ]
    if arguments.debug:
        print(lightcyan("Vs command:"))
        print(lightgreen(' '.join(vs_command)))


    # Encoder command
    encoder_command: list[str] = generate_ffmpeg_encoder_cmd(
        video_info=vs_video_info,
        params=e_params,
        in_media_info=in_media_info,
    )
    if arguments.debug:
        print(lightcyan("Encoder command:"))
        print(lightgreen(' '.join(encoder_command)))


    # Encoder process
    encoder_subprocess: subprocess.Popen | None = None
    try:
        encoder_subprocess = subprocess.Popen(
            encoder_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except Exception as e:
        sys.exit(red(f"[E] Unexpected error: {type(e)}"))
    if encoder_subprocess is None:
        sys.exit(red(f"[E] Encoder process is not started"))


    # Vs process
    # Clean environment for vspython
    vs_env = os.environ.copy()
    for k, v in vs_env.copy().items():
        if "conda" in k.lower():
            del vs_env[k]

        # TODO: to be verified:
        elif "python" in v.lower():
            del vs_env[k]
            print(f"PYTHON in variable: {v}")
    vs_subprocess: subprocess.Popen | None = None
    try:
        vs_subprocess = subprocess.Popen(
            vs_command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=vs_env,
        )
    except Exception as e:
        print(f"[E] Unexpected error: {type(e)}", flush=True)

    # Characteristics of the pipe
    frame_count: int = in_video_info['frame_count']
    h, w = in_video_info['shape'][:2]
    in_nbytes: int = h * w * vs_video_info['bpp'] // 8
    if arguments.debug:
        print(lightcyan("Pipe in:"))
        print(f"  shape: {w}x{h}")
        print(f"  nb of bytes: {in_nbytes}")
        print(f"  frame_count: {frame_count}")

    frame: bytes = None
    line: str = ''
    os.set_blocking(encoder_subprocess.stdout.fileno(), False)
    for _ in range(frame_count):
        # print(f"reading frame no. {i}", end="\r")
        frame: bytes = vs_subprocess.stdout.read(in_nbytes)
        if frame is None:
            print(red("None"))
        encoder_subprocess.stdin.write(frame)
        line = encoder_subprocess.stdout.readline().decode('utf-8')
        if line:
            print(line.strip(), end='\r')
    print()

    stdout_b: bytes | None = None
    stderr_b: bytes | None = None
    try:
        # Arbitrary timeout value
       stdout_b, stderr_b = encoder_subprocess.communicate(timeout=10)
    except:
        encoder_subprocess.kill()
        return False

    if stdout_b is not None:
        stdout = stdout_b.decode('utf-8)')
        if stdout:
            print(stdout)

    if stderr_b is not None:
        stderr = stderr_b.decode('utf-8)')
        if stderr:
            print(stderr)

    print(lightcyan("Done."))
    return


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()


