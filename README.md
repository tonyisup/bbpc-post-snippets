Podcast pipeline (local, Arch Linux)

Prereqs (system):
  sudo pacman -S ffmpeg sox imagemagick fontconfig python python-pip \
    python-virtualenv

Setup:
  cp .env.example .env   # or create .hf_token with your token only
  # add HF_TOKEN to your environment or populate .hf_token
  make venv

Usage:
  # Put your episode MP3 in input/
  EP=episode_012 make all

Outputs:
  out/episode_012/main/episode_012_1080p.mp4
  out/episode_012/clips/clip_01_9x16.mp4, clip_01_1x1.mp4, ...

Notes:
  - Diarization is via WhisperX + pyannote; requires a Hugging Face token.
  - To keep speaker identities consistent across episodes, use the optional
    enrollment scripts to map clusters to named hosts and pass --map to
    ass_from_diarized.py.
  - For GPU, install torch matching your CUDA in the venv.
