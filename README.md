[![unit tests](https://github.com/IBM/annotations2clips/actions/workflows/tests.yml/badge.svg)](https://github.com/IBM/annotations2clips/actions/workflows/tests.yml)

# Annotations2Clips

A lightweight package to chunk videos into clips based on annotation files.

## Setup

Ensure you have [uv](https://docs.astral.sh/uv/) installed for project and dependency management.

Clone this repository locally and set up the required dependencies from the root folder with:

```
uv sync
```

## Data prerequisites

This package is designed to work with JSON annotation files created by the open-source [VGG Image Annotator](http://www.robots.ox.ac.uk/~vgg/software/via) tool. Each JSON annotation file should be co-located with a folder of the same name which contains the MP4 video file to be processed, see the following exemplary folder structure:

```
.
└── station_1
    ├── user_1
    │   ├── 7acfe8b0-0b2a-49bb-af85-e67885baf693
    │   │   └── test_video.mp4
    │   ├── 7acfe8b0-0b2a-49bb-af85-e67885baf693.json
    │   ├── fef69bac-bc6d-47c7-8c8a-bd56ffa0c851
    │   │   └── test_video.mp4
    │   └── fef69bac-bc6d-47c7-8c8a-bd56ffa0c851.json
    └── user_2
        ├── 573ce385-0f6f-4c6b-8730-8130424f7c6f
        │   └── test_video.mp4
        └── 573ce385-0f6f-4c6b-8730-8130424f7c6f.json
```

## Usage

In the project root folder, run the script:

```bash
uv run convert_annotations_to_clips \
    --data_path "tests/test_data" \
    --output_path "output" \
    --preserve_folder_structure false \
    --clip_length 4.0 \
    --clip_fps 4
```

The arguments are defined as follows:

| Argument          | Description |
| --- | --- |
| `--data_path`      | Root folder containing all videos to be processed |
| `--output_path`     | Target root folder for the processed video clips  |
| `--preserve_folder_structure` | If true, processed clips will be stored in a folder sub-structure mirroring the video root folder, otherwise all clips will be stored together directly in the target root folder
| `--clip_length`   | The length of each output video clip in seconds |
| `--clip_fps`      | The frame rate of the output video clips |


## License

This package is made available under the [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0.html) license.


## IBM Public Repository Disclosure

All content in these repositories including code has been provided by IBM under the associated open source software license and IBM is under no obligation to provide enhancements, updates, or support. IBM developers produced this code as an open source project (not as an IBM product), and IBM makes no assertions as to the level of quality nor security, and will not be maintaining this code going forward.
