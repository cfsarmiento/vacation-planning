# Instagram Reel/Video Processor for Vacation Planning

Do you have a really large collection of Instagram reels/posts for a place you plan to travel to with all the good information about the location such as good resturants, attractions, nighlife, etc. with no time to actually go through it all? This script helps aggregate that information for further analysis and summarization. Process Instagram reels/posts or any `.mp4` file (scraped via the [*Instagram Saved Posts Organizer* Chrome extension](https://chromewebstore.google.com/detail/instagram-saved-posts-org/onbfnpknejpalckpjlgoglpfejckimhb)) into structured, searchable summaries. Each `.mp4` is run through three local Apple‑Silicon (MLX) models to produce a title, a concise summary, the raw audio transcript, and a visual summary — all aggregated into a single JSON file.

## Pipeline

For every `.mp4` in the target folder, [video_processor.py](video_processor.py) drives [utils/proccessing.py](utils/proccessing.py) to:

1. **Audio** — extract a 16 kHz `.wav` with `ffmpeg` and transcribe it with `mlx-community/whisper-large-v3-turbo`.
2. **Video** — sample frames (1 every 3s, capped at 12) and summarize them with the vision lanuguage model (VLM) `mlx-community/Qwen2-VL-2B-Instruct-4bit`, extracting restaurant names, places, neighborhoods, locations, and any other pertienet information.
3. **Summarize** — combine the transcript and visual summary with the LLM `mlx-community/Qwen3-8B-4bit` to generate a Title‑Cased title and a concise summary.

Results are written to a JSON object keyed by a generated title:

```json
{
  "Some Generated Title": {
    "summary": "...",
    "audio_transcript": "...",
    "video_summary": "..."
  }
}
```

## Hardware Considerations

> **This only runs on a Mac with Apple Silicon (M‑series).**

The pipeline is built on [MLX](https://github.com/ml-explore/mlx), Apple's array framework for Apple‑Silicon GPUs. `mlx-whisper`, `mlx-vlm`, and `mlx-lm` will **not** run on Intel Macs, Windows, or Linux.

- **Chip:** Apple Silicon (M1 or newer).
- **Memory:** 16 GB unified memory recommended. Three models are loaded; the frame cap (`max_frames = 12` in [utils/proccessing.py](utils/proccessing.py)) exists to keep the VLM from running out of memory — lower it if you hit memory pressure.
- **Disk:** The models are pulled from Hugging Face on first run (several GB total) and cached under `~/.cache/huggingface`. The first run is slow; later runs reuse the cache.

## Environment Setup

Requires **Python 3.11** and the **ffmpeg** system binary.

```bash
# 1. From the repo root, create and activate a virtual environment
python3.11 -m venv media_parsing/venv
source media_parsing/venv/bin/activate

# 2. Install the Python dependencies
pip install -r media_parsing/utils/requirements.txt

# 3. Install ffmpeg (system binary, not a pip package)
brew install ffmpeg
```

Verify ffmpeg is on your `PATH`:

```bash
ffmpeg -version
```

## Usage

Run as a module **from the repo root** (so the `media_parsing` package resolves):

```bash
python3 -m media_parsing.video_processor --data-path /path/to/your/mp4s
```

### Arguments

| Flag | Required | Default | Description |
| --- | --- | --- | --- |
| `--data-path` | Yes | — | Folder containing the `.mp4` files to process. |
| `--output-path` | No | `japan_traveling_reel_summary.json` | Path for the final aggregated JSON output. |

### Examples

Process every `.mp4` in a folder (output goes to the default `traveling_reel_summary.json` in the current directory):

```bash
python3 -m media_parsing.video_processor --data-path /Users/christiansarmiento/Desktop/tmp
```

Process a folder and write the output to a specific path:

```bash
python3 -m media_parsing.video_processor \
  --data-path /Users/christiansarmiento/Desktop/tmp \
  --output-path /Users/christiansarmiento/Desktop/tmp/traveling_reel_summary.json
```

## Notes

- Intermediate artifacts (`audio.wav` and the `frames/` directory) are created in the current working directory and cleaned up automatically after each video.
- Only files matching `*.mp4` in the top level of `--data-path` are processed (subfolders are not searched). If no `.mp4` files are found, an empty JSON object is written.
