#!/usr/bin/env bash
set -euo pipefail
IN="$1"
T="$2"
OUT="$3"
ffmpeg -y -ss "$T" -i "$IN" -frames:v 1 -q:v 2 "$OUT"
