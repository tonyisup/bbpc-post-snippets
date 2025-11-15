import argparse, orjson, pathlib

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour,\
 OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX,\
 ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL,\
 MarginR, MarginV, Encoding
Style: HostA,Inter,62,&H00FFFFFF,&H0000FFFF,&H00202020,&H00000000,-1,0,0,0,\
 100,100,0,0,1,4,0,2,60,60,80,1
Style: HostB,Inter,62,&H00FFD28C,&H0000FFFF,&H00202020,&H00000000,-1,0,0,0,\
 100,100,0,0,1,4,0,2,60,60,80,1
Style: HostC,Inter,62,&H0086E5FF,&H0000FFFF,&H00202020,&H00000000,-1,0,0,0,\
 100,100,0,0,1,4,0,2,60,60,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect,\
 Text
"""

def ass_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"

def kword(w):
    dur = max(0.01, w["end"] - w["start"])
    cs = int(round(dur * 100))
    token = (w.get("word") or "").replace("{", "\\{").replace("}", "\\}")
    return f"{{\\k{cs}}}{token}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json_in", required=True)
    ap.add_argument("--ass_out", required=True)
    ap.add_argument("--map", default="")
    ap.add_argument("--show_names", action="store_true")
    args = ap.parse_args()

    data = orjson.loads(pathlib.Path(args.json_in).read_bytes())
    spk_map = {}
    if args.map:
        spk_map = orjson.loads(pathlib.Path(args.map).read_bytes())

    lines = [ASS_HEADER]
    for seg in data["segments"]:
        words = seg.get("words") or []
        if not words:
            start, end = seg["start"], seg["end"]
            style = spk_map.get(seg.get("speaker", "SPEAKER_00"),
                                {"style": "HostA"}).get("style", "HostA")
            txt = seg["text"].replace("{", "\\{").replace("}", "\\}")
            dur = max(0.01, end - start)
            lines.append(
                "Dialogue: 0,{},{},{},,,0,0,0,,{{\\k{}}}{}\n".format(
                    ass_time(start), ass_time(end), style, int(dur * 100),
                    txt
                )
            )
            continue

        # Group contiguous words by speaker
        run = []
        cur_spk = None
        for w in words:
            spk = w.get("speaker") or seg.get("speaker") or "SPEAKER_00"
            if spk != cur_spk and run:
                s0, s1 = run[0]["start"], run[-1]["end"]
                style = spk_map.get(cur_spk, {"style": "HostA"}).get(
                    "style", "HostA"
                )
                prefix = ""
                if args.show_names:
                    name = spk_map.get(cur_spk, {}).get("name", cur_spk)
                    prefix = f"{name}: "
                text = prefix + "".join(kword(x) for x in run)
                lines.append(
                    f"Dialogue: 0,{ass_time(s0)},{ass_time(s1)},{style},,,"
                    f"0,0,0,,{text}\n"
                )
                run = []
            cur_spk = spk
            run.append(w)
        if run:
            s0, s1 = run[0]["start"], run[-1]["end"]
            style = spk_map.get(cur_spk, {"style": "HostA"}).get(
                "style", "HostA"
            )
            prefix = ""
            if args.show_names:
                name = spk_map.get(cur_spk, {}).get("name", cur_spk)
                prefix = f"{name}: "
            text = prefix + "".join(kword(x) for x in run)
            lines.append(
                f"Dialogue: 0,{ass_time(s0)},{ass_time(s1)},{style},,,"
                f"0,0,0,,{text}\n"
            )

    pathlib.Path(args.ass_out).write_text("".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
