"""
Video Parser

Author: Christian Sarmiento
Date Created: 6/12/26
Purpose: Using Instagram posts & reels scraped via the Instagram
Saved Posts Organizer Chrome extension, this script will intake
each video post and its corresponding metadata and process the
information to summarize what each post provides using the
following LLMs off of HuggingFace:

- mlx-community/whisper-large-v3-turbo (audio processing)
- mlx-community/Qwen2-VL-2B-Instruct-4bit (video processing)
- mlx-community/Qwen3-8B-4bit (text processing/generation)
"""

# Imports
from pathlib import Path
from datetime import datetime
import json

from data_aggregator.utils.proccessing import (
    process_audio, process_video, configure_vlm, process_summaries
)
from utils.helpers import (
    cleanup,  get_args, configure_lm
)

def main():

    # Record the start time
    start_time = datetime.now()
    print(f"Script started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Get CLI args
    args =  get_args()

    # Read the folder with the data
    if not args.data_path:
        raise ValueError("--data-path is required.")
    folder = Path(args.data_path).expanduser().resolve()
    if not folder.exists():
        raise FileNotFoundError(f"Data path does not exist: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Data path is not a directory: {folder}")

    # Configure the vision model
    vision_model, frame_processor, model_config = configure_vlm()

    # Configure the text model
    text_model, tokenizer = configure_lm("mlx-community/Qwen3-8B-4bit")

    aggregated_videos = {}
    videos = sorted(folder.glob("*.mp4"))
    video_count = len(videos)
    if video_count:

        # Iterate through each video
        print(f"Proccessing {video_count} videos...\n")
        for idx, video in enumerate(videos):
            print(f"Processing video {idx + 1}/{video_count}...")

            # Process the audio
            transcript = process_audio(video)

            # Process the video
            visual_summary = process_video(video, vision_model, frame_processor, model_config)

            # Generate a title and overall summary
            title, summary = process_summaries(transcript, visual_summary, text_model, tokenizer)

            # Save the output
            aggregated_videos[video.name] = {
                "title": title,
                "summary": summary,
                "audio_transcript": transcript,
                "video_summary": visual_summary
            }
            cleanup()
            print(f"Video {idx + 1}/{video_count} processed!")

    # Write the final output to a JSON object
    print("Saving final output...")
    output_path = Path(args.output_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(aggregated_videos, f, indent=2)
    print(f"Output saved to {output_path}!")

    # Record the end time and total duration
    end_time = datetime.now()
    elapsed = end_time - start_time
    print(f"\nScript ended at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time elapsed: {elapsed}")

if __name__ == "__main__":
    main()
