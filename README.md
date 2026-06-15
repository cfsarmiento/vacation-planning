# Vacation Planning

A growing toolkit for turning the messy pile of content you collect while researching a trip — saved Instagram reels, videos, and other sources — into structured, searchable data you can actually plan from.

The idea: you gather a lot of information about a place you want to visit (good restaurants, attractions, nightlife, neighborhoods, etc.) but never have time to sift through it all. These tools ingest that raw content, use AI to summarize and structure it, and then run higher-level analysis on top so the signal is easy to find. Each tool is a self-contained script under its own directory and can be run on its own or chained into a pipeline, with output from one feeding the next.

## Tools

Each tool lives in its own directory with a detailed README. Below is the high-level view of what's **currently** here.

### `data_aggregator/` — Media ingestion & summarization

Takes a folder of Instagram reels/posts (or any `.mp4` files) and turns each one into a structured summary. Every video is run through three local Apple-Silicon (MLX) models to extract:

- an **audio transcript** (Whisper),
- a **visual summary** of sampled frames — restaurant names, places, neighborhoods, locations (vision-language model),
- a **title and concise summary** combining the two (LLM).

Everything is aggregated into a single JSON file keyed by generated title — the input for downstream analysis. See [data_aggregator/README.md](data_aggregator/README.md).

> Runs **only on a Mac with Apple Silicon (M-series)**, since inference is local via MLX.

### `media_analysis/` — Cross-content analysis

Runs deeper AI analysis over the aggregated JSON from `data_aggregator` and writes a structured markdown report. The current analysis type is **`cluster`** — it finds natural groupings in the data (e.g. clusters of related spots), explains why they group, diagrams how they relate, and produces an executive summary with insights and outliers.

Inference runs either **remotely through Claude** (the default — works on any platform) or **locally through an MLX model** on Apple Silicon, selected via the `--model` flag. See [media_analysis/README.md](media_analysis/README.md).

An example output is checked in at [japan_travel_collection_cluster_analysis.md](japan_travel_collection_cluster_analysis.md).

## Setup

Setup is shared across the tools.

**Requirements:** Python 3.11, and the [`ffmpeg`](https://ffmpeg.org/) system binary (used by `data_aggregator` for audio extraction).

```bash
# From the repo root: create and activate a virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r utils/requirements.txt

# Install ffmpeg (system binary, not a pip package) — macOS:
brew install ffmpeg
```

### API key

Only needed when running inference **through Claude** (the default for `media_analysis`). Create a `.env` file in the repo root:

```bash
# .env (repo root)
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

It's loaded automatically and is git-ignored. If you only ever run local MLX models, no API key is needed.

### Differences between tools

- **`data_aggregator`** requires Apple Silicon (all inference is local MLX) and needs `ffmpeg`.
- **`media_analysis`** runs on any platform when using the default Claude model; local MLX models are an Apple-Silicon-only option.

Run each tool as a module **from the repo root** so its package resolves, e.g.:

```bash
python3 -m data_aggregator.video_processor --data-path /path/to/mp4s
python3 -m media_analysis.media_analyzer --data-path /path/to/aggregated.json
```

See each tool's README for full arguments, examples, and hardware notes.
