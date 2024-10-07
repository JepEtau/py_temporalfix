from datetime import (
    datetime,
    timedelta,
)
import math
from typing import TypeAlias


FrameRate: TypeAlias = float | int | tuple[int, int]

def frame_rate_to_str(frame_rate: FrameRate) -> str:
    if (
        isinstance(frame_rate, int)
        or isinstance(frame_rate, float) and int(frame_rate) == frame_rate
    ):
        return f"{int(frame_rate)}"

    return (
        f"{frame_rate[0]/frame_rate[1]:.02f}"
        if frame_rate[1] > 1
        else f"{frame_rate[0]}"
    )


def frame_to_s(no: int, frame_rate: FrameRate) -> int:
    if isinstance(frame_rate, tuple | list):
        return float(no * frame_rate[1]) / float(frame_rate[0])
    return float(no) / float(frame_rate)


def frame_to_ms(no: int, frame_rate: FrameRate) -> int:
    return 1000. * frame_to_s(no, frame_rate)


def frame_to_sexagesimal(no: int, frame_rate: FrameRate) -> str:
    """This function returns an approximate segaxesimal value.
        the ms are rounded to the near integer value.
        FFmpeg '-ss' option uses rounded ms
    """
    s: float
    if isinstance(frame_rate, tuple | list):
        s = (float(no * frame_rate[1])) / float(frame_rate[0])
    else:
        s = float(no) / float(frame_rate)
    frac, s = math.modf(s)
    return f"{timedelta(seconds=int(s))}.{int(1000 * frac):03}"


def ms_to_frame(ms: float, frame_rate: FrameRate) -> int:
    if isinstance(frame_rate, tuple | list):
        return int((ms * frame_rate[0]) / (1000. * frame_rate[1]))
    return int((ms * frame_rate) / 1000.)


def s_to_sexagesimal(s: float) -> int:
    frac, s = math.modf(s)
    return f"{timedelta(seconds=int(s))}.{int(1000 * frac):03}"


def current_datetime_str() -> str:
    return datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")


def reformat_datetime(date_str: str) -> str | None:
    """Returns the datetime to a string which can be used as a filename"""
    date_format = "%a, %d %b %Y %H:%M:%S GMT"
    try:
        d = datetime.strptime(date_str, date_format)
    except:
        d_str: str = date_str
        for c in (' ', ',', ':', ','):
            d_str = d_str.replace(c, '_')
        return d_str
    return d.strftime("%Y-%m-%d_%H-%M-%S")


if __name__ == "__main__":
    fps = 25
    frame_no = 100
    s = 3.5

    sexagesimal = frame_to_sexagesimal(frame_no, fps)
    print(f"frame to sexagesimal: {sexagesimal}")

    sexagesimal = s_to_sexagesimal(s)
    print(f"seconds to sexagesimal: {sexagesimal}")

