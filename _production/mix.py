"""Akashnir v2 - sound design + music mix, built sample-accurately from the EDL timeline."""
import subprocess, re, numpy as np, wave, os
import edl

SR = 48000
T = edl.END
N = int(T * SR) + SR
mix = np.zeros((N, 2), np.float32)

def decode(path, ss=0.0, t=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{ss:.4f}"] + (["-t", f"{t:.4f}"] if t else []) + \
          ["-i", path, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()

_lufs = {}
def lufs(path, ss=0.0, t=None):
    key = (path, ss, t)
    if key not in _lufs:
        cmd = ["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{ss}"] + (["-t", f"{t}"] if t else []) + \
              ["-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"]
        err = subprocess.run(cmd, capture_output=True, text=True).stderr
        _lufs[key] = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])
    return _lufs[key]

REF = -23.0
MAX_BOOST = 15.0                                    # never lift a quiet recording's noise floor more than this
def db(x): return 10 ** (x / 20)

def place(path, at, gain=0.0, ss=0.0, dur=None, fin=0.05, fout=0.05, loop=False, env=None, norm=True, norm_t=None):
    """Place a sound at film time `at`. gain is relative to loudness-normalised (-23 LUFS) level.
    env: list of (film_time, dB) points multiplied on top of gain."""
    if loop:
        assert dur is not None, "looped sounds need a duration"
        src = decode(path, ss)
        need = int(dur * SR) + SR
        reps = need // len(src) + 1
        x = np.tile(src, (reps, 1))[: int(dur * SR)]
    else:
        x = decode(path, ss, dur)
    g = gain
    if norm:
        g += min(REF - lufs(path, ss if not loop else 0.0, norm_t if norm_t else (dur if not loop else None)), MAX_BOOST)
    x = x * db(g)
    n = len(x)
    fi, fo = int(fin * SR), int(fout * SR)
    ramp = np.ones(n, np.float32)
    if fi: ramp[:fi] = np.linspace(0, 1, fi) ** 2
    if fo: ramp[-fo:] = np.minimum(ramp[-fo:], np.linspace(1, 0, fo) ** 2)
    if env:
        tt = at + np.arange(n) / SR
        et, ed = zip(*env)
        ramp = ramp * db(np.interp(tt, et, ed)).astype(np.float32)
    x = x * ramp[:, None]
    i0 = int(round(at * SR))
    i1 = min(i0 + n, N)
    mix[i0:i1] += x[: i1 - i0]

S = "sfx/"; MU = "music/"; V = edl.SRC + "/"
SM = edl.SMASH
sh = {s["id"]: s for s in edl.SHOTS}
def t0(i): return sh[i]["t0"]
def t1(i): return sh[i]["t1"]
def dur(i): return t1(i) - t0(i)

# ------------------------------------------------------------------ ACT I : the city
place(S + "city_traffic.mp3", 0.0, 2.5, dur=SM, loop=True, fin=1.2, fout=0.0, env=[
    (0.0, -6), (1.2, -1), (6.2, -1), (6.7, -15), (11.4, -15), (11.65, 0), (14.2, 0), (14.6, -15), (19.2, -15),
    (19.7, -24), (29.3, -24), (29.8, -9), (33.4, -9), (33.8, -17), (37.2, -17), (37.6, -16), (46.5, -16),
    (46.9, -1), (SM - 0.05, 2)])
for a, b in [(1.21, 6.42), (11.58, 14.42)]:
    place(S + "market_crowd.mp3", a, -4, ss=a - 1.0, dur=b - a, fin=0.25, fout=0.12)
place(S + "market_crowd.mp3", 46.79, -3, ss=4.0, dur=SM - 46.79, fin=0.15, fout=0.0)
place(S + "aerial_wind.mp3", 6.2, -2, dur=5.6, loop=True, fin=0.4, fout=0.4)
place(S + "aerial_wind.mp3", 14.2, -2, dur=5.4, loop=True, fin=0.4, fout=0.4)
# the tired river: drone wind over the Buriganga, then the water at the garbage bank
place(S + "aerial_wind.mp3", t0("A05") - 0.1, -4, dur=dur("A05") + 0.4, loop=True, fin=0.4, fout=0.5)
place(S + "river_polluted.mp3", t0("A05") - 0.1, 0, dur=t1("A06") - t0("A05") + 0.3, loop=True, fin=0.4, fout=0.4,
      env=[(t0("A05"), -9), (t0("A06") - 0.3, -9), (t0("A06") + 0.1, -1), (t1("A06"), -1)])
