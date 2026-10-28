"""Akashnir v2 - edit decision list. All film times in seconds at 24 fps; cuts snap to whole frames.

Music anchors (A Kind of Hope, Scott Buckley; bar = 4.3633 s):
  part 1 : first audible note (src 4.82) lands at film 52.40  -> film = src + M1
  part 2 : downbeat src 288.97 lands on the curtain reveal (34.mp4 src 13.9)
"""
FPS = 24
SRC = r"X:/lis cd/New folder"

def fr(t):
    return round(t * FPS) / FPS

# source clip facts: native fps (for conform slow-motion) and width
CLIPS = {
    "1": (59.94, 3840), "3": (59.94, 3840), "4": (25, 1920), "5": (29.97, 3840), "6": (50, 1920),
    "8": (30, 1920), "10": (30, 1920), "11": (29.97, 2048), "12": (29.97, 1920), "14": (60, 1920),
    "16": (60, 3840), "19": (30, 1920), "24": (30, 3840), "29": (60, 1920), "31": (30, 1920),
    "34": (30, 1920), "39": (50, 1920), "41": (30, 1920), "42": (30, 3840), "43": (60, 1920),
    "2-1": (29.97, 1920), "13-1": (30, 1920), "20-1": (30, 1920), "23-1": (30, 1920), "32-1": (30, 1920),
    "33-1": (30, 1920), "35-1": (50, 1920), "36-1": (50, 1920), "37-1": (50, 1920), "54-1": (30, 1920),
    "50": (30, 3840), "38-1": (30, 1920),
}
MTS = {"39", "35-1", "36-1", "37-1"}
FILE = {k: f"{k}.MTS" if k in MTS else f"{k}.mp4" for k in CLIPS}

def conform(clip):
    """slow factor that plays every source frame at 24 fps (true slow motion)."""
    return CLIPS[clip][0] / 24.0

M1 = 52.40 - 4.82                                  # part-1 music offset
P1_BARS = [6.41, 10.73, 15.13, 19.49, 23.85, 28.24, 32.61, 36.93, 41.31, 45.66, 50.13, 54.42, 58.85,
           63.16, 67.50, 71.84, 76.17, 80.56, 84.95, 89.35, 93.65, 98.03, 102.39, 106.77, 111.07, 115.40,
           119.80, 124.24, 128.51]
def k1(i):                                          # film time of part-1 bar i
    return fr(P1_BARS[i] + M1)

D2_SRC_IN, REVEAL_SRC = 10.0, 13.9
P2_HIT = 288.97
P2_END = 338.0
BAR = 4.3633
RELEASE_SRC = 36.35                                 # 54-1.mp4: hands open, doves take off

# ---------------------------------------------------------------- shots
# each: (id, clip, src_in, slow, film_start, film_end, opts)
#   slow  : output seconds per source second ("c" = conform every frame to 24 fps, 1.0 = real time)
#   opts  : cy (vertical framing centre 0..1), zoom (punch-in), cx, push, look (grade key), fin/fout (fade from/to black)
SHOTS = []
def shot(id, clip, src_in, slow, t0, t1, **o):
    SHOTS.append(dict(id=id, clip=clip, src_in=src_in, slow=conform(clip) if slow == "c" else slow,
                      t0=fr(t0), t1=fr(t1), **o))

# ACT I - the city (sound-design driven, ends in a smash cut)
shot("A01", "5", 0.5, 1.0, 1.2, 6.4, cy=0.5, push=1.06)
shot("A02", "1", 0.0, "c", 6.4, 11.6, cy=0.45)
shot("A03", "5", 7.0, 1.0, 11.6, 14.4, zoom=2.0, cx=0.5, cy=0.55)
shot("A04", "1", 5.4, "c", 14.4, 19.4, cy=0.45)
shot("A05", "2-1", 13.6, 1.25, 19.4, 25.4, cy=0.5)
shot("A06", "3", 2.0, "c", 25.4, 29.6, cy=0.56)
shot("A07", "4", 0.0, "c", 29.6, 33.6, cy=0.42)
shot("A08", "39", 14.0, "c", 33.6, 37.4, cy=0.5)
shot("A09", "6", 46.6, "c", 37.4, 41.6, cy=0.45)
shot("A10", "6", 53.9, "c", 41.6, 46.8, cy=0.45)
# accelerating montage under the riser (durations shrink -> tension)
t = 46.8
for i, (clip, s_in, slow, dur, kw) in enumerate([
        ("5", 11.0, 1.0, 0.70, dict(zoom=2.2, cx=0.25, cy=0.75)),
        ("1", 8.0, "c", 0.60, dict(cy=0.45)),
        ("2-1", 1.0, 1.0, 0.55, dict(cy=0.6)),
        ("5", 3.0, 1.0, 0.48, dict(cy=0.5)),
        ("4", 6.0, "c", 0.42, dict(cy=0.42)),
        ("39", 20.0, "c", 0.36, dict(cy=0.5)),
        ("5", 12.0, 1.0, 0.32, dict(zoom=2.4, cx=0.7, cy=0.35)),
        ("1", 1.0, "c", 0.37, dict(cy=0.45))]):
    shot(f"AM{i+1}", clip, s_in, slow, t, t + dur, **kw); t += dur
