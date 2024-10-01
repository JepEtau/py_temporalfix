from enum import IntEnum


class ColorCode(IntEnum):
    red = 31
    green = 32
    orange = 33
    blue = 34
    purple = 35
    cyan = 36
    lightgrey = 37
    darkgrey = 90
    lighred = 91
    lightgreen = 92
    yellow = 93
    lightblue = 94
    pink = 95
    lightcyan = 96


def _color_str_template(color:ColorCode) -> str:
    return "\033[%dm{}\033[00m" % (color.value)

def orange(*values: object) -> str:
    return _color_str_template(ColorCode.orange).format(values[0])

def red(*values: object) -> str:
    return _color_str_template(ColorCode.red).format(values[0])

def lightcyan(*values: object) -> str:
    return _color_str_template(ColorCode.lightcyan).format(values[0])

def lightgreen(*values: object) -> str:
    return _color_str_template(ColorCode.lightgreen).format(values[0])

def purple(*values: object) -> str:
    return _color_str_template(ColorCode.purple).format(values[0])

def blue(*values: object) -> str:
    return _color_str_template(ColorCode.blue).format(values[0])

def cyan(*values: object) -> str:
    return _color_str_template(ColorCode.cyan).format(values[0])

def lightgrey(*values: object) -> str:
    return _color_str_template(ColorCode.lightgrey).format(values[0])

def darkgrey(*values: object) -> str:
    return _color_str_template(ColorCode.darkgrey).format(values[0])

def yellow(*values: object) -> str:
    return _color_str_template(ColorCode.yellow).format(values[0])

def green(*values: object) -> str:
    return _color_str_template(ColorCode.green).format(values[0])

__all__ = [
    "blue",
    "darkgrey",
    "green",
    "lightcyan",
    "lightgreen",
    "lightgrey",
    "orange",
    "purple",
    "red",
    "yellow",
    "cyan",
]
