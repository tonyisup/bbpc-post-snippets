# scripts/ass_from_whisper.py
import argparse, orjson, pathlib

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Subs,Inter,62,&H00FFFFFF,&H0000FFFF,&H001E1E1E,&H00000000,-1,0,0,0,100,100,0,0,1,4,0,2,60,60,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def ass_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"

def build_kara_line(seg):
    # Use \k for centiseconds. Highlight words progressively.
    # If no word timing, fall back to whole segment duration.
    words = seg.get("words") or []
    if not words:
        dur = max(0.01, seg["end"] - seg["start"])
        cs = int(round(dur * 100))
        text = seg["text"].replace("{", "\\{").replace("}", "\\}")
        return f"{{\\k{cs}}}{text}"

    parts = []
    for w in words:
        wdur = max(0.01, (w["end"] - w["start"]))
        cs = int(round(wdur * 100))
        token = (w["word"] or "").replace("{", "\\{").replace("}", "\\}")
        parts.append(f"{{\\k{cs}}}{token}")
    return "".join(parts)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--whisper_json", required=True)
    ap.add_argument("--ass_out", required=True)
    ap.add_argument("--style_name", default="Subs")
    args = ap.parse_args()

    data = orjson.loads(pathlib.Path(args.whisper_json).read_bytes())
    lines = [ASS_HEADER]
    for seg in data["segments"]:
        text = build_kara_line(seg)
        start = ass_time(seg["start"])
        end = ass_time(seg["end"])
        evt = f"Dialogue: 0,{start},{end},{args.style_name},,0,0,0,,{text}\n"
        lines.append(evt)

    pathlib.Path(args.ass_out).write_text("".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