SMASH = fr(t)                                       # hard cut to black + silence

# ACT II - Akashnir (cut on the piano's downbeats; each bar-shot takes the next n bars)
TITLE_IN = k1(0)
_bar = [2]
def bars(id, clip, src_in, slow, n=1, **o):
    a = _bar[0]; _bar[0] += n
    shot(id, clip, src_in, slow, k1(a), k1(a + n), **o)
shot("T01", "11", 2.0, 1.25, 52.40, k1(2), cy=0.5, fin=1.6)          # the title, over doves in open sky
bars("B01", "16", 1.0, "c", cy=0.5)
bars("B02", "8", 0.0, 1.25, 2, cy=0.42)
bars("B06", "50", 2.0, 1.25, cy=0.55)                                 # saplings against old concrete
bars("B03", "12", 0.5, 1.25, cy=0.5)
bars("B04", "20-1", 2.4, 1.25, cy=0.45)
bars("F01", "41", 2.0, 1.25, cy=0.55)                                 # ৪১৮টি গাছ
bars("F02", "10", 0.6, 1.25, cy=0.5)                                  # ৫৮ প্রজাতি
bars("F03", "19", 0.8, 1.25, cy=0.56)                                 # প্রায় ১১,০০০ বর্গফুট
bars("B05", "29", 0.6, "c", cy=0.5)
# ACT III - care, and life returning
bars("C01", "24", 2.0, 1.25, 2, cy=0.55)                              # খাবারের ব্যবস্থা
bars("C06", "38-1", 8.0, 1.25, zoom=1.45, cx=0.66, cy=0.39)           # ...and the wild sparrows come to eat
bars("C02", "42", 1.0, 1.25, cy=0.45)
bars("C03", "43", 0.5, "c", cy=0.5)
bars("C04", "23-1", 1.2, 1.25, cy=0.42)                               # পানির ব্যবস্থা
bars("C05", "14", 0.4, "c", 2, cy=0.55)                               # সবুজ আশ্রয়
bars("L01", "35-1", 7.3, "c", cy=0.5)                                 # monkey among the canna flowers
bars("L02", "36-1", 11.1, "c", cy=0.55, zoom=1.2, cx=0.45)            # mongoose crossing
HALF = fr(k1(_bar[0]) + BAR / 2)
shot("L03", "37-1", 1.0, "c", k1(_bar[0]), HALF, cy=0.5)             # cats resting
shot("L04", "13-1", 0.6, 1.25, HALF, k1(_bar[0] + 1), cy=0.5)        # rabbits
_bar[0] += 1
bars("L05", "11", 50.4, 1.25, 2, cy=0.58)                             # wild doves land
# ACT IV - her garden, the inauguration, freedom
bars("Q01", "33-1", 0.5, 1.25, cy=0.5)
bars("Q02", "32-1", 1.2, 1.25, cy=0.45)
shot("Q03", "31", 3.0, 1.25, k1(_bar[0]), k1(_bar[0]) + 6.6, cy=0.5) # the held breath: birdsong only
D2_START = SHOTS[-1]["t1"]
REVEAL = fr(D2_START + (REVEAL_SRC - D2_SRC_IN))
M2 = REVEAL - P2_HIT                                # part-2 music offset
def b2(src):
    return fr(src + M2)
shot("D02", "34", D2_SRC_IN, 1.0, D2_START, b2(P2_HIT + BAR), cy=0.45)
shot("D03", "34", 21.4, 1.0, b2(P2_HIT + BAR), b2(P2_HIT + 2 * BAR), cy=0.45)
RELEASE = b2(P2_HIT + 3 * BAR)                      # doves leave the hands on a downbeat
shot("D04", "54-1", RELEASE_SRC - BAR / 1.25, 1.25, b2(P2_HIT + 2 * BAR), RELEASE + 2.9, cy=0.42)
shot("D05", "8", 6.6, 1.25, RELEASE + 2.9, b2(P2_HIT + 5 * BAR), cy=0.5)
END_DRONE = b2(P2_HIT + 5 * BAR)
shot("D06", "1", 3.9, "c", END_DRONE, b2(P2_HIT + 7 * BAR), cy=0.45, look="1@hope", fout=1.2)
CREDITS_IN = b2(P2_HIT + 7 * BAR)
LOGO_IN = b2(P2_HIT + 10 * BAR)                     # ivory logo card on the score's last ringing note
END = fr(P2_END + M2 + 2.8)                         # a breath of birdsong after the music

