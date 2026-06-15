# Imports
import os
import shutil
import argparse

import mlx.core as mx
from mlx_lm import load, generate
import anthropic
from dotenv import load_dotenv

# Load environment variables the .env file
load_dotenv()

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
    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-6",
        help="The model to use for inference. If using a local model off HuggingFace, it must be an mlx_community model so that it is compatible with Apple Silicone architecture."
    )
    parser.add_argument(
        "--analysis-type",
        type=str,
        default="cluster",
        help="The type of analysis to conduct on the data."
    )

    return parser.parse_args()


def get_messages(given_prompt, task):
    """
    Helper method that gets the list of messages to send for inference

    Params:
    - given_prompt: the string that represents the main prompt to be passed along.
    - task: the inference task we would like to complete (['cluster'])
    """

    prompts = []
    if task == "cluster":
        system_prompt = "You are an expert data analyst and knowledge organization specialist. Your strength is identifying patterns, relationships, and natural groupings within complex datasets. You approach analysis systematically, provide clear reasoning for your classifications, and always think about how to communicate findings visually and narratively. When analyzing data, you consider multiple dimensions of similarity—semantic, categorical, temporal, and relational. You produce well-structured markdown output with clear hierarchies, visual diagrams, and comprehensive summaries that make complex patterns accessible. You are thorough, precise, and always explain your clustering logic clearly."
        prompts.append({"role": "system", "content": system_prompt})
    prompts.append({"role": "user", "content": given_prompt})

    return prompts

def run_local_inference(prompt, llm, tokenizer, token_max, inference_type="video_processing"):
    """
    Helper function that will run inference through the model.

    Params:
    - prompt: the given prompt string passed to the model
    - llm: the text model we will use for infernece
    - tokenizer: the tokenization object used to convert strings to tokens
    - token_max: max number of generated tokens
    """

    # Conform the prompt to the chat template
    messages = get_messages(prompt, inference_type)

    # Run inference
    print(f"Running text model inference for inference type {inference_type}...")
    formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    response = generate(llm, tokenizer, prompt=formatted_prompt, max_tokens=token_max, verbose=False)
    print("Text model inference complete")

    return response


def send_inference_request(prompt, client, token_max, given_model, inference_type="video_processing"):
    """
    Helper function to send an inference request to the Anthropic servers 
    (OpenAI as well in the future)

    Params:
    - prompt: the prompt we want to send to the server
    - client: the server client used to interface with the Anthropic servers
    """

    # Conform the prompt to the chat template
    formatted_messages = get_messages(prompt, inference_type)

    # Format the system prompt for Antrhopic
    system_prompt = anthropic.NOT_GIVEN
    chat_messages = []
    for message in formatted_messages:
        if message["role"] == "system":
            system_prompt = message["content"]
        else:
            chat_messages.append(message)

    # Send the request
    print(f"Running text model inference for inference type {inference_type}...")
    response = client.messages.create(
        model=given_model,
        max_tokens=token_max,
        system=system_prompt,
        thinking={"type": "enabled", "budget_tokens": 1500},
        messages=chat_messages
    )
    print("Text model inference complete")

    # Get main generation out
    for block in response.content:
        if block.type == "text":
            generation = block.text

    return generation


def cleanup():
    """
    Helper function to cleanup any generated artifacts
    """

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
    - m: the MLX model object OR Claude client
    - t: the MLX tokenizer object
    """

    print(f"Configuring the language model w/ {model}...")
    if 'mlx' in model:
        m, t = load(model)
    elif 'claude' in model:
        m = anthropic.Anthropic()
        t = None
    
    print(f"{model} configured!")

    return m, t
