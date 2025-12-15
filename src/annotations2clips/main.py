"""Generation of clips from annotated videos."""

from loguru import logger

from annotations2clips.utils import setup_logger
from annotations2clips.video_processor import VideoProcessor, VideoProcessorSettings


def main() -> None:
    """
    Main function to initialize the video processor and annotation reader
    classes and generate the chunked video clips.

    Args:
        None

    Returns:
        None
    """

    args = VideoProcessorSettings()
    setup_logger(sink=args.output_path)
    logger.info(f"Starting video processing with the following settings: {args}")

    video_processor = VideoProcessor(args=args)

    video_processor.discover_files()
    video_processor.get_annotations()

    stats = video_processor.create_clips()
    video_processor.save_stats(
        output_path=args.output_path, stats_dict=stats, filename="clips_stats.json"
    )
    video_processor.create_jsonl_file(
        filename="clips.jsonl",
        video_key="image",
        class_key="label",
    )
    video_processor.save_file_mapping(filename="file_mapping.json")

    return None


if __name__ == "__main__":
    main()
