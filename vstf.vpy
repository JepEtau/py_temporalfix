import os
import sys
from typing import Literal
for subd in ("Scripts", "vs-scripts", "vs-plugins", ""):
    sys.path.insert(0, os.path.abspath(os.path.join("external", "vspython", subd)))
sys.path.insert(0, os.path.abspath(os.path.join(".")))
from multiprocessing import cpu_count
import vapoursynth as vs
core = vs.core
core.num_threads = int(cpu_count() - 2)
core.max_cache_size = 20000
from vs_temporalfix import vs_temporalfix

input_fp: str
# clip = core.ffms2.Source(source=input_fp.replace("\"", ""), cache=0)
clip = core.bs.VideoSource(source=input_fp.replace("\"", ""), cachemode = 0)
# clip = clip.std.SetFrameProps(_Matrix=vs.MATRIX_BT709)


strength: int
tr: int
if clip.format != vs.YUV444P16:
    clip = core.resize.Point(clip, format=vs.YUV444P16, matrix_s="709", range_s="limited")
clip = vs_temporalfix(
    clip,
    strength=int(strength),
    tr=int(tr),
    debug=False
)

pix_fmt: Literal['yuv420p', 'yuv444p16le']
if pix_fmt == 'yuv444p16le' and clip.format != vs.YUV444P16:
    clip = core.resize.Bicubic(clip, format=vs.YUV444P16, matrix_s="709", range_s="limited")

if pix_fmt == 'yuv420p' and clip.format != vs.YUV420P8:
    clip = core.resize.Bicubic(clip, format=vs.YUV420P8, matrix_s="709", range_s="limited")

clip.set_output()
