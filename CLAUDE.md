# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a podcast post-processing pipeline that transforms raw podcast audio (MP3) into polished video content with karaoke-style subtitles. The pipeline performs transcription, speaker diarization, subtitle generation (ASS format), and renders both a full-length video and multiple optimized clips for social media.

## Key Dependencies

- **WhisperX**: End-to-end speech recognition with word-level timing and speaker diarization
- **pyannote.audio**: Speaker diarization (requires Hugging Face token with pyannote access)
- **FFmpeg**: Audio normalization and video rendering with complex filters
- **scikit-learn**: TF-IDF vectorization for clip discovery
- Python libraries: orjson, numpy, pandas, spacy, nltk, rich

## Setup Commands

```bash
# Initial setup
cp .env.example .env  # or create .hf_token with your HF token
make venv             # Creates virtual environment and installs dependencies

# For GPU support (optional)
# After make venv, install PyTorch matching your CUDA version manually
```

## Core Workflow

The standard workflow is driven by Make:

```bash
# Full pipeline for a single episode
EP=episode_012 make all

# This runs:
# 1. Audio normalization (loudnorm)
# 2. WhisperX transcription + diarization
# 3. ASS subtitle generation
# 4. Main video render (1080p)
# 5. Clip discovery and rendering (9:16 and 1:1 formats)
```

### Individual Pipeline Steps

```bash
# Run specific steps (requires EP variable)
EP=episode_012 make $(WORK)/audio_norm.m4a   # Audio prep only
EP=episode_012 make $(WORK)/transcript.json  # Transcribe + diarize only
EP=episode_012 make $(WORK)/subs.ass         # Generate subtitles only
EP=episode_012 make $(WORK)/main/episode_012_1080p.mp4  # Main video only
EP=episode_012 make clips                    # Clips only
EP=episode_012 make chapters                 # Generate chapter markers

# Clean outputs for an episode
EP=episode_012 make clean
```

## Architecture

### Data Flow

```
input/episode_012.mp3
  → [prep_audio.sh] → audio_norm.m4a (loudness normalized)
  → [transcribe_diarize_whisperx.py] → transcript.json (segments with word timings + speakers)
  → [ass_from_diarized.py] → subs.ass (karaoke-style subtitles with speaker colors)
  → [render_main.sh] → main/episode_012_1080p.mp4 (full video)

transcript.json
  → [clip_picker.py] → clips/picks.json (scored, diverse clip selections)
  → [render_clips.sh] → clips/clip_01_9x16.mp4, clip_01_1x1.mp4, ...
```

### Key Scripts

**transcribe_diarize_whisperx.py**
- End-to-end WhisperX pipeline: ASR → word alignment → diarization
- Requires HF_TOKEN environment variable for pyannote models
- Outputs JSON with segments containing word-level timings and speaker labels
- Default: large-v3 model, 3 speakers, auto device selection (CUDA/CPU)

**ass_from_diarized.py**
- Converts diarized transcript JSON to ASS subtitle format
- Generates karaoke-style word-by-word highlighting with `{\k}` tags
- Maps speakers to predefined styles (HostA: white, HostB: orange, HostC: blue)
- Supports optional speaker name mapping via `--map` JSON file
- Groups contiguous words by speaker into dialogue lines

**clip_picker.py**
- Sliding window approach to discover interesting 30-90s clips
- Scoring algorithm combines:
  - TF-IDF richness (keyword density)
  - Question detection (bonus for "?")
  - Number mentions (bonus for digits)
  - Length preference (Gaussian centered at 55s)
- Diversification ensures clips don't overlap within 45s
- Default: top 10 clips with 10s stride

**render_main.sh**
- Two-pass rendering: base video with cover + waveform/subtitles overlay
- Background: blurred cover scaled to 1920x1080
- Foreground: sharp cover image (900px) at top-left
- Waveform: cyan line waveform over semi-transparent black box
- Subtitles: ASS format with custom fonts from assets/font/

