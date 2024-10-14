# py_temporalfix

The objective is to use a separate portable vs/python interpretor to run the [vs_temporalfix](https://github.com/pifroggi/vs_temporalfix) script developped by [pifroggi](https://github.com/pifroggi)

_This project is experimental_
&nbsp;

## Table of Contents
- [Basic usage](#Basic-usage)
- [Requirements](#Requirements)
- [Installation](#Installation)
- [Usage](#Usage)
- [Manual installation](#Manual-installation)
- [Troubleshooting](#Troubleshooting)

&nbsp;


## Basic usage
`python py_temporalfix.py --input input_video.mkv --output output_video.mkv --t_radius 6 --strength 300`

&nbsp;

_Note: when the output container is Matroska (.mkv), the strength and temporal radius values are added to the output video metadata._
_Note2: it's possible to not specify the output filepath: a suffix will be automatically added to the filename_

## Requirements
- Windows 11
- Python 3.12

&nbsp;

## Installation

> [!TIP]
> It is recommended, but not required to use the [miniconda distribution](https://docs.anaconda.com/free/miniconda/index.html) to create a separate python environment from the system python.

- (Optional) **Create a conda environment**
    ```
    conda create -n pytf python==3.12
    conda activate pytf
    ```

- **Clone or download the repository**  
Clone this repository: `git clone https://github.com/JepEtau/py_temporalfix.git`  
Or download/extract the zip file.


- **Dependencies and external tools**  
This will install the required python packages. FFmpeg and a vs (portable) environnment will also be downloaded to the `external` directory.
    ```sh
    python install_deps.py
    ```

> [!WARNING]
> As this script is highly experimental, in case of any problem with the installation, follow these [instructions](#Manual-installation). I won't provide any help with vs/python. Never.

- (Optional) **Update vs_temporal_fix script**: download the script from the [author's github repo](https://github.com/pifroggi/vs_temporalfix) to the root of this project.

&nbsp;

## Usage

`python py_temporalfix.py --help`

### Input, output
| Option&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;| Description |
| :--- | :--- |
| `--input` | Path to the input video file  |
| `--output`| Path to the output video file |
| `--suffix`| Suffix used when no output filename is specified (default:  `_fixed_<t_radius>_<strength>`)|


### Parameters passed to the script.
For more details: [vs_temporalfix](https://github.com/pifroggi/vs_temporalfix)

| Option&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; |  Default | Description |
| :--- | :---: | :--- |
| `--t_radius` | `6` | The temporal radius sets the number of frames to average over. Higher means more stable. There is a big drop in performance for tr > 6 |
| `--strength` | `400` | Suppression strength of temporal inconsistencies. Higher means more aggressive. If you get blending/ghosting on small movements or blocky artifacts, reduce this. |


### Video encoding
Parameters passed to the encoder. Refer to the [FFmpeg documentation](https://ffmpeg.org/ffmpeg-all.html)

| Option&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; |   Default  | Description
| :--- | :---: | :--- |
| `--encoder`   | `h264`    |  `h264`, `h265`, `ffv1`, `vp9`|
| `--pix_fmt`   | `yuv420p` |  rgb or yuv formats  |
| `--preset`    |  -         | `ultrafast`, `superfast`, `veryfast`, `faster`, `fast`, `medium`, `slow`, `slower`, `veryslow`   |
| `--crf`       |    `23`|  0 to 51  |
| `--tune`      |  `film`, `animation`, `grain`, `stillimage`, `fastdecode`, `zerolatency`  |
| `--ffmpeg_args` | `""` | Used to pass customized arguments to the encoder (FFmpeg). Override the previous options. This option must be double quoted. Example: `--ffmpeg_args "-preset veryfast"`|


### Not yet supported:
| Argument  | Format        | Description           |
| :--- | :---: | :--- |
| `-ss`     | hh:mm:ss.ms   | seek start            |
| `-t`      | hh:mm:ss.ms   | duration              |
| `-to`     | hh:mm:ss.ms   | position              |

&nbsp;

## Manual installation

- Python packages
    ```bash
    pip install --upgrade pip
    pip install -r .\requirements.txt
    ```

- Download the following zip files
    + Download and extract content of [FFmpeg](https://github.com/JepEtau/external_rehost/releases/download/external/ffmpeg_win32_x64.zip) to `external/ffmpeg`
    + Download and extract content of [vspython](https://github.com/JepEtau/external_rehost/releases/download/external/vspython.zip) to `external/vspython`

Note: in case of any problem with vspython, create a portable python env and populate this env with vspipe.
     
&nbsp;

## Troubleshooting

Append `--log` to the command line. The script:  
- parses the script and display some info
- displays the encoder command line
- creates a log file in the output directory
Please attach this log when reporting an issue
