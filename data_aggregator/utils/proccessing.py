# Imports
import subprocess
import os
import shutil
import re
import argparse

from utils.helpers import run_local_inference

import mlx.core as mx
import mlx_whisper
from mlx_vlm import load as vlm_load, generate as vlm_generate
from mlx_lm import load as lm_load, generate as lm_generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

# ---------------------------- Processing Functions ----------------------------

def process_audio(video_file):
    '''
    Helper method that will extract audio and dervive a transcript using a local model.

    Params:
    - video_file: the .mp4 file to be processed

    Returns:
    - text: the transcript returned from the model
    '''

    # Extract the audio
    print("Extracting audio from the video...")
    transcript = "Could not transcribe."
    try:
        command = ["ffmpeg", "-i", video_file, "-ar", "16000", "audio.wav"]
        subprocess.run(command)

        # Transcribe using the model
        print("Transcribing the audio...")
        transcript = mlx_whisper.transcribe(
            "audio.wav", 
            path_or_hf_repo="mlx-community/whisper-large-v3-turbo"
        )["text"]
        print("Audio transcribed!")

    except Exception as e:
        print(f"Could not transcribe audio, setting a placeholder transcription: {e}")

    return transcript


def process_video(video_file, model, processor, config):
    """
    Helper function that processes a given video for a summary.

    Params:
    - video_file: the .mp4 file to be processed
    - model: the MLX model object
    - processor: the MLX proccessing object
    - config: the MLX configuration object 

    Returns:
    - response: the string of text that summarizes the video
    """

    # Convert the video into individual frames (one every few seconds), downscaling
    # to fit within a 512x512 box for memory usage optimization
    print("Converting video to frames...")
    response = "Could not process frame."
    try:
        os.makedirs("frames", exist_ok=True)
        command = [
            "ffmpeg", "-i", video_file,
            "-vf", "fps=1/3,scale=w=512:h=512:force_original_aspect_ratio=decrease",
            "frames/frame%04d.jpg"
        ]
        subprocess.run(command)

        # Process the frames, capping the total so we don't run the VLM out of memory
        print("Processing frames...")
        max_frames = 12
        frames = sorted([f"frames/{f}" for f in os.listdir("frames")])

        ## Cap the frames
        if len(frames) > max_frames:
            step = len(frames) / max_frames
            frames = [frames[int(i * step)] for i in range(max_frames)]
        
        ## Process the frame with the vision model
        prompt = "Create a general summary of the given video. Extract resturant names, place names, neighborhoods, locations visible/mentioned, and any other pertinent information described in the video."
        formatted_prompt = apply_chat_template(processor, config, prompt, num_images=len(frames))
        processed = vlm_generate(model, processor, formatted_prompt, frames)

        # Newer mlx_vlm returns a GenerationResult object - keep only the text
        response = getattr(processed, "text", processed)
        print("Frames processed!")
    
    except Exception as e:
        print(f"Could not process frame, setting a placeholder summary: {e}")

    return response


def process_summaries(audio_transcript, video_summary, model, tokenizer_obj):
    """
    Helper function to process output from both audio and video processing to get a general
    title and summary for each video.

    Params:
    - audio_transcript: a string representing the audio transcript
    - video_summary: a string that holds a summary of the actual video
    - model: the text model we will be using
    - tokenizer_obj: the tokenization object used to embed the text
    """

    print("Generating summaries...")
    generated_title = "Unprocessed Video"
    generated_summary = "Could not proccess this video."
    try:
        
        # Get the title
        title_prompt = f"/no_think Create a title that concisely summarizes the following: \nAudio Transcription: {audio_transcript} \nVideo Summary: {video_summary} \n\n Use `Title Case` to format the generated title. Do not output anything except the requested title in the specified format."
        generated_title = run_local_inference(title_prompt, model, tokenizer_obj, token_max=75)
        generated_title = re.sub(r"<think>[\s\S]*?</think>", "", generated_title).strip()

        # Get the summary
        summary_prompt = f"/no_think Concisely summarize the following: \nAudio Transcription: {audio_transcript} \nVideo Summary: {video_summary} \n\n Do not output anything except the requested summary."
        generated_summary = run_local_inference(summary_prompt, model, tokenizer_obj, token_max=1024)
        generated_summary = re.sub(r"<think>[\s\S]*?</think>", "", generated_summary).strip()

    except Exception as e:
        print(f"Could not generate summaries, using placeholder values: {e}")

    return generated_title, generated_summary


# ---------------------------- Configuration Functions ----------------------------


def configure_vlm():
    """
    Helper method to configure the vision language model (VLM) used for video processing

    Returns:
    - m: the MLX model object
    - p: the MLX proccessing object
    - c: the MLX configuration object
    """

    print("Configuring the vision model w/ mlx-community/Qwen2-VL-2B-Instruct-4bit...")
    model_path = "mlx-community/Qwen2-VL-2B-Instruct-4bit"
    m, p = vlm_load(model_path)
    c = load_config(model_path)
    print("mlx-community/Qwen2-VL-2B-Instruct-4bit configured!")

    return m, p, c
