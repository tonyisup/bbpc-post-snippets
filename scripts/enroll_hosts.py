# scripts/enroll_hosts.py
import argparse, orjson, numpy as np, torch
from pyannote.audio import Model
from pyannote.audio.pipelines.utils.hook import ProgressHook
from pyannote.audio import Inference

ap = argparse.ArgumentParser()
ap.add_argument("--refs", nargs="+", required=True)  # pairs: name=wavpath
ap.add_argument("--out", required=True)
args = ap.parse_args()

infer = Inference("pyannote/embedding", window="whole")
enroll = {}
for pair in args.refs:
    name, path = pair.split("=", 1)
    emb = infer(path)
    enroll[name] = emb.tolist()
open(args.out,"wb").write(orjson.dumps(enroll))
