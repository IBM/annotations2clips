"""Test video processor class and methods."""

import csv
import json
import sys
from pathlib import Path

import pytest

from annotations2clips.video_processor import VideoProcessor, VideoProcessorSettings


@pytest.fixture
def video_processor(monkeypatch) -> VideoProcessor:
    """Instantiate a VideoProcessor object."""
    params = [
        "src/annotations2clips/main.py",
        "--data_path",
        "tests/test_data",
        "--output_path",
        "tests/output",
        "--preserve_folder_structure",
        "true",
    ]
    monkeypatch.setattr(sys, "argv", params)
    args = VideoProcessorSettings()
    processor = VideoProcessor(args=args)

    return processor


def test_check_valid_annotation_file(video_processor) -> None:
    """Test annotation file validation."""

    processor = video_processor

    file_path = Path(
        "tests", "test_data", "station_1", "user_1", "fef69bac-bc6d-47c7-8c8a-bd56ffa0c851.json"
    )
    is_valid, _ = processor.check_valid_annotation_file(file_path)

    assert is_valid


def test_annotation_return_dict(video_processor) -> None:
    """Test retrieval of dictionary from annotation file."""

    processor = video_processor

    file_path = Path(
        "tests", "test_data", "station_1", "user_1", "fef69bac-bc6d-47c7-8c8a-bd56ffa0c851.json"
    )
    _, annotation_dict = processor.check_valid_annotation_file(file_path)

    assert annotation_dict["project"]["pid"] == file_path.stem
    assert annotation_dict["file"]["1"]["fname"] == "test_video.mp4"


def test_discover_files(video_processor) -> None:
    """Test discovery of video and annotation files."""

    processor = video_processor
    processor.discover_files()

    print(processor.videos)

    assert len(processor.videos) == 3


def test_get_annotations(video_processor) -> None:
    """Test retrieval of annotations."""

    processor = video_processor
    processor.discover_files()
    processor.get_annotations()

    number_of_events = len([
        event
        for video in processor.annotations.keys()
        for key in processor.annotations[video].keys()
        for event in processor.annotations[video][key]
    ])
    unique_actions = len(
        set([
            action
            for video in processor.annotations.keys()
            for action in processor.annotations[video].keys()
        ])
    )

    assert number_of_events == 23
    assert unique_actions == 9


def test_create_clips_and_metadata_file_creation(video_processor) -> None:
    """Test creation of clips and saving of metadata to files."""

    processor = video_processor
    processor.discover_files()
    processor.get_annotations()
    stats = processor.create_clips()

    output_path = Path("tests", "output")
    num_clips = len([v for v in output_path.rglob("*.mp4")])

    processor.create_jsonl_file()
    with Path(str(Path(output_path, "clips.jsonl"))).open("r") as f:
        jsonl_lines = []
        reader = csv.reader(f)
        for row in reader:
            jsonl_lines.append(row)

    processor.save_stats(output_path=output_path, stats_dict=stats)
    with Path(str(Path(output_path, "clips_stats.json"))).open("r") as f:
        stats_dict = json.load(f)

    processor.save_file_mapping()
    with Path(str(Path(output_path, "clips_mapping.json"))).open("r") as f:
        mapping_dict = json.load(f)

    assert num_clips == 144
    assert jsonl_lines[0] == [
        '{"image:":"245ac5779079b967_blue_000_000.mp4"',
        'label:"blue"}',
    ]
    assert jsonl_lines[-1] == [
        '{"image:":"e89d7c6e33e5a806_white_002_005.mp4"',
        'label:"white"}',
    ]
    assert stats_dict == {
        "blue": 4,
        "green": 5,
        "grey": 62,
        "red": 12,
        "violet": 18,
        "white": 35,
        "indigo": 4,
        "orange": 2,
        "yellow": 2,
    }
    assert (
        mapping_dict["e89d7c6e33e5a806"]
        == "tests/test_data/station_1/user_2/573ce385-0f6f-4c6b-8730-8130424f7c6f"
    )

    output_path
