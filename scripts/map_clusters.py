# scripts/map_clusters.py
import argparse, orjson, numpy as np
from pyannote.audio import Inference
from pyannote.core import Annotation, Segment

def cluster_centroids(rttm):
    from pyannote.core import Annotation
    ann = Annotation()
    with open(rttm) as f:
        for line in f:
            if not line.strip() or line.startswith("#"): continue
            p = line.split()
            ann[Segment(float(p[3]), float(p[3])+float(p[4])), p[7]] = 1
    return {spk: [(seg.start, seg.end) for seg in ann.get_timeline().support().uri]
            for spk in ann.labels()}

ap = argparse.ArgumentParser()
ap.add_argument("--rttm", required=True)
ap.add_argument("--audio", required=True)
ap.add_argument("--enroll_json", required=True)
ap.add_argument("--out_map", required=True)
args = ap.parse_args()

infer = Inference("pyannote/embedding", window="whole")
with open(args.enroll_json,"rb") as f:
    enroll = orjson.loads(f.read())
enroll_vecs = {k: np.asarray(v) for k,v in enroll.items()}

# Simple approach: sample a few speech regions per cluster and average embeddings
from pyannote.core import Annotation, Segment
ann = Annotation()
with open(args.rttm) as f:
    for line in f:
        p = line.split()
        ann[Segment(float(p[3]), float(p[3])+float(p[4])), p[7]] = 1

mapping = {}
for spk in ann.labels():
    spans = list(ann.label_timeline(spk).support().itersegments())
    spans = spans[:5]  # sample
    embs = []
    for s in spans:
        emb = infer.crop(args.audio, s)
        embs.append(emb)
    centroid = np.mean(np.stack(embs), axis=0)
    # map to enrolled host
    best, best_sim = None, -1
    for name, vec in enroll_vecs.items():
        sim = float(np.dot(centroid, vec) / (np.linalg.norm(centroid)*np.linalg.norm(vec)))
        if sim > best_sim:
            best, best_sim = name, sim
    mapping[spk] = {"name": best, "style": {"Alice":"HostA","Bob":"HostB","Carol":"HostC"}.get(best,"HostA"), "sim": best_sim}

open(args.out_map,"wb").write(orjson.dumps(mapping))
