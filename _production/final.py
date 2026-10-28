"""Akashnir - titles (ASS, Google Sans, Bangla complex shaping) + conform + finishing pass + master encode."""
import subprocess, os, sys
import edl

FPS = edl.FPS
OUT = sys.argv[1] if len(sys.argv) > 1 else r"X:/lis cd/New folder/Akashnir_ChadBagan_Documentary_v3_1080p.mp4"
PREVIEW = os.environ.get("PREVIEW")             # "start,end" seconds -> quick check render

# ------------------------------------------------------------------ titles
def ts(t):
    t = max(t, 0); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

WHITE = "&H00E4EDF3"        # warm off-white
ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Place,Google Sans Medium,128,{WHITE},{WHITE},&H70000000,&H00000000,0,0,0,0,106,100,0,0,1,4,0,5,0,0,0,1
Style: Line,Google Sans,68,{WHITE},{WHITE},&H58000000,&H00000000,0,0,0,0,105,100,0,0,1,4,0,2,0,0,214,1
Style: Fact,Google Sans Medium,92,{WHITE},{WHITE},&H58000000,&H00000000,0,0,0,0,105,100,0,0,1,4.5,0,2,0,0,214,1
Style: Lower,Google Sans,42,{WHITE},{WHITE},&H58000000,&H00000000,0,0,0,0,104,100,0,0,1,4,0,1,170,0,214,1
Style: Credit,Google Sans,46,&H10E4EDF3,{WHITE},&HFF000000,&H00000000,0,0,0,0,104,100,0,0,1,0,0,5,0,0,0,1
Style: Small,Google Sans,40,&H30E4EDF3,{WHITE},&HFF000000,&H00000000,0,0,0,0,104,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
FADES = {"Place": (900, 900), "Line": (700, 700), "Fact": (500, 550),
         "Lower": (600, 700), "Credit": (1000, 900), "Small": (1000, 1000)}
POS = {"Place": r"\pos(960,300)"}

def write_ass(path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(ASS_HEAD)
        for a, b, style, text in edl.TEXT:
            fi, fo = FADES[style]
            tags = rf"\fad({fi},{fo})" + POS.get(style, "")
            if style in ("Line", "Lower", "Place", "Fact"):
                tags += r"\blur8"
            f.write(f"Dialogue: 0,{ts(a)},{ts(b)},{style},,0,0,0,,{{{tags}}}{text}\n")

# ------------------------------------------------------------------ conform list (shots + black slugs)
def slug(name, dur):
    p = f"shots/{name}.mkv"
    n = round(dur * FPS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1920x804:r={FPS}",
                    "-frames:v", str(n), "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p10le",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv", p], check=True)
    return p

def conform_list():
    items = [slug("_black_head", edl.SHOTS[0]["t0"])]
    prev_end = edl.SHOTS[0]["t0"]
    for s in edl.SHOTS:
        if s["t0"] - prev_end > 1e-6:
            items.append(slug(f"_black_{s['id']}", s["t0"] - prev_end))
        items.append(f"shots/{s['id']}.mkv"); prev_end = s["t1"]
    items.append(slug("_black_tail", edl.END - prev_end))
    with open("render/conform.txt", "w") as f:
        for p in items: f.write(f"file '../{p}'\n")
    return "render/conform.txt"

# ------------------------------------------------------------------ title artwork canvases
def title_canvases():
    """Place each title PNG (cropped to its lettering) on a transparent 1920x804 canvas."""
    from PIL import Image
    paths = []
    for i, (png, *_, w, cx, cy, _op) in enumerate(edl.TITLES):
        art = Image.open(png).convert("RGBA")
        art = art.crop(art.getchannel("A").getbbox())
        art = art.resize((int(w), round(art.height * w / art.width)), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (1920, 804), (0, 0, 0, 0))
        canvas.alpha_composite(art, (round(cx * 1920 - art.width / 2), round(cy * 804 - art.height / 2)))
        p = f"text/title_{i}.png"; canvas.save(p); paths.append(p)
    return paths

# ------------------------------------------------------------------ finishing + master
def main():
    os.makedirs("render", exist_ok=True)
    write_ass("text/titles.ass")
    lst = conform_list()
    off = float(PREVIEW.split(",")[0]) if PREVIEW else 0.0
    # title artwork goes on before halation + grain so it lives in the same film texture as the picture
    pngs = title_canvases()
    over, inputs, last = [], [], "[0:v]"
    for p, (_, a, b, fi, fo, *_, op) in zip(pngs, edl.TITLES):
        if b - off <= 0:                                # preview starts after this title is gone
            continue
        n = len(inputs) // 8 + 2                        # input index (0 = picture, 1 = mix)
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{edl.END:.3f}", "-i", p]
        # embed the artwork: lens-soft edges, its own moving grain, a touch of the scene showing through
        over.append(f"[{n}:v]format=gbrap,gblur=sigma=0.9,colorchannelmixer=aa={op},"
                    f"format=yuva444p10le,noise=c0s=34:c0f=t,gblur=sigma=0.65:planes=1,"
                    f"fade=t=in:st={max(a - off, 0):.3f}:d={fi}:alpha=1,"
                    f"fade=t=out:st={b - fo - off:.3f}:d={fo}:alpha=1[t{n}];"
                    f"{last}[t{n}]overlay=0:0:format=yuv420p10:eof_action=pass[o{n}];")
        last = f"[o{n}]"
    # halation: threshold + blur the highlights in 16-bit (clips at 0), pre-scale the warm glow,
    # then screen it at full opacity in float (ffmpeg's float blend opacity / 16-bit curves both misbehave)
    look = (
        "split[base][hl];"
        "[hl]format=gbrp16le,colorlevels=rimin=0.6:gimin=0.6:bimin=0.6,gblur=sigma=26,"
        "colorchannelmixer=rr=0.16:gg=0.105:bb=0.06,format=gbrpf32le[glow];"
        "[base]format=gbrpf32le[basef];[basef][glow]blend=all_mode=screen,format=gbrp16le,"
        "vignette=angle=0.28:eval=init,"
        "format=yuv420p10le,noise=c0s=5:c0f=t,"
        "pad=1920:1080:0:138:black,format=yuv420p,"
        "ass=text/titles.ass:fontsdir=fonts:shaping=complex[v]")
    cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", "render/mix.wav"]
    if PREVIEW:
        a, b = (float(v) for v in PREVIEW.split(","))
        cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-ss", str(a), "-t", str(b - a), "-f", "concat", "-safe", "0", "-i", lst,
               "-ss", str(a), "-t", str(b - a), "-i", "render/mix.wav"]
        look = look.replace("ass=text/titles.ass", f"setpts=PTS+{a}/TB,ass=text/titles.ass") + ";[v]setpts=PTS-STARTPTS[v]"
        look = look.replace("[v];[v]setpts", "[vv];[vv]setpts")
        inputs = [v if not (j and inputs[j - 1] == "-t") else f"{edl.END - a:.3f}" for j, v in enumerate(inputs)]
    cmd += inputs + ["-filter_complex", "".join(over) + last + look, "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "slow" if not PREVIEW or os.environ.get("FINALQ") else "fast", "-crf", "16", "-tune", "film",
            "-x264-params", "aq-mode=3:deblock=-1,-1", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT]
    subprocess.run(cmd, check=True)
    print("wrote", OUT)

if __name__ == "__main__":
    main()
