import argparse, orjson, math, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def windows_from_segments(segments, min_s=30, max_s=90, stride_s=10):
    # Build windows aligned to segment boundaries, expanding until within range
    windows = []
    n = len(segments)
    starts = list(range(0, n, max(1, int(stride_s / 3))))
    for si in starts:
        t0 = segments[si]["start"]
        text = []
        t1 = t0
        for ei in range(si, n):
            t1 = segments[ei]["end"]
            text.append(segments[ei]["text"])
            dur = t1 - t0
            if dur >= min_s:
                if dur <= max_s:
                    windows.append(
                        {"si": si, "ei": ei, "start": t0, "end": t1,
                         "text": " ".join(text)}
                    )
                else:
                    break
    return windows

def boundaries_penalty(seg_before, seg_after):
    # Favor windows that start/end near pauses (>= 250ms)
    p = 0.0
    if seg_before:
        gap = max(0.0, seg_before["end"] - seg_before["start"])  # placeholder
    if seg_after:
        pass
    return p

def score_windows(windows, corpus_tf, vectorizer):
    X = vectorizer.transform([w["text"] for w in windows]).toarray()
    # Content richness: L2 norm of tf-idf
    richness = np.linalg.norm(X, axis=1)
    # Question bonus
    q_bonus = np.array([0.2 if "?" in w["text"] else 0.0 for w in windows])
    # Numbers bonus
    num_bonus = np.array([0.15 if any(ch.isdigit() for ch in w["text"]) else 0.0
                          for w in windows])
    # Length prior centered at 55s
    lengths = np.array([w["end"] - w["start"] for w in windows])
    length_prior = np.exp(-((lengths - 55.0) ** 2) / (2 * 12.0 ** 2))

    base = 1.0 * richness + q_bonus + num_bonus + 0.5 * length_prior
    return base

def diversify_pick(windows, scores, k=10):
    chosen = []
    used = np.zeros(len(windows), dtype=bool)
    # Greedy with minimum temporal distance of 45s
    for _ in range(k):
        idx = np.argmax(np.where(~used, scores, -1e9))
        if scores[idx] < 0:
            break
        chosen.append(idx)
        # suppress nearby windows
        start, end = windows[idx]["start"], windows[idx]["end"]
        for j, w in enumerate(windows):
            if not used[j]:
                if (abs(w["start"] - start) < 45) or (abs(w["end"] - end) < 45):
                    used[j] = True
        used[idx] = True
    return [windows[i] for i in chosen]

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
    segments = data["segments"]
    windows = windows_from_segments(segments, args.min_s, args.max_s, args.stride_s)

    corpus = [" ".join(s["text"] for s in segments)]
    vect = TfidfVectorizer(stop_words="english", max_features=8192)
    vect.fit(corpus)

    scores = score_windows(windows, None, vect)
    picks = diversify_pick(windows, scores, args.k)

    for p in picks:
        p["title"] = p["text"][:80].strip().rstrip(",;:-") + "…"

    open(args.out_json, "wb").write(orjson.dumps(picks))

if __name__ == "__main__":
    main()
