import argparse, os, orjson, torch, whisperx

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)  # base path (no ext)
    ap.add_argument("--model", default="large-v3")
    ap.add_argument(
        "--device",
        default="cuda" if torch.cuda.is_available() else "cpu",
    )
    ap.add_argument("--num_speakers", type=int, default=3)
    args = ap.parse_args()

    device = args.device
    audio = args.audio
    asr = whisperx.load_model(args.model, device)

    result = asr.transcribe(audio, vad=True)
    lang = result.get("language")

    # Align word timings for better karaoke
    amodel, meta = whisperx.load_align_model(language_code=lang, device=device)
    result = whisperx.align(
        result["segments"],
        amodel,
        meta,
        audio,
        device,
        return_char_alignments=False,
    )

    # Diarization (requires HF token for pyannote)
    token = os.getenv("HF_TOKEN")
    diar = whisperx.DiarizationPipeline(
        use_auth_token=token, device=device
    )
    dia_segs = diar(audio, num_speakers=args.num_speakers)

    # Assign speakers to words
    result = whisperx.assign_word_speakers(dia_segs, result)

    out = {
        "language": lang,
        "segments": result["segments"],
    }
    with open(args.out + ".json", "wb") as f:
        f.write(orjson.dumps(out))

if __name__ == "__main__":
    main()
