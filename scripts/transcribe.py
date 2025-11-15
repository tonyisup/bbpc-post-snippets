import argparse, json, orjson, os
from faster_whisper import WhisperModel

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)  # base path without extension
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--device", default="auto")  # "cuda" or "cpu"
    ap.add_argument("--beam_size", type=int, default=5)
    args = ap.parse_args()

    model = WhisperModel(args.model, device=args.device, compute_type="auto")

    segments, info = model.transcribe(
        args.audio,
        vad_filter=True,
        word_timestamps=True,
        beam_size=args.beam_size,
        language=None,
    )

    segs = []
    for s in segments:
        segs.append(
            {
                "start": s.start,
                "end": s.end,
                "text": s.text.strip(),
                "words": [
                    {
                        "start": w.start,
                        "end": w.end,
                        "word": w.word,
                        "prob": getattr(w, "probability", None),
                    }
                    for w in (s.words or [])
                ],
            }
        )

    meta = {
        "duration": info.duration,
        "language": info.language,
        "segments": segs,
    }

    with open(args.out + ".json", "wb") as f:
        f.write(orjson.dumps(meta))

if __name__ == "__main__":
    main()
