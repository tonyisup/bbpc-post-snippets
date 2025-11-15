EP ?= episode_012
AUDIO_IN := input/$(EP).mp3
WORK := out/$(EP)
AUDIO_NORM := $(WORK)/audio_norm.m4a
WHISPER_JSON := $(WORK)/transcript.json
ASS := $(WORK)/subs.ass
MAIN_MP4 := $(WORK)/main/$(EP)_1080p.mp4
CLIPS_JSON := $(WORK)/clips/picks.json
HF_TOKEN ?= $(shell cat .hf_token 2>/dev/null)

all: $(MAIN_MP4) clips

$(WORK):
	mkdir -p $(WORK) $(WORK)/main $(WORK)/clips

$(AUDIO_NORM): | $(WORK)
	bash scripts/prep_audio.sh $(AUDIO_IN) $(AUDIO_NORM)

$(WHISPER_JSON): $(AUDIO_NORM) | venv
	HF_TOKEN=$(HF_TOKEN) $PY) scripts/transcribe_diarize_whisperx.py \
		 --audio $(AUDIO_NORM) --out $(WORK)/transcript --num_speakers 3

$(ASS): $(WHISPER_JSON)
	python scripts/ass_from_whisper.py --whisper_json $(WHISPER_JSON) \
		--ass_out $(ASS) --map $(WORK)/speaker_map.json

$(MAIN_MP4): $(AUDIO_NORM) $(ASS)
	bash scripts/render_main.sh $(AUDIO_NORM) $(ASS) assets/cover.png $(MAIN_MP4)

clips: $(CLIPS_JSON)
	bash scripts/render_clips.sh $(AUDIO_NORM) $(ASS) assets/cover.png $(CLIPS_JSON) $(WORK)/clips

$(CLIPS_JSON): $(WHISPER_JSON)
	python scripts/clip_picker.py --whisper_json $(WHISPER_JSON) --out_json $(CLIPS_JSON) --k 10

clean:
	rm -rf $(WORK)
