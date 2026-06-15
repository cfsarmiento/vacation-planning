# Imports
import subprocess
import os
import shutil
import re
import argparse

import mlx.core as mx
import mlx_whisper
from mlx_lm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config


def select_analysis_type(analysis, given_data):
    """
    Helper method that will select a prompt based on the analysis 
    type passed

    Params:
    - analysis: string that represents the type of analysis to be conducted
    - data: the dictiomary that represents the JSON object with all of our data

    Returns:
    - analysis_prompt: the string that will be passed along as a prompt to the
    language model
    """

    prompts = {
        "cluster": "You will receive a JSON object containing various data points, records, or information items.\n\nYour task:\n1. Analyze the JSON data and identify natural groupings or clusters based on thematic, categorical, or relational similarities\n2. Create a comprehensive markdown document that presents your clustering analysis\n3. For each cluster, provide:\n   - A descriptive cluster name/title\n   - The items or data points that belong to it\n   - A brief explanation of why these items cluster together\n4. Include a visual ASCII diagram or text-based representation showing how the clusters relate to each other and their hierarchical or interconnected structure\n5. Provide an executive summary at the end analyzing:\n   - The overall structure and patterns you discovered\n   - Key insights about the data organization\n   - Any notable outliers or items that don't fit neatly into clusters\n   - Recommendations for how this data could be used or structured\n\nFormat your response as a markdown (.md) document with proper headers, bullet points, code blocks where appropriate, and clear visual organization. Use mermaid diagram syntax if possible for cluster visualization. Do not output anything except the markdown content.\n\nHere is the JSON data to analyze:\n\n{json_data}\n\nProvide the complete markdown analysis now:"
    }

    if analysis == "cluster":
        prompt = prompts[analysis].format(json_data=given_data)
    
    return prompt