place(S + "crows.mp3", t0("A06") + 0.5, -11, ss=0.4, dur=1.9, fin=0.02, fout=0.3)
place(S + "crows.mp3", t0("A06") + 2.6, -16, ss=3.8, dur=1.5, fin=0.02, fout=0.4)
place(S + "pigeons.mp3", 29.58, -3, ss=1.0, dur=4.05, fin=0.2, fout=0.3)
place(S + "leaves_wind.mp3", 33.5, -10, dur=4.0, loop=True, fin=0.3, fout=0.3)
place(S + "wing_flutter.mp3", 39.1, -1, fin=0.01, fout=0.3)
place(S + "wing_flutter.mp3", 42.25, -4, fin=0.01, fout=0.3)
# low strings creep in under the pollution, swelling into the smash cut
place(MU + "Anabasis_I.mp3", 19.4, 0, ss=0.0, dur=SM - 19.4, fin=0.0, fout=0.0, norm_t=60,
      env=[(19.4, -40), (24.0, -10), (36.0, -7), (46.8, -3), (SM - 0.05, 0)])
# riser: its built-in hard stop (measured) lands exactly on the smash cut
r = decode(S + "riser.mp3"); env = np.sqrt(np.convolve((r ** 2).mean(1), np.ones(480) / 480, "same"))
stop = np.where(env > env.max() * 0.25)[0][-1] / SR
place(S + "riser.mp3", SM - stop, -3, dur=stop, fin=0.5, fout=0.0)

# ------------------------------------------------------------------ silence, then a single bird
place(S + "rooftop_birds.mp3", SM + 1.05, -3, ss=3.25, dur=1.6, fin=0.03, fout=0.6)
P1 = edl.M1
p1_end = t1("Q02") + 0.6                            # score breathes out under her hands in the flowers
place(MU + "AKindOfHope.mp3", 4.0 + P1, -5.5, ss=4.0, dur=p1_end - (4.0 + P1), fin=0.0, fout=4.6, norm_t=100)

# ------------------------------------------------------------------ ACT II : the garden
place(S + "rooftop_birds.mp3", SM + 2.6, -14, dur=t0("D02") - SM - 2.1, loop=True, fin=2.5, fout=1.0)
place(S + "doves.mp3", t0("T01") + 2.5, -14, ss=1.0, dur=6.5, fin=1.5, fout=1.5)
place(S + "city_traffic.mp3", t0("B01"), -27, dur=dur("B01") + 0.3, loop=True, fin=1.0, fout=1.2)
place(S + "city_traffic.mp3", t0("B06") - 0.3, -25, dur=dur("B06") + 0.6, loop=True, fin=0.8, fout=0.8)  # concrete walls
place(S + "leaves_wind.mp3", t0("B03") - 0.5, -11, dur=t1("F02") - t0("B03") + 1.0, loop=True, fin=1.0, fout=1.0)

# ------------------------------------------------------------------ ACT III : care, life returning
c1 = t0("C01")
place(S + "seeds.mp3", c1 + 1.0, -5, dur=2.6, fin=0.02, fout=0.6)
place(S + "seeds.mp3", c1 + 5.2, -7, ss=0.6, dur=2.4, fin=0.02, fout=0.6)
c6 = sh["C06"]                                      # the wild sparrows' own chirps, recorded on the roof
place(V + "38-1.mp4", t0("C06") - 0.2, -4, ss=c6["src_in"] - 0.2, dur=dur("C06") + 0.5, fin=0.3, fout=0.4)
place(S + "wing_flutter.mp3", t0("C06") + 3.3, -9, fin=0.01, fout=0.3)
place(S + "budgies.mp3", t0("C02"), -9, dur=dur("C02"), fin=0.3, fout=0.4)
place(S + "doves.mp3", t0("C03"), -6, dur=dur("C03"), fin=0.4, fout=0.4)
place(S + "fountain.mp3", t0("C04") - 0.3, -4, ss=1.2, dur=dur("C04") + 0.6, loop=True, fin=0.4, fout=0.6)  # skip the opening splash
place(S + "leaves_wind.mp3", t0("C05"), -10, dur=dur("C05"), loop=True, fin=0.8, fout=0.8)
place(S + "wing_flutter.mp3", t0("C05") + 3.2, -12, fin=0.01, fout=0.3)
place(S + "monkey_rustle.mp3", t0("L01") + 0.2, -6, dur=dur("L01") - 0.2, fin=0.2, fout=0.4)
place(S + "mongoose_scurry.mp3", t0("L02") + 0.5, -10, dur=3.5, fin=0.1, fout=0.5)
place(S + "cat_purr.mp3", t0("L03"), -11, dur=dur("L03") + 0.2, fin=0.2, fout=0.3)
place(S + "rabbit_munch.mp3", t0("L04"), -6, dur=dur("L04"), fin=0.15, fout=0.4)
place(S + "wing_flutter.mp3", t0("L05") + 0.3, -5, fin=0.01, fout=0.4)
place(S + "doves.mp3", t0("L05") + 1.5, -9, ss=2.0, dur=7.0, fin=0.8, fout=0.8)

