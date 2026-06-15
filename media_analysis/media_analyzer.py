"""
Media Analyzer

Author: Christian Sarmiento
Date Created: 6/13/26
Purpose: Using the outputted JSON file from the 
`data_aggregator/video_proccessor.py` script that has per-video AI 
generated summaries and audio transcripts, this script does several
types of analysis on that data using AI to gain a deeper understanding
on the type of information we have available to us. 
"""

# Imports
from pathlib import Path
from datetime import datetime
import json

from utils.helpers import (
    cleanup,  get_args, configure_lm, run_local_inference, send_inference_request
)
from media_analysis.utils.analysis import select_analysis_type


def main():

    # Record the start time
    start_time = datetime.now()
    print(f"Script started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Get CLI args
    args =  get_args()

    # Parameters
    MAX_TOKENS = 20000
    TASK = args.analysis_type
    SELECTED_MODEL = args.model #"mlx-community/Meta-Llama-3-8B-Instruct-4bit"

    # Read the JSON file with the data
    if not args.data_path:
        raise ValueError("--data-path is required.")
    json_path = Path(args.data_path).expanduser().resolve()
    if not json_path.exists():
        raise FileNotFoundError(f"Data path does not exist: {json_path}")
    if not json_path.is_file():
        raise IsADirectoryError(f"Data path is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError(f"Data path is not a JSON file: {json_path}")
    
    with open(json_path, "r") as f:
        data = json.load(f)

    # Decide which prompt will be run based off analysis type
    prompt = select_analysis_type(analysis=TASK, given_data=data)

    # Conduct inference based on the selected model
    if "mlx" in SELECTED_MODEL:

        # Configure model & run inference
        model, tokenizer = configure_lm(SELECTED_MODEL)
        response = run_local_inference(
            prompt, model, tokenizer, MAX_TOKENS, inference_type=TASK
        )

    elif "claude" in SELECTED_MODEL:

        # Send inference request to the Anthropic servers
        claude_client, _ = configure_lm(SELECTED_MODEL)
        response = send_inference_request(
            prompt, claude_client, MAX_TOKENS, SELECTED_MODEL, inference_type=TASK
        )

    # Write the markdown output to file
    print("Saving final output...")
    output_path = Path(args.output_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(response)
    print(f"Output saved to {output_path}!")

    # Record the end time and total duration
    cleanup()
    end_time = datetime.now()
    elapsed = end_time - start_time
    print(f"\nScript ended at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time elapsed: {elapsed}")

if __name__ == "__main__":
    main()
