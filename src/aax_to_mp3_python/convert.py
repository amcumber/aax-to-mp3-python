import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import click

"""
See https://wphelp365.com/blog/ultimate-guide-downloading-converting-aax-mp3/ 
on how to use.
Step 3 + 4 will get activation bytes. 

Example:
python convert.py -i "The Tower of the Swallow.aax" -a xxxxxx
where -a is the activation code
"""


def get_chapters(file):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise FileNotFoundError("ffprobe not found!")
    cmd = [
        ffprobe,
        "-show_chapters",
        "-loglevel",
        "error",
        "-print_format",
        "json",
        file,
    ]
    output = subprocess.check_output(cmd, universal_newlines=True)
    chapters = json.loads(output)
    return chapters


# def fix_file_end(file: Path, suffix="Chapter"):
#     ft = file.suffix
#     *front, i_ch = file.stem.split('_')
#     idx = int(i_ch) if i_ch.isnumeric() else i_ch
#     new_idx = f{val:>03}
#     front.append(new_idx)
#     new_name = '_'.join(front)
#     raise NotImplementedError("needs finishing")

def parse_chapters(
    chapters: dict[str, Any],
    file: Path,
    activation_bytes: str,
    album: str,
    ch_start=None,
    ch_end=None,
    suffix: str = "",
):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise FileNotFoundError("ffmpeg not found!")
    for i_chap, chapter in enumerate(chapters["chapters"]):
        if ch_start is not None and i_chap + 1 < ch_start:
            continue
        if ch_end is not None and i_chap + 1 > ch_end:
            continue
        title = chapter["tags"]["title"]

        cmd = [
            ffmpeg,
            "-y",
            "-activation_bytes",
            activation_bytes,
            "-i",
            file,
            "-ss",
            chapter["start_time"],
            "-to",
            chapter["end_time"],
            "-metadata",
            f"title={title}",
        ]

        if album:
            cmd.extend(["-metadata", f"album={album}"])

        out_arg = Path(file).stem
        tail = f"_{i_chap + 1}"
        if suffix:
            tail = f"_{suffix}{tail}"
        output = f"{out_arg}_{tail}.mp3"
        cmd.extend(["-c:a", "mp3", "-vn", output])
        print(cmd)

        subprocess.check_output(cmd, universal_newlines=True)


@click.command("peak-file")
@click.option(
    "-f",
    "--file",
    help="input aax file",
    type=Path,
)
@click.option("-a", "--activation-bytes", help="activation bytes", type=str)
def peak_aax(file, activation_bytes) -> None:
    chapters = get_chapters(file)
    for chapter in chapters["chapters"]:
        title = chapter["tags"]["title"]
        start = chapter["start_time"]
        end = chapter["end_time"]
        print(f"{title}: {start}:{end}")


@click.command("convert-serial")
@click.option(
    "-f",
    "--file",
    help="input aax file",
    type=Path,
)
@click.option("-a", "--activation-bytes", help="activation bytes", type=str)
@click.option(
    "--album",
    help="ID3v2 tag for Album, if not specified, uses from aax",
    default="",
    type=str,
)
@click.option("--start", help="chapter start", type=int)
@click.option("--end", help="chapter end", type=int)
def convert_serial(
    file: Path, activation_bytes: str, album: None | str = None, start=None, end=None
) -> None:
    """Covert AAX to MP3 file given an set of activation bytes"""
    # Collate args
    if not file or not activation_bytes:
        raise ValueError("File and activation_bytes required")
    chapters = get_chapters(file)
    print(chapters)

    parse_chapters(
        chapters, file, activation_bytes, album=album, ch_start=start, ch_end=end
    )


if __name__ == "__main__":
    convert_serial()