# ------------------------------------------------------------------ ACT IV : her garden, the held breath, the reveal
place(S + "leaves_wind.mp3", t0("Q01"), -13, dur=dur("Q01") + dur("Q02"), loop=True, fin=0.8, fout=1.0)
place(S + "rooftop_birds.mp3", t0("Q03"), -9, ss=6.0, dur=t0("D02") - t0("Q03") + 1.0, fin=0.6, fout=1.0)
place(S + "budgies.mp3", t0("Q03") + 1.0, -17, ss=1.0, dur=5.0, fin=0.6, fout=0.8)
# real ceremony audio under the climax
place(V + "34.mp4", t0("D02"), -3, ss=10.0, dur=dur("D02"), fin=0.4, fout=0.25)
place(V + "34.mp4", t0("D03"), -4, ss=21.4, dur=dur("D03"), fin=0.25, fout=0.6)
place(S + "curtain.mp3", edl.REVEAL - 0.75, -6, fin=0.02, fout=0.3)
d4 = sh["D04"]
place(V + "54-1.mp4", t0("D04"), -5, ss=d4["src_in"], dur=(dur("D04")) / d4["slow"], fin=0.3, fout=0.6)
place(S + "flock_release.mp3", edl.RELEASE - 0.12, -1, fin=0.01, fout=0.6)
place(S + "crowd_applause.mp3", edl.RELEASE + 0.5, -9, dur=t1("D04") - edl.RELEASE + 0.4, fin=0.4, fout=0.9)
place(MU + "AKindOfHope.mp3", 284.6 + edl.M2, 1.0, ss=284.6, dur=edl.P2_END - 284.6, fin=4.3, fout=1.5, norm_t=None)
place(S + "rooftop_birds.mp3", t0("D05"), -16, ss=10.0, dur=dur("D05") + 0.5, fin=0.8, fout=0.8)
place(S + "aerial_wind.mp3", t0("D06"), -15, dur=dur("D06"), loop=True, fin=1.0, fout=1.5)
place(S + "city_traffic.mp3", t0("D06"), -28, dur=dur("D06"), loop=True, fin=1.5, fout=1.5)
# after the last note: the rooftop's birds, under the ivory logo
place(S + "rooftop_birds.mp3", edl.LOGO_IN + 2.2, -17, ss=2.0, dur=T - edl.LOGO_IN - 2.2, fin=2.2, fout=1.8)

# ------------------------------------------------------------------ master
mix = mix[: int(T * SR)]
peak = np.abs(mix).max()
if peak > 0.98: mix *= 0.98 / peak
os.makedirs("render", exist_ok=True)
raw = "render/mix_raw.wav"
with wave.open(raw, "wb") as w:
    w.setnchannels(2); w.setsampwidth(3); w.setframerate(SR)
    i = np.clip(mix, -1, 1) * (2 ** 23 - 1)
    i = i.astype(np.int32).reshape(-1)
    b = np.zeros((len(i), 3), np.uint8)
    b[:, 0] = i & 0xFF; b[:, 1] = (i >> 8) & 0xFF; b[:, 2] = (i >> 16) & 0xFF
    w.writeframes(b.tobytes())
print("raw mix", raw, f"{T:.2f}s, pre-peak {peak:.3f}")

# two-pass loudness normalisation: -15 LUFS integrated, -1.5 dBTP, keep dynamics (linear)
m = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", raw, "-af",
                    "loudnorm=I=-15:TP=-1.5:LRA=20:print_format=summary", "-f", "null", "-"], capture_output=True, text=True).stderr
def g(k):
    hit = re.search(k + r":\s+(-?[\d.]+|-inf)", m)
    assert hit, f"loudnorm did not report {k}"
    return hit.group(1)
mi, mtp, mlra, mth = g("Input Integrated"), g("Input True Peak"), g("Input LRA"), g("Input Threshold")
print("measured", mi, "LUFS  TP", mtp, " LRA", mlra)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                f"loudnorm=I=-15:TP=-1.5:LRA=20:measured_I={mi}:measured_TP={mtp}:measured_LRA={mlra}:measured_thresh={mth}:linear=true,"
                f"alimiter=limit=0.84:attack=3:release=60:level=disabled", "-ar", str(SR), "-c:a", "pcm_s24le", "render/mix.wav"], check=True)
m2 = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", "render/mix.wav", "-af", "ebur128=peak=true", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
print("final:", " ".join(re.findall(r"(I:\s+-?[\d.]+ LUFS|LRA:\s+[\d.]+ LU|Peak:\s+-?[\d.]+ dBFS)", m2)[-3:]))
