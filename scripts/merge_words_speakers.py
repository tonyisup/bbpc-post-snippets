# scripts/merge_words_speakers.py
import argparse, orjson
from pyannote.core import Annotation, Segment
from pyannote.core.annotation import Annotation as Ann

def load_rttm(path):
    ann = Annotation()
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith("#"): continue
            parts = line.strip().split()
            # RTTM: SPEAKER <uri> 1 <start> <dur> <..> <speaker>
            start = float(parts[3]); dur = float(parts[4])
            spk = parts[7]
            ann[Segment(start, start+dur), spk] = 1
    return ann

ap = argparse.ArgumentParser()
ap.add_argument("--whisper_json", required=True)
ap.add_argument("--rttm", required=True)
ap.add_argument("--out_json", required=True)
args = ap.parse_args()

data = orjson.loads(open(args.whisper_json,"rb").read())
ann = load_rttm(args.rttm)

for seg in data["segments"]:
    # assign per word; fallback to segment speaker by majority overlap
    words = seg.get("words") or []
    if words:
        for w in words:
            t0, t1 = w["start"], w["end"]
            winners = ann.crop(Segment(t0, t1)).labels()
            if winners:
                # choose label with max overlap
                best = max(winners, key=lambda sp: ann.crop(Segment(t0,t1)).label_duration(sp))
                w["speaker"] = best
    # segment-level speaker as majority over its span
    t0, t1 = seg["start"], seg["end"]
    winners = ann.crop(Segment(t0, t1)).labels()
    if winners:
        best = max(winners, key=lambda sp: ann.crop(Segment(t0,t1)).label_duration(sp))
        seg["speaker"] = best

open(args.out_json,"wb").write(orjson.dumps(data))
