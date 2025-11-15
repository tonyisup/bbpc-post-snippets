#!/usr/bin/env bash
set -euo pipefail

AUDIO="$1"           # normalized audio
ASS="$2"             # subtitles.ass
COVER="$3"           # cover.png
OUT="$4"             # mp4 path
TITLE="${5:-}"       # optional overlay title text
FPS=30
W=1920
H=1080

# Build a background by scaling and blurring cover, overlay sharp cover left
ffmpeg -y -i "$AUDIO" -loop 1 -i "$COVER" -filter_complex "
  [1:v]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},gblur=sigma=20[bg];
  [1:v]scale=900:-1[cover];
  [bg][cover]overlay=60:60,format=yuv420p[base];
  anullsrc=r=48000:cl=stereo [sil];
" -map "[base]" -map 0:a -c:v libx264 -r $FPS -pix_fmt yuv420p -shortest \
  -preset veryfast -crf 18 -movflags +faststart temp_base.mp4

# Add waveform and subtitles
ffmpeg -y -i temp_base.mp4 -vf "
  [0:v]drawbox=x=0:y=860:w=${W}:h=220:color=black@0.25:t=fill[bg2];
  [0:a]showwaves=mode=line:s=${W}x200:colors=0x00FFFF[sw];
  [bg2][sw]overlay=(W-w)/2:870:shortest=1,subtitles='${ASS}':fontsdir=./assets/font
  " -c:v libx264 -preset veryfast -crf 18 -r $FPS -pix_fmt yuv420p \
  -c:a copy -movflags +faststart "$OUT"

rm -f temp_base.mp4