# ---------------------------------------------------------------- title artwork (PNG) placements
TITLE_PNG = SRC + "/আকাশনীড় Bengali Title+.png"           # maroon: opening title, over the doves' sky
LOGO_PNG = SRC + "/Warm ivory Bengali title lettering.png"  # ivory: final end card, on black
# (png, start, end, fade_in, fade_out, width_px, centre_x, centre_y, opacity) in the 1920x804 picture
TITLES = [
    (TITLE_PNG, TITLE_IN, k1(2) - 0.5, 1.8, 1.3, 820, 0.30, 0.30, 0.93),   # sky texture breathes through
    (LOGO_PNG, LOGO_IN + 0.2, END - 0.15, 2.0, 2.2, 940, 0.50, 0.50, 1.0),
]

# ---------------------------------------------------------------- on-screen text (Bangla, Google Sans)
# (start, end, style, text)
def S(id):
    s = next(x for x in SHOTS if x["id"] == id); return s["t0"], s["t1"]
TEXT = [
    (7.0, 11.3, "Place", "ঢাকা"),
    (14.8, 19.2, "Line", "দুই কোটিরও বেশি মানুষের শহর"),
    (20.0, 25.1, "Line", "নদী ক্লান্ত, বাতাস ভারী"),
    (43.0, 46.7, "Line", "এই শহরে পাখিরা বসবে কোথায়?"),
    (S("F01")[0] + 0.35, S("F01")[1] - 0.3, "Fact", "৪১৮টি গাছ"),
    (S("F02")[0] + 0.35, S("F02")[1] - 0.3, "Fact", "৫৮ প্রজাতি"),
    (S("F03")[0] + 0.35, S("F03")[1] + 1.2, "Fact", "প্রায় ১১,০০০ বর্গফুট"),
    (S("C01")[0] + 1.0, S("C01")[1] - 1.0, "Fact", "খাবারের ব্যবস্থা"),
    (S("C04")[0] + 0.35, S("C04")[1] - 0.3, "Fact", "পানির ব্যবস্থা"),
    (S("C05")[0] + 1.0, S("C05")[1] - 1.0, "Fact", "সবুজ আশ্রয়"),
    (S("L05")[0] + 2.4, S("L05")[1] - 0.5, "Line", "প্রকৃতিকে জায়গা দিলে, প্রকৃতি ফিরে আসে"),
    (END_DRONE + 1.2, CREDITS_IN - 1.2, "Line", "এই শহরের প্রতিটি ছাদ হতে পারে একটি আকাশনীড়"),
    # credits on black, then the ivory logo card (TITLES)
    (CREDITS_IN + 0.6, CREDITS_IN + 6.6, "Credit",
     r"{\fs54}পরিকল্পনা ও বাস্তবায়নে\N{\fnGoogle Sans Medium\fs120}ফরিদা খানম\N{\fnGoogle Sans\fs56}জেলা প্রশাসক ও জেলা ম্যাজিস্ট্রেট, ঢাকা"),
    (CREDITS_IN + 7.2, LOGO_IN - 0.6, "Small",
     r"{\fnGoogle Sans Medium\fs66}জেলা প্রশাসকের কার্যালয়, ঢাকা{\fnGoogle Sans\fs48}\Nছাদবাগান বাস্তবায়নে: গ্রীন সেভার্স"
     r"\N\N{\fs36}সংগীত: “A Kind of Hope”, “Anabasis I” — Scott Buckley (CC BY 4.0)   ·   শব্দ: ElevenLabs"),
]

if __name__ == "__main__":
    for s in SHOTS:
        print(f'{s["id"]:4} clip {s["clip"]:>4}  src {s["src_in"]:6.2f}+{(s["t1"]-s["t0"])/s["slow"]:5.2f}  '
              f'film {s["t0"]:7.3f} -> {s["t1"]:7.3f}  ({s["t1"]-s["t0"]:.2f}s, slow {s["slow"]:.3f})')
    print("SMASH", SMASH, "TITLE_IN", TITLE_IN, "REVEAL", REVEAL, "RELEASE", RELEASE, "M2", round(M2, 3),
          "CREDITS", CREDITS_IN, "END", END)
