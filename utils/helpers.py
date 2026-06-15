# Imports
import os
import shutil
import argparse

import mlx.core as mx
from mlx_lm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

# ---------------------------- Helper Functions ----------------------------

def get_args():
    """
    Helper function to take in CLI arguments via ArgParse
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data-path",
        type=str,
        help="The path to where all of your .mp4 files to be processed live."
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="traveling_reel_summary.json",
        help="The path to where the final JSON object will be outputted to."
    )

    return parser.parse_args()

def inference(prompt, llm, tokenizer, token_max, inference_type="video_processing"):
    """
    Helper function that will run inference through the model.

    Params:
    - prompt: the given prompt string passed to the model
    - llm: the text model we will use for infernece
    - tokenizer: the tokenization object used to convert strings to tokens
    - token_max: max number of generated tokens
    """

    # Conform the prompt to the chat template
    messages = []
    if inference_type == "cluster":
        system_prompt = "You are an expert data analyst and knowledge organization specialist. Your strength is identifying patterns, relationships, and natural groupings within complex datasets. You approach analysis systematically, provide clear reasoning for your classifications, and always think about how to communicate findings visually and narratively. When analyzing data, you consider multiple dimensions of similarity—semantic, categorical, temporal, and relational. You produce well-structured markdown output with clear hierarchies, visual diagrams, and comprehensive summaries that make complex patterns accessible. You are thorough, precise, and always explain your clustering logic clearly."
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    # Run inference
    print(f"Running text model inference for inference type {inference_type}...")
    formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    response = generate(llm, tokenizer, prompt=formatted_prompt, max_tokens=token_max, verbose=False)
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
    
    # Clear GPU memory buffers
    mx.clear_cache()

    print("Cleanup complete!")


def configure_lm(model):
    """
    Helper method to configure the language model (LM) used for text processing & generation

    Params:
    - model: a string that represents the HuggingFace model we want to run with (currently
    only supports Apple Sillicon architecture through the MLX HF community)
    Returns:
    - m: the MLX model object
    - t: the MLX tokenizer object
    """

    print(f"Configuring the language model w/ {model}...")
    m, t = load(model)
    print(f"{model} configured!")

    return m, t
