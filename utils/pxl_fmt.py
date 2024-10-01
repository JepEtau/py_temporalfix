import re
from .p_print import *


ffmpeg_pixl_fmts: str = """
FLAGS NAME            NB_COMPONENTS BITS_PER_PIXEL BIT_DEPTHS
-----
IO... yuv420p                3             12      8-8-8
IO... yuyv422                3             16      8-8-8
IO... rgb24                  3             24      8-8-8
IO... bgr24                  3             24      8-8-8
IO... yuv422p                3             16      8-8-8
IO... yuv444p                3             24      8-8-8
IO... yuv410p                3              9      8-8-8
IO... yuv411p                3             12      8-8-8
IO... gray                   1              8      8
IO..B monow                  1              1      1
IO..B monob                  1              1      1
I..P. pal8                   1              8      8
IO... yuvj420p               3             12      8-8-8
IO... yuvj422p               3             16      8-8-8
IO... yuvj444p               3             24      8-8-8
IO... uyvy422                3             16      8-8-8
..... uyyvyy411              3             12      8-8-8
IO... bgr8                   3              8      3-3-2
.O..B bgr4                   3              4      1-2-1
IO... bgr4_byte              3              4      1-2-1
IO... rgb8                   3              8      3-3-2
.O..B rgb4                   3              4      1-2-1
IO... rgb4_byte              3              4      1-2-1
IO... nv12                   3             12      8-8-8
IO... nv21                   3             12      8-8-8
IO... argb                   4             32      8-8-8-8
IO... rgba                   4             32      8-8-8-8
IO... abgr                   4             32      8-8-8-8
IO... bgra                   4             32      8-8-8-8
IO... gray16be               1             16      16
IO... gray16le               1             16      16
IO... yuv440p                3             16      8-8-8
IO... yuvj440p               3             16      8-8-8
IO... yuva420p               4             20      8-8-8-8
IO... rgb48be                3             48      16-16-16
IO... rgb48le                3             48      16-16-16
IO... rgb565be               3             16      5-6-5
IO... rgb565le               3             16      5-6-5
IO... rgb555be               3             15      5-5-5
IO... rgb555le               3             15      5-5-5
IO... bgr565be               3             16      5-6-5
IO... bgr565le               3             16      5-6-5
IO... bgr555be               3             15      5-5-5
IO... bgr555le               3             15      5-5-5
..H.. vaapi                  0              0      0
IO... yuv420p16le            3             24      16-16-16
IO... yuv420p16be            3             24      16-16-16
IO... yuv422p16le            3             32      16-16-16
IO... yuv422p16be            3             32      16-16-16
IO... yuv444p16le            3             48      16-16-16
IO... yuv444p16be            3             48      16-16-16
..H.. dxva2_vld              0              0      0
IO... rgb444le               3             12      4-4-4
IO... rgb444be               3             12      4-4-4
IO... bgr444le               3             12      4-4-4
IO... bgr444be               3             12      4-4-4
IO... ya8                    2             16      8-8
IO... bgr48be                3             48      16-16-16
IO... bgr48le                3             48      16-16-16
IO... yuv420p9be             3             13      9-9-9
IO... yuv420p9le             3             13      9-9-9
IO... yuv420p10be            3             15      10-10-10
IO... yuv420p10le            3             15      10-10-10
IO... yuv422p10be            3             20      10-10-10
IO... yuv422p10le            3             20      10-10-10
IO... yuv444p9be             3             27      9-9-9
IO... yuv444p9le             3             27      9-9-9
IO... yuv444p10be            3             48      10-10-10
IO... yuv444p10le            3             48      10-10-10
IO... yuv422p9be             3             18      9-9-9
IO... yuv422p9le             3             18      9-9-9
IO... gbrp                   3             24      8-8-8
IO... gbrp9be                3             27      9-9-9
IO... gbrp9le                3             27      9-9-9
IO... gbrp10be               3             30      10-10-10
IO... gbrp10le               3             30      10-10-10
IO... gbrp16be               3             48      16-16-16
IO... gbrp16le               3             48      16-16-16
IO... yuva422p               4             24      8-8-8-8
IO... yuva444p               4             32      8-8-8-8
IO... yuva420p9be            4             22      9-9-9-9
IO... yuva420p9le            4             22      9-9-9-9
IO... yuva422p9be            4             27      9-9-9-9
IO... yuva422p9le            4             27      9-9-9-9
IO... yuva444p9be            4             36      9-9-9-9
IO... yuva444p9le            4             36      9-9-9-9
IO... yuva420p10be           4             25      10-10-10-10
IO... yuva420p10le           4             25      10-10-10-10
IO... yuva422p10be           4             30      10-10-10-10
IO... yuva422p10le           4             30      10-10-10-10
IO... yuva444p10be           4             40      10-10-10-10
IO... yuva444p10le           4             40      10-10-10-10
IO... yuva420p16be           4             40      16-16-16-16
IO... yuva420p16le           4             40      16-16-16-16
IO... yuva422p16be           4             48      16-16-16-16
IO... yuva422p16le           4             48      16-16-16-16
IO... yuva444p16be           4             64      16-16-16-16
IO... yuva444p16le           4             64      16-16-16-16
..H.. vdpau                  0              0      0
IO... xyz12le                3             36      12-12-12
IO... xyz12be                3             36      12-12-12
IO... nv16                   3             16      8-8-8
..... nv20le                 3             20      10-10-10
..... nv20be                 3             20      10-10-10
IO... rgba64be               4             64      16-16-16-16
IO... rgba64le               4             64      16-16-16-16
IO... bgra64be               4             64      16-16-16-16
IO... bgra64le               4             64      16-16-16-16
IO... yvyu422                3             16      8-8-8
IO... ya16be                 2             32      16-16
IO... ya16le                 2             32      16-16
IO... gbrap                  4             32      8-8-8-8
IO... gbrap16be              4             64      16-16-16-16
IO... gbrap16le              4             64      16-16-16-16
..H.. qsv                    0              0      0
..H.. mmal                   0              0      0
..H.. d3d11va_vld            0              0      0
..H.. cuda                   0              0      0
IO... 0rgb                   3             24      8-8-8
IO... rgb0                   3             24      8-8-8
IO... 0bgr                   3             24      8-8-8
IO... bgr0                   3             24      8-8-8
IO... yuv420p12be            3             18      12-12-12
IO... yuv420p12le            3             18      12-12-12
IO... yuv420p14be            3             21      14-14-14
IO... yuv420p14le            3             21      14-14-14
IO... yuv422p12be            3             24      12-12-12
IO... yuv422p12le            3             24      12-12-12
IO... yuv422p14be            3             28      14-14-14
IO... yuv422p14le            3             28      14-14-14
IO... yuv444p12be            3             36      12-12-12
IO... yuv444p12le            3             36      12-12-12
IO... yuv444p14be            3             42      14-14-14
IO... yuv444p14le            3             42      14-14-14
IO... gbrp12be               3             36      12-12-12
IO... gbrp12le               3             36      12-12-12
IO... gbrp14be               3             42      14-14-14
IO... gbrp14le               3             42      14-14-14
IO... yuvj411p               3             12      8-8-8
I.... bayer_bggr8            3              8      2-4-2
I.... bayer_rggb8            3              8      2-4-2
I.... bayer_gbrg8            3              8      2-4-2
I.... bayer_grbg8            3              8      2-4-2
I.... bayer_bggr16le         3             16      4-8-4
I.... bayer_bggr16be         3             16      4-8-4
I.... bayer_rggb16le         3             16      4-8-4
I.... bayer_rggb16be         3             16      4-8-4
I.... bayer_gbrg16le         3             16      4-8-4
I.... bayer_gbrg16be         3             16      4-8-4
I.... bayer_grbg16le         3             16      4-8-4
I.... bayer_grbg16be         3             16      4-8-4
IO... yuv440p10le            3             20      10-10-10
IO... yuv440p10be            3             20      10-10-10
IO... yuv440p12le            3             24      12-12-12
IO... yuv440p12be            3             24      12-12-12
IO... ayuv64le               4             64      16-16-16-16
..... ayuv64be               4             64      16-16-16-16
..H.. videotoolbox_vld       0              0      0
IO... p010le                 3             15      10-10-10
IO... p010be                 3             15      10-10-10
IO... gbrap12be              4             48      12-12-12-12
IO... gbrap12le              4             48      12-12-12-12
IO... gbrap10be              4             40      10-10-10-10
IO... gbrap10le              4             40      10-10-10-10
..H.. mediacodec             0              0      0
IO... gray12be               1             12      12
IO... gray12le               1             12      12
IO... gray10be               1             10      10
IO... gray10le               1             10      10
IO... p016le                 3             24      16-16-16
IO... p016be                 3             24      16-16-16
..H.. d3d11                  0              0      0
IO... gray9be                1              9      9
IO... gray9le                1              9      9
IO... gbrpf32be              3             96      32-32-32
IO... gbrpf32le              3             96      32-32-32
IO... gbrapf32be             4            128      32-32-32-32
IO... gbrapf32le             4            128      32-32-32-32
..H.. drm_prime              0              0      0
..H.. opencl                 0              0      0
IO... gray14be               1             14      14
IO... gray14le               1             14      14
IO... grayf32be              1             32      32
IO... grayf32le              1             32      32
IO... yuva422p12be           4             36      12-12-12-12
IO... yuva422p12le           4             36      12-12-12-12
IO... yuva444p12be           4             48      12-12-12-12
IO... yuva444p12le           4             48      12-12-12-12
IO... nv24                   3             24      8-8-8
IO... nv42                   3             24      8-8-8
..H.. vulkan                 0              0      0
..... y210be                 3             20      10-10-10
IO... y210le                 3             20      10-10-10
IO... x2rgb10le              3             30      10-10-10
..... x2rgb10be              3             30      10-10-10
IO... x2bgr10le              3             30      10-10-10
..... x2bgr10be              3             30      10-10-10
IO... p210be                 3             20      10-10-10
IO... p210le                 3             20      10-10-10
IO... p410be                 3             30      10-10-10
IO... p410le                 3             30      10-10-10
IO... p216be                 3             32      16-16-16
IO... p216le                 3             32      16-16-16
IO... p416be                 3             48      16-16-16
IO... p416le                 3             48      16-16-16
IO... vuya                   4             32      8-8-8-8
I.... rgbaf16be              4             64      16-16-16-16
I.... rgbaf16le              4             64      16-16-16-16
IO... vuyx                   3             24      8-8-8
IO... p012le                 3             18      12-12-12
IO... p012be                 3             18      12-12-12
..... y212be                 3             24      12-12-12
IO... y212le                 3             24      12-12-12
....B xv30be                 3             30      10-10-10
IO... xv30le                 3             30      10-10-10
..... xv36be                 3             36      12-12-12
IO... xv36le                 3             36      12-12-12
..... rgbf32be               3             96      32-32-32
..... rgbf32le               3             96      32-32-32
..... rgbaf32be              4            128      32-32-32-32
..... rgbaf32le              4            128      32-32-32-32
IO... p212be                 3             24      12-12-12
IO... p212le                 3             24      12-12-12
IO... p412be                 3             36      12-12-12
IO... p412le                 3             36      12-12-12
IO... gbrap14be              4             56      14-14-14-14
IO... gbrap14le              4             56      14-14-14-14
..H.. d3d12                  0              0      0
"""

