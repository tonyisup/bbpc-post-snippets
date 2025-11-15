import argparse, orjson

def fmt(ts):
    h = int(ts // 3600)
    m = int((ts % 3600) // 60)
    s = int(ts % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--whisper_json", required=True)
    ap.add_argument("--out_txt", required=True)
    args = ap.parse_args()

    data = orjson.loads(open(args.whisper_json, "rb").read())
    lines = []
    for i, s in enumerate(data["segments"]):
        if i % 10 == 0:
            lines.append(f"{fmt(s['start'])} Chapter {len(lines) + 1}")
    open(args.out_txt, "w").write("\n".join(lines))

if __name__ == "__main__":
    main()
