# Makefile (80-col friendly)
EP ?= episode_012

# Tools
PY := ./.venv/bin/python
PIP := ./.venv/bin/pip

# Inputs/Outputs
AUDIO_IN := input/$(EP).mp3
WORK := out/$(EP)
AUDIO_NORM := $(WORK)/audio_norm.m4a
WHISPER_JSON := $(WORK)/transcript.json
ASS := $(WORK)/subs.ass
MAIN_MP4 := $(WORK)/main/$(EP)_1080p.mp4
CLIPS_JSON := $(WORK)/clips/picks.json
CLIPS_DIR := $(WORK)/clips

# Auth
HF_TOKEN ?= $(shell cat .hf_token 2>/dev/null)

# Default
all: $(MAIN_MP4) clips

# Setup
venv:
	python -m venv .venv
	$(PY) -m pip install -U pip wheel setuptools
	$(PIP) install -r requirements.txt

dirs:
	mkdir -p $(WORK) $(WORK)/main $(WORK)/clips

# Audio prep
$(AUDIO_NORM): $(AUDIO_IN) | dirs
	bash scripts/prep_audio.sh $(AUDIO_IN) $(AUDIO_NORM)

# Transcribe + diarize (WhisperX end-to-end)
$(WHISPER_JSON): $(AUDIO_NORM) | venv
	HF_TOKEN=$(HF_TOKEN) $(PY) scripts/transcribe_diarize_whisperx.py \
	  --audio $(AUDIO_NORM) --out $(WORK)/transcript --num_speakers 3

# ASS with speaker styles
$(ASS): $(WHISPER_JSON)
	$(PY) scripts/ass_from_diarized.py \
	  --json_in $(WHISPER_JSON) --ass_out $(ASS)

# Main video render
$(MAIN_MP4): $(AUDIO_NORM) $(ASS) | dirs
	bash scripts/render_main.sh $(AUDIO_NORM) $(ASS) assets/cover.png \
	  $(MAIN_MP4)

# Clip discovery and render
$(CLIPS_JSON): $(WHISPER_JSON) | venv
	$(PY) scripts/clip_picker.py --whisper_json $(WHISPER_JSON) \
	  --out_json $(CLIPS_JSON) --k 10

clips: $(CLIPS_JSON) $(AUDIO_NORM) $(ASS) | dirs
	bash scripts/render_clips.sh $(AUDIO_NORM) $(ASS) assets/cover.png \
	  $(CLIPS_JSON) $(CLIPS_DIR)

# Utilities
chapters:
	$(PY) scripts/make_chapters.py --whisper_json $(WHISPER_JSON) \
	  --out_txt $(WORK)/chapters.txt

clean:
	rm -rf $(WORK)

.PHONY: all venv dirs clips chapters clean
