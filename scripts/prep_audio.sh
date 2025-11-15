#!/usr/bin/env bash
set -euo pipefail
IN="$1"; OUT="$2"
ffmpeg -y -i "$IN" -af loudnorm=I=-16:LRA=--:TP=-1.5:measred_I=-16 \
	-c:a aac -b:a 192k "$OUT"
