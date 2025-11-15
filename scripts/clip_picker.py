import argparse, orjson, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def windows_from_segments(segments, min_s=30, max_s=90, stride_s=10):
    wins = []
    n = len(segments)
    step = max(1, int(stride_s / 3))
    for si in range(0, n, step):
        t0 = segments[si]["start"]
        text = []
        t1 = t0
        for ei in range(si, n):
            t1 = segments[ei]["end"]
            text.append(segments[ei]["text"])
            dur = t1 - t0
            if dur >= min_s:
                if dur <= max_s:
                    wins.append(
                        {"si": si, "ei": ei, "start": t0, "end": t1,
                         "text": " ".join(text)}
                    )
                else:
                    break
    return wins

def score_windows(wins, vectorizer):
    X = vectorizer.transform([w["text"] for w in wins]).toarray()
    rich = np.linalg.norm(X, axis=1)
    q = np.array([0.2 if "?" in w["text"] else 0.0 for w in wins])
    num = np.array([0.15 if any(c.isdigit() for c in w["text"]) else 0.0
                    for w in wins])
    lengths = np.array([w["end"] - w["start"] for w in wins])
    lp = np.exp(-((lengths - 55.0) ** 2) / (2 * 12.0 ** 2))
    return 1.0 * rich + q + num + 0.5 * lp

def diversify_pick(wins, scores, k=10):
    chosen = []
    used = np.zeros(len(wins), dtype=bool)
    for _ in range(k):
        idx = np.argmax(np.where(~used, scores, -1e9))
        if scores[idx] < 0:
            break
        chosen.append(idx)
        s, e = wins[idx]["start"], wins[idx]["end"]
        for j, w in enumerate(wins):
            if not used[j]:
                if (abs(w["start"] - s) < 45) or (abs(w["end"] - e) < 45):
                    used[j] = True
        used[idx] = True
    return [wins[i] for i in chosen]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--whisper_json", required=True)
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--min_s", type=float, default=30.0)
    ap.add_argument("--max_s", type=float, default=90.0)
    ap.add_argument("--stride_s", type=float, default=10.0)
    ap.add_argument("--k", type=int, default=10)
    args = ap.parse_args()

    data = orjson.loads(open(args.whisper_json, "rb").read())
    segs = data["segments"]

    corpus = [" ".join(s["text"] for s in segs)]
    vect = TfidfVectorizer(stop_words="english", max_features=8192).fit(corpus)

    wins = windows_from_segments(segs, args.min_s, args.max_s, args.stride_s)
    scores = score_windows(wins, vect)
    picks = diversify_pick(wins, scores, args.k)
    for p in picks:
        p["title"] = p["text"][:80].strip().rstrip(",;:-") + "…"

    open(args.out_json, "wb").write(orjson.dumps(picks))

if __name__ == "__main__":
    main()