**render_clips.sh**
- Generates two aspect ratios per clip: 9:16 (vertical) and 1:1 (square)
- Uses TSV index generated from picks.json
- Temporal trimming with FFmpeg atrim/asetpts for clean clip extraction
- 9:16: Cover centered at top with subtitle box at bottom
- 1:1: Cover centered in frame

### File Formats

**transcript.json** (WhisperX output)
```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.5,
      "end": 3.2,
      "text": "Welcome to the show",
      "words": [
        {"start": 0.5, "end": 0.8, "word": "Welcome", "speaker": "SPEAKER_00"},
        {"start": 0.9, "end": 1.0, "word": "to", "speaker": "SPEAKER_00"}
      ]
    }
  ]
}
```

**picks.json** (clip_picker.py output)
```json
[
  {
    "si": 12,
    "ei": 18,
    "start": 45.3,
    "end": 102.8,
    "text": "Full transcript text...",
    "title": "Truncated title for display..."
  }
]
```

**Speaker mapping JSON** (optional, for --map flag)
```json
{
  "SPEAKER_00": {"name": "Alice", "style": "HostA"},
  "SPEAKER_01": {"name": "Bob", "style": "HostB"}
}
```

## Speaker Identity Mapping (Advanced)

To maintain consistent speaker identities across episodes:

1. **Enrollment**: Extract embeddings from reference audio
   ```bash
   $(PY) scripts/enroll_hosts.py --refs Alice=alice.wav Bob=bob.wav --out enrolled.json
   ```

2. **Mapping**: Match diarized clusters to enrolled speakers
   ```bash
   $(PY) scripts/map_clusters.py --rttm episode.rttm --audio audio.m4a \
     --enroll_json enrolled.json --out_map speaker_map.json
   ```

3. **Generate subtitles with mapping**
   ```bash
   $(PY) scripts/ass_from_diarized.py --json_in transcript.json \
     --ass_out subs.ass --map speaker_map.json --show_names
   ```

## Directory Structure

```
input/              # Source MP3 files
out/
  episode_012/
    audio_norm.m4a  # Normalized audio
    transcript.json # WhisperX output
    subs.ass        # Subtitles
    main/
      episode_012_1080p.mp4
    clips/
      picks.json
      index.tsv
      clip_01_9x16.mp4
      clip_01_1x1.mp4
      ...
assets/
  cover.png         # Required: episode cover art (referenced by render scripts)
  font/             # Optional: custom fonts for ASS rendering
```

## Common Modifications

**Adjust clip parameters**
```bash
EP=episode_012 $(PY) scripts/clip_picker.py \
  --whisper_json out/episode_012/transcript.json \
  --out_json out/episode_012/clips/picks.json \
  --min_s 45 --max_s 60 --k 15
```

**Change number of speakers**
Edit Makefile line 40 or run manually:
```bash
HF_TOKEN=$(HF_TOKEN) $(PY) scripts/transcribe_diarize_whisperx.py \
  --audio audio_norm.m4a --out transcript --num_speakers 2
```

**Customize subtitle styles**
Edit ASS_HEADER in scripts/ass_from_diarized.py (lines 3-25) to modify:
- Font family/size
- Colors (in BGR hex format: &H00BBGGRR)
- Outline/shadow thickness
- Positioning (MarginL/MarginR/MarginV)

**Modify video rendering**
- render_main.sh: Adjust cover scale/position, waveform colors, box transparency
- render_clips.sh: Change aspect ratios, crop regions, subtitle positioning

## Python Virtual Environment

All Python scripts should be run via `.venv/bin/python` (aliased as `$(PY)` in Makefile). The Makefile handles this automatically. If running scripts manually outside Make, activate the venv first or use the full path.

## FFmpeg Notes

- All render scripts use `-preset veryfast` for speed; change to `medium` or `slow` for better compression
- CRF values: main=18 (high quality), clips=20 (good quality)
- Audio: AAC 192k for main, 160k for clips
- Fonts: Place custom fonts in `assets/font/` and reference via `fontsdir=./assets/font`
