# Imports
import subprocess
import os
import shutil

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
    command = ["ffmpeg", "-i", video_file, "-ar", "16000", "audio.wav"]
    subprocess.run(command)

    # Transcribe using the model
    print("Transcribing the audio...")
    transcript = mlx_whisper.transcribe(
        "audio.wav", 
        path_or_hf_repo="mlx-community/whisper-large-v3-turbo"
    )["text"]
    print("Audio transcribed!")

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

    # Convert the video into individual frames (one every few seconds)
    print("Converting video to frames...")
    os.makedirs("frames", exist_ok=True)
    command = ["ffmpeg", "-i", video_file, "-vf", "fps=1/3", "frames/frame%04d.jpg"]
    subprocess.run(command)

    # Process the frames, capping the total so we don't run the VLM out of memory
    print("Processing frames...")
    max_frames = 12
    frames = sorted([f"frames/{f}" for f in os.listdir("frames")])
    if len(frames) > max_frames:
        step = len(frames) / max_frames
        frames = [frames[int(i * step)] for i in range(max_frames)]
    prompt = "Create a general summary of the given video. Extract resturant names, place names, neighborhoods, locations visible/mentioned, and any other pertinent information described in the video."
    formatted_prompt = apply_chat_template(processor, config, prompt, num_images=len(frames))
    processed = vlm_generate(model, processor, formatted_prompt, frames)
    response = getattr(processed, "text", processed)
    print("Frames processed!")

    # Newer mlx_vlm returns a GenerationResult object; keep only the text
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

    # Get the title
    print("Generating summaries...")
    title_prompt = f"/no_think Create a title that concisely summarizes the following: \nAudio Transcription: {audio_transcript} \nVideo Summary: {video_summary} \n\n Use `Title Case` to format the generated title. Do not output anything except the requested title in the specified format."
    generated_title = inference(title_prompt, model, tokenizer_obj, token_max=75)

    # Get the summary
    summary_prompt = f"/no_think Concisely summarize the following: \nAudio Transcription: {audio_transcript} \nVideo Summary: {video_summary} \n\n Do not output anything except the requested summary."
    generated_summary = inference(summary_prompt, model, tokenizer_obj, token_max=1024)

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


def configure_lm():
    """
    Helper method to configure the language model (LM) used for text processing & generation

    Returns:
    - m: the MLX model object
    - t: the MLX tokenizer object
    """

    print("Configuring the language model w/ mlx-community/Qwen3-8B-4bit...")
    m, t = lm_load("mlx-community/Qwen3-8B-4bit")
    print("mlx-community/Qwen3-8B-4bit configured!")

    return m, t


# ---------------------------- Helper Functions ----------------------------


def inference(prompt, llm, tokenizer, token_max):
    """
    Helper function that will run inference through the model.

    Params:
    - prompt: the given prompt string passed to the model
    - llm: the text model we will use for infernece
    - tokenizer: the tokenization object used to convert strings to tokens
    - token_max: max number of generated tokens
    """

    # Conform the prompt to the chat template
    messages = [{"role": "user", "content": prompt}]

    # Run inference
    print("Running text model inference...")
    formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    response = lm_generate(llm, tokenizer, prompt=formatted_prompt, max_tokens=token_max, verbose=False)
    print("Text model inference complete")

    return response


def cleanup():
    '''
    Helper function to cleanup any generated artifacts
    '''

    # Remove the extracted audio
    print("Cleaning up generated artifacts...")
    if os.path.exists("audio.wav"):
        os.remove("audio.wav")

    # Remove the frames directory recursively
    if os.path.exists("frames"):
        shutil.rmtree("frames")
    print("Cleanup complete!")
