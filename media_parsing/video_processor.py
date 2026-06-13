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
import json

from media_parsing.proccessing import (
    process_audio, process_video, configure_vlm, configure_lm, process_summaries
)

def main():

    # Read the folder with the data
    data_path = "/Users/christiansarmiento/Desktop/tmp"
    folder = Path(data_path)

    # Configure the vision model
    vision_model, frame_processor, model_config = configure_vlm()

    # Configure the text model
    text_model, tokenizer = configure_lm()

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
            aggregated_videos[title] = {
                "summary": summary,
                "audio_transcript": transcript,
                "video_summary": visual_summary
            }
            print(f"Video {idx + 1}/{video_count} processed!")

    # Write the final output to a JSON object
    print("Saving final output...")
    output_path = "japan_traveling_reel_summary.json"
    with open(output_path, "w") as f:
        json.dump(aggregated_videos, f, indent=2)
    print(f"Output saved to {output_path}!")

if __name__ == "__main__":
    main()
