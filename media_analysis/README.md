# Media Analyzer for Vacation Planning

Once you've aggregated a folder of Instagram reels/posts into a single JSON file with [data_aggregator/video_processor.py](../data_aggregator/video_processor.py) (per‑video AI summaries, audio transcripts, and visual summaries), this script does deeper AI analysis on that aggregated data to help you actually make sense of it. [media_analyzer.py](media_analyzer.py) reads that JSON, runs an analysis prompt over it, and writes a structured markdown report.

Inference can run either **remotely through Claude** (the default) or **locally through an Apple‑Silicon (MLX) model** — you pick with the `--model` flag.

## Pipeline

For a given JSON data file, [media_analyzer.py](media_analyzer.py) drives [utils/analysis.py](utils/analysis.py) and the shared helpers in [utils/helpers.py](../utils/helpers.py) to:

1. **Load** — read and validate the aggregated JSON file passed via `--data-path`.
2. **Select** — choose an analysis prompt based on `--analysis-type` (see [Analysis Types](#analysis-types)).
3. **Analyze** — run inference with the selected `--model`:
   - If the model name contains `claude`, the prompt is sent to the Anthropic servers.
   - If the model name contains `mlx`, the prompt is run locally through an MLX model.
4. **Write** — save the model's markdown output to `--output-path`.

### Analysis Types

| Type | Description |
| --- | --- |
| `cluster` (default) | Identifies natural groupings/clusters in the data and produces a markdown report with named clusters, the items in each, why they group together, a mermaid/ASCII diagram of how they relate, and an executive summary with insights and outliers. |

## Hardware & Model Considerations

You can run this script on any platform **as long as you use Claude** (the default) for inference — only an internet connection and an Anthropic API key are required.

> **Local models only run on a Mac with Apple Silicon (M‑series).**

Local inference is built on [MLX](https://github.com/ml-explore/mlx), Apple's array framework for Apple‑Silicon GPUs. Because of this, any local model you pass to `--model` **must** be an `mlx-community` model from Hugging Face (e.g. `mlx-community/Meta-Llama-3-8B-Instruct-4bit`) so that it is compatible with the Apple Silicon architecture. `mlx-lm` will **not** run on Intel Macs, Windows, or Linux (in the future, support will be added for Intel/Windows/Linux). On first run the model is pulled from Hugging Face (several GB) and cached under `~/.cache/huggingface`, so the first run is slow and later runs reuse the cache.

If you are not on Apple Silicon, stick with the default Claude model.

## Environment Setup

Requires **Python 3.11**.

```bash
# 1. From the repo root, create and activate a virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 2. Install the Python dependencies
pip install -r utils/requirements.txt
```

### API Key (for running with Claude)

Claude is the **default** model, so to run the script out of the box you need an Anthropic API key. Create a `.env` file in the **root of the repo** and put your key in it:

```bash
# .env (in the repo root)
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

The key is loaded automatically via `python-dotenv` ([utils/helpers.py](../utils/helpers.py) calls `load_dotenv()`). The `.env` file is git‑ignored, so your key will not be committed. If you only ever run local MLX models, no `.env` / API key is needed.

## Usage

You must have the virtual environment activated (`source venv/bin/activate`). Run as a module **from the repo root** (so the `media_analysis` package resolves):

```bash
python3 -m media_analysis.media_analyzer --data-path /path/to/aggregated.json
```

### Arguments

| Flag | Required | Default | Description |
| --- | --- | --- | --- |
| `--data-path` | Yes | — | Path to the aggregated `.json` file produced by `data_aggregator/video_processor.py`. |
| `--output-path` | No | `traveling_reel_summary.json` | Path for the markdown analysis output. (Pass a `.md` path; see note below.) |
| `--model` | No | `claude-sonnet-4-6` | Model used for inference. Use a `claude-*` model to run through Anthropic, or an `mlx-community/...` model to run locally on Apple Silicon. |
| `--analysis-type` | No | `cluster` | The type of analysis to conduct (see [Analysis Types](#analysis-types)). |

### Examples

Run the default `cluster` analysis through Claude (requires `.env` with your API key):

```bash
python3 -m media_analysis.media_analyzer \
  --data-path /Users/christiansarmiento/Desktop/japan_traveling_reel_summary.json \
  --output-path /Users/christiansarmiento/Desktop/japan_cluster_analysis.md
```

If you wanted to change the Claude model:

```bash
python3 -m media_analysis.media_analyzer \
  --data-path /Users/christiansarmiento/Desktop/japan_traveling_reel_summary.json \
  --output-path /Users/christiansarmiento/Desktop/japan_cluster_analysis.md \
  --model claude-haiku-4-5-20251001
```


Run the same analysis locally on Apple Silicon with an MLX model (no API key needed):

```bash
python3 -m media_analysis.media_analyzer \
  --data-path /Users/christiansarmiento/Desktop/japan_traveling_reel_summary.json \
  --output-path /Users/christiansarmiento/Desktop/japan_cluster_analysis.md \
  --model mlx-community/Meta-Llama-3-8B-Instruct-4bit
```

## Notes

- The output is markdown — give `--output-path` a `.md` extension even though the default value is a `.json` filename.
- The default `MAX_TOKENS` is set in [media_analyzer.py](media_analyzer.py); raise it if your analysis is getting truncated for large datasets.
- After each run, generated artifacts and GPU memory buffers are cleaned up automatically (`cleanup()` in [utils/helpers.py](../utils/helpers.py)).
