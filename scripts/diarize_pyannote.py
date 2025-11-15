import argparse, os, torch, json, orjson, tempfile
from pyannote.audio import Pipeline

ap = argparse.ArgumentParser()
ap.add_argument("--audio", required=True)
ap.add_argument("--out_rttm", required=True)
ap.add_argument("--num_speakers", type=int, default=3)
args = ap.parse_args()

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=os.getenv("HF_TOKEN"),
)
dia = pipeline(args.audio, num_speakers=args.num_speakers)
with open(args.out_rttm, "w") as f:
    dia.write_rttm(f)
