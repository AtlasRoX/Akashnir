"""Akashnir - titles (ASS, Google Sans, Bangla complex shaping) + conform + finishing pass + master encode."""
import subprocess, os, sys
import edl

FPS = edl.FPS
OUT = sys.argv[1] if len(sys.argv) > 1 else r"X:/lis cd/New folder/Akashnir_ChadBagan_Documentary_1080p.mp4"
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
Style: Place,Google Sans Medium,112,{WHITE},{WHITE},&H70000000,&H00000000,0,0,0,0,100,100,0,0,1,4,0,5,0,0,0,1
Style: Title,Google Sans Medium,150,{WHITE},{WHITE},&HFF000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Sub,Google Sans,44,&H30E4EDF3,{WHITE},&HFF000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Line,Google Sans,56,{WHITE},{WHITE},&H58000000,&H00000000,0,0,0,0,100,100,0,0,1,3.5,0,2,0,0,214,1
Style: Lower,Google Sans,42,{WHITE},{WHITE},&H58000000,&H00000000,0,0,0,0,100,100,0,0,1,3.5,0,1,170,0,214,1
Style: Credit,Google Sans,34,&H20E4EDF3,{WHITE},&HFF000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Small,Google Sans,30,&H40E4EDF3,{WHITE},&HFF000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
FADES = {"Place": (900, 900), "Title": (1600, 1200), "Sub": (1400, 1100), "Line": (700, 700),
         "Lower": (600, 600), "Credit": (1000, 900), "Small": (1000, 1000)}
POS = {"Sub": r"\pos(960,640)", "Title": r"\pos(960,522)", "Place": r"\pos(960,300)"}

def write_ass(path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(ASS_HEAD)
        for a, b, style, text in edl.TEXT:
            fi, fo = FADES[style]
            tags = rf"\fad({fi},{fo})" + POS.get(style, "")
            if style in ("Line", "Lower", "Place"):
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

# ------------------------------------------------------------------ finishing + master
def main():
    os.makedirs("render", exist_ok=True)
    write_ass("text/titles.ass")
    lst = conform_list()
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
    cmd += ["-filter_complex", "[0:v]" + look, "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "slow" if not PREVIEW else "fast", "-crf", "16", "-tune", "film",
            "-x264-params", "aq-mode=3:deblock=-1,-1", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT]
    subprocess.run(cmd, check=True)
    print("wrote", OUT)

if __name__ == "__main__":
    main()
