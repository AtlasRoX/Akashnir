"""Render every EDL shot to a graded 1920x804 / 24 fps / 10-bit intermediate."""
import subprocess, sys, os, json
from concurrent.futures import ThreadPoolExecutor
import edl

OUT = "shots"; os.makedirs(OUT, exist_ok=True)
SIZE = {}
def size(clip):
    if clip not in SIZE:
        o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", f"{edl.SRC}/{edl.FILE[clip]}"], capture_output=True, text=True).stdout
        SIZE[clip] = tuple(int(v) for v in o.strip().splitlines()[0].split(",")[:2])
    return SIZE[clip]

def even(v): return int(round(v / 2) * 2)

def cmd(s):
    W, H = size(s["clip"])
    dur = s["t1"] - s["t0"]; n = round(dur * edl.FPS)
    need = dur / s["slow"] + 0.25
    zoom = s.get("zoom", 1.0); cx = s.get("cx", 0.5); cy = s.get("cy", 0.5)
    cw = W / zoom; ch = cw * 804 / 1920
    if ch > H:                       # source not wide enough (should not happen for 16:9)
        ch = H; cw = ch * 1920 / 804
    x = min(max(cx * W - cw / 2, 0), W - cw); y = min(max(cy * H - ch / 2, 0), H - ch)
    f = [f"setpts=(PTS-STARTPTS)*{s['slow']:.6f}", "fps=24",
         f"crop={even(cw)}:{even(ch)}:{even(x)}:{even(y)}"]
    if s.get("push"):
        z = s["push"]
        f.append(f"zoompan=z='1+{z-1:.4f}*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1920x804:fps=24")
        f.append("scale=1920:804:flags=lanczos+accurate_rnd+full_chroma_int:in_color_matrix=bt709")
    else:
        f.append("scale=1920:804:flags=lanczos+accurate_rnd+full_chroma_int:in_color_matrix=bt709")
    look = s.get("look", s["clip"])
    f += ["format=rgb48le", f"lut3d=file=luts/clips/{look.replace('@', '@')}.cube:interp=tetrahedral",
          "scale=out_color_matrix=bt709:out_range=tv", "format=yuv420p10le"]
    if s.get("fin"):  f.append(f"fade=t=in:st=0:d={s['fin']}")
    if s.get("fout"): f.append(f"fade=t=out:st={dur - s['fout']:.3f}:d={s['fout']}")
    return ["ffmpeg", "-v", "error", "-y", "-ss", f"{s['src_in']:.3f}", "-t", f"{need:.3f}",
            "-i", f"{edl.SRC}/{edl.FILE[s['clip']]}", "-an", "-vf", ",".join(f), "-frames:v", str(n),
            "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p10le",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
            "-threads", "4", f"{OUT}/{s['id']}.mkv"]

def run(s):
    c = cmd(s); sig = " ".join(c)
    sp = f"{OUT}/{s['id']}.sig"
    if os.path.exists(f"{OUT}/{s['id']}.mkv") and os.path.exists(sp) and open(sp, encoding="utf-8").read() == sig:
        print("same", s["id"], flush=True); return True
    r = subprocess.run(c, capture_output=True, text=True)
    ok = r.returncode == 0
    if ok: open(sp, "w", encoding="utf-8").write(sig)
    print(("ok  " if ok else "FAIL"), s["id"], "" if ok else r.stderr[-600:], flush=True)
    return ok

if __name__ == "__main__":
    ids = sys.argv[1:]
    todo = [s for s in edl.SHOTS if (s["id"] in ids if ids else True)]
    with ThreadPoolExecutor(3) as ex:
        res = list(ex.map(run, todo))
    print("done", sum(res), "/", len(res))
