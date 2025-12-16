"""Define the annotation reader class and methods."""

import json
from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger


class AnnotationReader:
    """Annotation reader class."""

    action_dict: Dict[str, List[Tuple]] = {}

    def __init__(
        self,
        path_to_annotation_file: Path,
    ):
        """Initialize the annotation reader class."""

        self.path_to_annotation_file = path_to_annotation_file
        self.action_dict: Dict[str, List[Tuple]] = {}

    def extract_annotations(self) -> Dict[str, List[Tuple]]:
        """
        Extract annotation details from an annotation file and
        populate the action_dict class attribute with the annotation
        details.

        Args:
            None

        Returns:
            Dictionary with the actions as keys and lists of start andstop times for each action.
        """

        with Path(self.path_to_annotation_file).open("r") as f:
            annotation_dict = json.load(f)

        id_to_action_dict = {k: v for k, v in annotation_dict["attribute"]["1"]["options"].items()}
        logger.debug(f"annotation_dict: {id_to_action_dict}")

        number_of_actions = 0

        for annotation in annotation_dict["metadata"]:
            entry = annotation_dict["metadata"][annotation]

            try:
                _action = str(id_to_action_dict.get(entry["av"]["1"]))
            except Exception:
                _action = str(entry["av"]["1"])

            if len(entry["z"]) == 2:
                _t_start = entry["z"][0]
                _t_end = entry["z"][1]

                if _action in self.action_dict:
                    self.action_dict[_action].append((_t_start, _t_end))
                else:
                    self.action_dict[_action] = [(_t_start, _t_end)]

                number_of_actions += 1

        logger.info(
            f"Parsed {number_of_actions} actions from file {self.path_to_annotation_file.name}"
        )

        return self.action_dict
