"""Utility functions for Annotations2Clips."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Union

from loguru import logger


def setup_logger(
        sink: Union[str, Path],
        level: Union[int, str] = "DEBUG",
        rotation: Union[int, str] = "100 MB",
) -> None:
    """Set up logging utilities."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if Path(sink).is_dir():
            sink = Path(sink, f"annotations2clips_{timestamp}.log")
    elif Path(sink).is_file():
            sink = sink
    else:
        sink = f"annotations2clips_{timestamp}.log"
        

    logger.remove()
    logger.add(sys.stderr, format="{time} | {level} | {message}")
    logger.add(sink=sink, level=level, rotation=rotation)

    return None

def construct_video_filename(
    uid: str,
    action: str,
    action_index: int,
    chunk_index: int
    ) -> str:
    """Construct a video filename given a set of arguments.

    Args:
        uid (str): A unique identifier.
        action (str): The name of the action type.
        action_index (int): A running index to track multiple instances of the same action type.
        chunk_index (int): A running index to track the chunk instance of the same action.

    Returns:
        The filename as a string.
    """

    filename=f"{uid}_{action}_{action_index:03}_{chunk_index:03}.mp4"

    return filename

def construct_preserved_output_path(
        root: Path,
        input_file: Path,
        output_folder: Path,
        output_file: str
    ) -> Path:
    """Construct a path preserving the original folder structure.
    
    Args:
        root (Path): The root data folder containing all source videos.
        file (Path): The path to the video file being processed.
        output_folder (Path): The main output folder for the processed video clips.
        output_file (str): Name of the output video clip.

    Returns:
        A Path object preserving the original folder structure within the output folder.
    """

    relative_video_path = input_file.relative_to(root)
    preserved_output_path = Path(output_folder, relative_video_path.parent, output_file)

    return preserved_output_path