_pixel_formats: dict[str, dict[str, int | bool]] = {}
if (formats := re.findall(
        re.compile(r"[IOHBP.]{5}\s+([a-z_\d]+)\s+([1234]{1})\s+(\d+)\s+([\d-]+)"),
        ffmpeg_pixl_fmts
    )
):
    formats: list[str, str, str, str]
    for f in formats:
        k, nc, bpp, bit_depths = f
        c_order: str = ''
        if (
            'a' in k
            or 'be' in k
        ):
            # not supported
            c_order = ''
        elif 'rgb' in k:
            c_order = 'rgb'
        elif 'gbr' in k:
            c_order = 'gbr'
        elif 'bgr' in k:
            c_order = 'bgr'
        elif 'yuv' in k:
            c_order = 'yuv'
        elif 'gray' in k:
            c_order = 'gray'

        storage_bpp = max(list(map(int, bit_depths.split('-'))))
        _pixel_formats[k] = {
            'c': int(nc),
            'bpp': storage_bpp,
            'pipe_bpp': int(bpp),
            'c_order': c_order,
            'supported': True if c_order in ('rgb', 'bgr', 'gbr', 'yuv') else False,
        }
else:
    raise ValueError(red("Failed extracting pixel format"))

# Debug
# for k, v in _pixel_formats.items():
#     if v['supported']:
#         print(lightgreen(k))
#     else:
#         print(lightgrey(k))

PIXEL_FORMAT = _pixel_formats
