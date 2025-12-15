"""Define the video processor class and methods."""

import json
from math import floor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from loguru import logger
from moviepy import VideoFileClip
from pydantic_settings import BaseSettings, SettingsConfigDict
from tqdm import tqdm

from annotations2clips.annotation_reader import AnnotationReader
from annotations2clips.utils import construct_preserved_output_path, construct_video_filename


class VideoProcessorSettings(BaseSettings):
    """Video processor settings.

    Attributes:
        data_path (Path): Root folder containing all videos to be processed.
        output_path (Path): Target root folder for the processed video clips.
        preserve_folder_structure (bool): If true, processed clips will be stored in a folder sub-structure similar to the video root folder, otherwise all clips will be stored together directly in the target root folder.
        clip_length (float): The length of each output video clip in seconds.
        clip_fps (int): The frame rate of the output video clips.
        codec (string): A four-character code defining the video codec to use.
    """

    data_path: Path
    output_path: Path
    preserve_folder_structure: bool = False
    clip_length: float = 4.0
    clip_fps: int = 4
    codec: Optional[str] = "h264"
    model_config = SettingsConfigDict(cli_parse_args=True)


class VideoProcessor:
    """Video processor class."""

    videos: Dict[str, Dict[str, Any]] = {}

    def __init__(
        self,
        args: VideoProcessorSettings,
    ):
        """Initialize the video processor class."""

        self.args = args

    @staticmethod
    def check_valid_annotation_file(json_file: Path) -> Tuple[bool, Union[Dict[str, Any]]]:
        """Check whether a JSON file represents a valid annotation file.

        Args:
            json_file (Path): Path to a JSON file.

        Returns:
            A tuple containing a boolean confirming whether the JSON file is a valid annotation file (True) or not (False),
            and a dictionary with annotation entries if they exist.
        """

        with Path(json_file).open("r") as f:
            try:
                dict_to_check = json.load(f)
            except Exception:
                raise Exception(f"Not a valid JSON: {json_file}")

        is_valid = all([
            k in dict_to_check.keys() for k in ["project", "attribute", "file", "metadata"]
        ])

        if is_valid:
            return_dict = {k: v for k, v in dict_to_check.items() if k in ["project", "file"]}
        else:
            return_dict = {}

        return (is_valid, return_dict)

    def discover_files(self) -> None:
        """
        Discover video and annotation files within the root data path.

        Creates a class attribute that is a dictionary containing
        unique video file tags as keys together with the paths to
        the respective MP4 and JSON files.
        """

        self.videos: Dict[str, Dict[str, Any]] = {}

        root = self.args.data_path

        dir_count = 0
        file_count = 0

        for item in tqdm(root.rglob("*")):
            if item.is_file():
                file_count += 1
                if item.suffix == ".json":
                    valid_annotation = self.check_valid_annotation_file(item)
                    if valid_annotation[0]:
                        uid = valid_annotation[1]["project"]["pid"]
                        video_file_name = valid_annotation[1]["file"]["1"]["fname"]
                        if Path(item.parent, item.stem).is_dir():
                            video_path = Path(item.parent, item.stem, video_file_name)
                            self.videos[uid] = {
                                "annotation_path": item,
                                "video_path": video_path,
                            }
                        else:
                            logger.warning(
                                f"No corresponding folder found for annotation file {item.name}"
                            )
            elif item.is_dir():
                dir_count += 1

        number_of_videos = sum(
            1
            for uid in self.videos.keys()
            for path in self.videos[uid].values()
            if path.suffix == ".mp4"
        )

        logger.info(
            f"Found {number_of_videos} annotated videos in {file_count} files across {dir_count} directories"
        )

        return None

    def get_annotations(self) -> None:
        """
        Populates a class attribute that is a dictionary with the
        unique video file tags together with the annotation details
        regarding action type, start time and end time for each
        video.
        """

        self.annotations: Dict[str, Dict[str, List[Tuple]]] = {k: dict() for k in self.videos}

        logger.info("Parsing annotations from annotation files")
        for video in tqdm(self.videos):
            logger.debug(f"Parsing annotations for {video}")
            annotation_reader = AnnotationReader(
                path_to_annotation_file=self.videos[video]["annotation_path"]
            )
            self.annotations[video] = annotation_reader.extract_annotations()

        unique_actions = len(
            set([
                action
                for video in self.annotations.keys()
                for action in self.annotations[video].keys()
            ])
        )
        total_number_of_actions = len([
            event
            for video in self.annotations.keys()
            for key in self.annotations[video].keys()
            for event in self.annotations[video][key]
        ])
        logger.info(
            f"Parsed a total of {total_number_of_actions} events from {unique_actions} unique actions"
        )

        return None

    def create_clips(self) -> Dict[str, int]:
        """
        Create the video clips and return a dictionary containing the
        number of clips for each action type.

        Args:
            None

        Returns:
            A dictionary containing the action names as keys and the number of
            corresponding video clips as values.
        """

        stats_dict: Dict[str, int] = {}

        logger.info("Chunking videos into clips")
        for uid in tqdm(sorted(self.videos, key=lambda s: s.encode("utf-8")), desc="videos"):
            self.videos[uid]["clips"] = {}
            action_tracker_per_video: Dict[str, int] = {}
            for action in sorted(self.annotations[uid], key=lambda s: s.encode("utf-8")):
                for t_segment in self.annotations[uid][action]:
                    if action in action_tracker_per_video.keys():
                        action_tracker_per_video[action] += 1
                    else:
                        action_tracker_per_video[action] = 0
                    len_t_segment = t_segment[1] - t_segment[0]
                    if len_t_segment < self.args.clip_length:
                        logger.warning(
                            f"Skipping action segment {action} in time segment {t_segment} in video {uid} because it is below clip length {self.args.clip_length}"
                        )
                    n_chunks = floor(len_t_segment / self.args.clip_length)
                    t_start = (
                        t_segment[0] + (len_t_segment - (n_chunks * self.args.clip_length)) / 2
                    )
                    for chunk in range(n_chunks):
                        t_end = t_start + self.args.clip_length
                        clip = VideoFileClip(self.videos[uid]["video_path"]).subclipped(
                            t_start, t_end
                        )
                        filename = construct_video_filename(
                            uid=uid,
                            action=action,
                            action_index=action_tracker_per_video[action],
                            chunk_index=chunk,
                        )
                        output_path = (
                            construct_preserved_output_path(
                                root=self.args.data_path,
                                input_file=self.videos[uid]["video_path"],
                                output_folder=self.args.output_path,
                                output_file=filename,
                            )
                            if self.args.preserve_folder_structure
                            else Path(self.args.output_path, filename)
                        )
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        clip.write_videofile(
                            filename=output_path,
                            fps=self.args.clip_fps,
                            codec=self.args.codec,
                            logger=None,
                        )
                        if action not in self.videos[uid]["clips"]:
                            self.videos[uid]["clips"][action] = [filename]
                        else:
                            self.videos[uid]["clips"][action].append(filename)
                        t_start = t_end
                    if action in stats_dict:
                        stats_dict[action] += n_chunks
                    else:
                        stats_dict[action] = n_chunks
                logger.info(
                    f"Saved {n_chunks} chunks of video {uid} containing action '{action}' to {output_path.parent}"
                )

        return stats_dict

    def create_jsonl_file(
        self,
        filename: str = "clips.jsonl",
        video_key: str = "image",
        class_key: str = "label",
    ) -> None:
        """Create a JSONL file summarizing the video clip files and action labels.

        Args:
            filename (str): Name of the JSONL file to output the clip file and lable information.
            video_key (str): The string to use as key for the video clip.
            class_key (str): The string to use as key for the action label.

        Returns:
            None
        """

        out_file = Path(self.args.output_path, filename)

        with Path(out_file).open("w") as out:
            for uid in self.videos:
                for action in self.videos[uid]["clips"]:
                    out.writelines([
                        f'{{"{video_key}:":"{clip_file}","{class_key}":"{action}"}}\n'
                        for clip_file in self.videos[uid]["clips"][action]
                    ])

        logger.info(f"Clip and action inventory written to {out_file}")

        return None

    @staticmethod
    def save_stats(
        output_path: Path, stats_dict: Dict[str, int], filename: str = "clips_stats.json"
    ) -> None:
        """Write a JSON file with the number of clips generated per action type.

        Args:
            output_path (Path): The output path to write the file.
            stats_dict (dict): A dictionary containing the actions as keys and number of clips as values.
            filename (str): The name of the file to write.

        Returns:
            None
        """

        out_file = Path(output_path, filename)

        with Path(out_file).open("w") as out:
            json.dump(stats_dict, out, indent=4)

        logger.info(f"Action statistics written to {out_file}")

        return None

    def save_file_mapping(self, filename: str = "clips_mapping.json") -> None:
        """Save the mapping of unique video ids to original paths in a file.

        Args:
            filename (str): Name of the output file to save the file mapping.

        Returns:
            None
        """

        out_file = Path(self.args.output_path, filename)

        mapping_dict = {
            k: v
            for (k, v) in zip(
                self.videos, [str(self.videos[uid]["video_path"].parent) for uid in self.videos]
            )
        }

        with Path(out_file).open("w") as out:
            json.dump(mapping_dict, out, indent=4)

        logger.info(f"File mapping written to {out_file}")

        return None
