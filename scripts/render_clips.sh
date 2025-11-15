#!/usr/bin/env bash
set -euo pipefail
AUDIO="$1"      # normalized audio
ASS="$2"
COVER="$3"
CLIPS_JSON="$4"
OUT_DIR="$5"
FPS=30

mkdir -p "$OUT_DIR"

python - <<'PY'
import json, sys, os, orjson
data = orjson.loads(open(sys.argv[1], "rb").read())
for i, c in enumerate(data, 1):
    base = f"clip_{i:02d}"
    print(f"{base}|{c['start']}|{c['end']}|{c['title']}")
PY "$CLIPS_JSON" > "$OUT_DIR/index.tsv"

while IFS='|' read -r NAME START END TITLE; do
  # 9:16 canvas with blurred background + centered square cover
  ffmpeg -y -i "$AUDIO" -loop 1 -i "$COVER" -ss "$START" -to "$END" \
    -filter_complex "
      [1:v]scale=1080:1920:force_original_aspect_ratio=increase,
           crop=1080:1920,
           gblur=sigma=20[bg];
      [1:v]scale=900:-1[cover];
      [bg][cover]overlay=(W-w)/2:200,format=yuv420p[base];
      [0:a]atrim=start=${START}:end=${END},asetpts=PTS-STARTPTS[aud];
      [base]subtitles='${ASS}':fontsdir=./assets/font[vsub];
      [vsub]drawbox=x=0:y=1500:w=1080:h=350:color=black@0.30:t=fill[vbox]
    " -map "[vbox]" -map "[aud]" -c:v libx264 -r $FPS -preset veryfast \
    -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k \
    -movflags +faststart "$OUT_DIR/${NAME}_9x16.mp4"

  # Optional square 1:1 variant
  ffmpeg -y -i "$AUDIO" -loop 1 -i "$COVER" -ss "$START" -to "$END" \
    -filter_complex "
      [1:v]scale=1080:1080:force_original_aspect_ratio=increase,
           crop=1080:1080,
           gblur=sigma=18[bg];
      [1:v]scale=900:-1[cover];
      [bg][cover]overlay=(W-w)/2:(H-h)/2,format=yuv420p[base];
      [0:a]atrim=start=${START}:end=${END},asetpts=PTS-STARTPTS[aud];
      [base]subtitles='${ASS}':fontsdir=./assets/font[vsub]
    " -map "[vsub]" -map "[aud]" -c:v libx264 -r $FPS -preset veryfast \
    -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k \
    -movflags +faststart "$OUT_DIR/${NAME}_1x1.mp4"

done < "$OUT_DIR/index.tsv"
