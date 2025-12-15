"""Test parsing of annotation file."""

from pathlib import Path

from annotations2clips.annotation_reader import AnnotationReader


def test_extract_annotations() -> None:
    """Test annotation extraction."""

    path_to_annotation_file = Path(
        "tests", "test_data", "station_1", "user_2", "573ce385-0f6f-4c6b-8730-8130424f7c6f.json"
    )
    annotation_reader = AnnotationReader(path_to_annotation_file=path_to_annotation_file)
    annotations = annotation_reader.extract_annotations()
    total_number_of_actions = len([
        event for action in annotations for event in annotations[action]
    ])

    assert list(annotations.keys()) == ["grey", "white", "red", "violet", "green", "blue"]
    assert annotations["grey"] == [(0, 49.695), (225.365, 259.365), (271.375, 368.365)]
    assert annotations["white"] == [(49.715, 74.145), (178.035, 225.345), (378.679, 403.78833)]
    assert annotations["red"] == [(74.165, 115.065)]
    assert annotations["violet"] == [(115.085, 178.015)]
    assert annotations["green"] == [(259.385, 271.345)]
    assert annotations["blue"] == [(368.385, 378.65857)]
    assert total_number_of_actions == 10
