"""QC: contact sheet of the master at key story moments + stream/loudness checks."""
import subprocess, sys, re
from PIL import Image, ImageDraw, ImageFont
import edl

MASTER = sys.argv[1] if len(sys.argv) > 1 else r"X:/lis cd/New folder/Akashnir_ChadBagan_Documentary_1080p.mp4"
OUTIMG = sys.argv[2] if len(sys.argv) > 2 else "stills/qc_sheet.jpg"
font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 20)

marks = [(3.5, "A01 market")] + [((a + b) / 2, f"text: {st}") for a, b, st, _ in edl.TEXT] + [
    (edl.SMASH - 0.2, "montage end"), (edl.SMASH + 0.5, "smash black"), (edl.SHOTS[18]["t0"] + 0.3, "B01 fade-in"),
    (edl.REVEAL + 0.2, "curtain reveal")]
marks.sort()
tiles = []
for t, label in marks:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", MASTER, "-frames:v", "1", "-vf", "scale=640:360",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    if len(raw) < 640 * 360 * 3: continue
    im = Image.frombytes("RGB", (640, 360), raw[:640 * 360 * 3]); d = ImageDraw.Draw(im)
    d.text((6, 4), f"{t:6.2f}s  {label}", font=font, fill="yellow"); tiles.append(im)
cols = 4; rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 644, rows * 364), "gray")
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 644, (i // cols) * 364))
sheet.save(OUTIMG, quality=82)

info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,duration,nb_frames",
                       "-of", "compact", MASTER], capture_output=True, text=True).stdout
print(info.strip())
err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", MASTER, "-map", "0:a", "-af", "ebur128=peak=true", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
print("audio:", " ".join(re.findall(r"(I:\s+-?[\d.]+ LUFS|LRA:\s+[\d.]+ LU|Peak:\s+-?[\d.]+ dBFS)", err)[-3:]))
print("expected duration", round(edl.END, 3), "s")
