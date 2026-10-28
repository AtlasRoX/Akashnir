"""Akashnir - edit decision list. All film times in seconds at 24 fps; cuts snap to whole frames.

Music anchors (A Kind of Hope, Scott Buckley):
  part 1 : first audible note (src 4.82) lands at film 52.40  -> film = src + M1
  part 2 : climax downbeat (src 288.97) lands on the curtain reveal (34.mp4 src 13.9)
"""
FPS = 24
SRC = r"X:/lis cd/New folder"

def fr(t):
    return round(t * FPS) / FPS

# source clip facts: native fps (for conform slow-motion) and size
CLIPS = {
    "1": (59.94, 3840), "3": (59.94, 3840), "4": (25, 1920), "5": (29.97, 3840), "6": (50, 1920),
    "8": (30, 1920), "10": (30, 1920), "11": (29.97, 2048), "12": (29.97, 1920), "14": (60, 1920),
    "15": (30, 1920), "16": (60, 3840), "19": (30, 1920), "22": (30, 1920), "24": (30, 3840),
    "29": (60, 1920), "31": (30, 1920), "34": (30, 1920), "39": (50, 1920), "41": (30, 1920),
    "42": (30, 3840), "43": (60, 1920), "44": (30, 3840), "49": (30, 1920), "50": (30, 3840),
    "51": (30, 3840), "53": (30, 3840),
}
FILE = {k: f"{k}.MTS" if k == "39" else f"{k}.mp4" for k in CLIPS}

def conform(clip):
    """slow factor that plays every source frame at 24 fps (true slow motion)."""
    return CLIPS[clip][0] / 24.0

M1 = 52.40 - 4.82                                  # part-1 music offset
P1_BARS = [6.41, 10.73, 15.13, 19.49, 23.85, 28.24, 32.61, 36.93, 41.31, 45.66, 50.13, 54.42, 58.85,
           63.16, 67.50, 71.84, 76.17, 80.56, 84.95, 89.35, 93.65, 98.02, 102.39, 106.77]
def b1(src):                                        # film time of a part-1 downbeat
    return fr(src + M1)

D2_START, D2_SRC_IN, REVEAL_SRC = None, 10.0, 13.9
P2_HIT = 288.97
P2_BARS = [288.97, 293.34, 297.70, 302.07, 306.43, 310.80, 315.16, 319.53, 323.89, 328.26, 332.62]
P2_END = 338.0

# ---------------------------------------------------------------- shots
# each: (id, clip, src_in, slow, film_start, film_end, opts)
#   slow  : output seconds per source second ("c" = conform every frame to 24 fps, 1.0 = real time)
#   opts  : cy (vertical framing centre 0..1), zoom (punch-in), cx, look (grade key), fin/fout (fade from/to black)
SHOTS = []
def shot(id, clip, src_in, slow, t0, t1, **o):
    SHOTS.append(dict(id=id, clip=clip, src_in=src_in, slow=conform(clip) if slow == "c" else slow,
                      t0=fr(t0), t1=fr(t1), **o))

# ACT I - the city (sound-design driven, ends in a smash cut)
shot("A01", "5", 0.5, 1.0, 1.2, 6.4, cy=0.5, push=1.06)
shot("A02", "1", 0.0, "c", 6.4, 11.6, cy=0.45)
shot("A03", "5", 7.0, 1.0, 11.6, 14.4, zoom=2.0, cx=0.5, cy=0.55)
shot("A04", "1", 5.4, "c", 14.4, 19.4, cy=0.45)
shot("A05", "3", 2.0, "c", 19.4, 25.4, cy=0.56)
shot("A06", "53", 1.0, 1.25, 25.4, 29.6, cy=0.5)
shot("A07", "4", 0.0, "c", 29.6, 33.6, cy=0.42)
shot("A08", "39", 14.0, "c", 33.6, 37.4, cy=0.5)
shot("A09", "6", 46.6, "c", 37.4, 41.6, cy=0.45)
shot("A10", "6", 53.9, "c", 41.6, 46.8, cy=0.45)
# accelerating montage under the riser (durations shrink -> tension)
t = 46.8
for i, (clip, s_in, slow, dur, kw) in enumerate([
        ("5", 11.0, 1.0, 0.70, dict(zoom=2.2, cx=0.25, cy=0.75)),
        ("1", 8.0, "c", 0.60, dict(cy=0.45)),
        ("3", 10.0, "c", 0.55, dict(cy=0.6)),
        ("5", 3.0, 1.0, 0.48, dict(cy=0.5)),
        ("4", 6.0, "c", 0.42, dict(cy=0.42)),
        ("39", 20.0, "c", 0.36, dict(cy=0.5)),
        ("5", 12.0, 1.0, 0.32, dict(zoom=2.4, cx=0.7, cy=0.35)),
        ("1", 1.0, "c", 0.37, dict(cy=0.45))]):
    shot(f"AM{i+1}", clip, s_in, slow, t, t + dur, **kw); t += dur
SMASH = fr(t)                                       # hard cut to black + silence

# ACT II - Akashnir (cut on the piano's downbeats)
TITLE_IN = b1(6.41)
shot("B01", "16", 1.0, "c", b1(10.73), b1(15.13), cy=0.5, fin=1.0)
shot("B02", "8", 0.0, 1.25, b1(15.13), b1(23.85), cy=0.42)
shot("B03", "12", 0.5, 1.25, b1(23.85), b1(28.24), cy=0.5)
shot("B04", "10", 0.6, 1.25, b1(28.24), b1(32.61), cy=0.5)
shot("B05", "19", 0.8, 1.25, b1(32.61), b1(36.93), cy=0.56)
shot("B06", "29", 0.6, "c", b1(36.93), b1(41.31), cy=0.5)
shot("B07", "41", 2.0, 1.25, b1(41.31), b1(45.66), cy=0.55)
shot("B08", "50", 2.0, 1.25, b1(45.66), b1(50.13), cy=0.55)
shot("B09", "49", 3.0, 1.25, b1(50.13), b1(54.42), cy=0.5)
shot("B10", "14", 0.4, "c", b1(54.42), b1(63.16), cy=0.55)
shot("B11", "51", 3.0, 1.25, b1(63.16), b1(67.50), cy=0.5)
# ACT III - care
shot("C01", "24", 2.0, 1.25, b1(67.50), b1(76.17), cy=0.55)
shot("C02", "42", 1.0, 1.25, b1(76.17), b1(80.56), cy=0.45)
shot("C03", "43", 0.5, "c", b1(80.56), b1(84.95), cy=0.5)
shot("C04", "44", 6.0, 1.25, b1(84.95), b1(89.35), cy=0.5)
shot("C05", "22", 0.5, 1.25, b1(89.35), b1(93.65), cy=0.5)
shot("C06", "11", 50.4, 1.25, b1(93.65), b1(102.39), cy=0.58)
# ACT IV - inauguration & hope
shot("D01", "31", 3.0, 1.25, b1(102.39), b1(102.39) + 7.6, cy=0.5)
D2_START = SHOTS[-1]["t1"]
REVEAL = fr(D2_START + (REVEAL_SRC - D2_SRC_IN))
M2 = REVEAL - P2_HIT                                # part-2 music offset
def b2(src):
    return fr(src + M2)
shot("D02", "34", D2_SRC_IN, 1.0, D2_START, b2(293.34), cy=0.45)
shot("D03", "34", 21.4, 1.0, b2(293.34), b2(297.70), cy=0.45)
shot("D04", "8", 7.2, 1.25, b2(297.70), b2(302.07), cy=0.5)
shot("D05", "11", 37.6, 1.25, b2(302.07), b2(306.43), cy=0.55)
shot("D06", "1", 3.9, "c", b2(306.43), b2(319.53), cy=0.45, look="1@hope", fout=1.8)
CREDITS_IN = b2(319.53)
END = fr(P2_END + M2 + 0.6)

# ---------------------------------------------------------------- on-screen text (Bangla, Google Sans)
# (start, end, style, text)
TEXT = [
    (7.2, 11.0, "Place", "ঢাকা"),
    (15.0, 18.9, "Line", "দুই কোটিরও বেশি মানুষের শহর"),
    (20.3, 24.9, "Line", "নদী ক্লান্ত, বাতাস ভারী"),
    (43.4, 46.6, "Line", "এই শহরে পাখিরা বসবে কোথায়?"),
    (TITLE_IN, b1(10.73) - 0.35, "Title", "আকাশনীড়"),
    (TITLE_IN + 0.9, b1(10.73) - 0.35, "Sub", "পাখির রাজ্যে আমন্ত্রণ"),
    (b1(32.61) + 0.5, b1(36.93) - 0.3, "Line", "কংক্রিটের ছাদে ফিরেছে সবুজ"),
    (b1(54.42) + 1.4, b1(63.16) - 1.6, "Line", "পাখিদের জন্য বাসা"),
    (b1(67.50) + 1.4, b1(76.17) - 1.6, "Line", "যত্নে গড়া আশ্রয়"),
    (b1(93.65) + 1.8, b1(102.39) - 0.8, "Line", "প্রকৃতিকে জায়গা দিলে, প্রকৃতি ফিরে আসে"),
    (REVEAL + 0.7, b2(293.34) - 0.3, "Lower", "শুভ উদ্বোধন  ·  ১৬ সেপ্টেম্বর ২০২৬"),
    (b2(306.43) + 2.2, b2(319.53) - 2.6, "Line", "এই শহরের প্রতিটি ছাদ হতে পারে একটি আকাশনীড়"),
    # credits on black
    (CREDITS_IN + 0.8, CREDITS_IN + 7.4, "Title", "আকাশনীড়"),
    (CREDITS_IN + 1.6, CREDITS_IN + 7.4, "Sub", "জেলা প্রশাসকের কার্যালয়, ঢাকা"),
    (CREDITS_IN + 8.0, CREDITS_IN + 14.6, "Credit",
     r"শুভ উদ্বোধন\N{\fs46\b1}মোঃ মনিরুজ্জামান মিঞা{\b0\fs34}\Nবিভাগীয় কমিশনার, ঢাকা"
     r"\N\N{\fs34}পরিকল্পনা ও বাস্তবায়নে\N{\fs46\b1}ফরিদা খানম{\b0\fs34}\Nজেলা প্রশাসক ও জেলা ম্যাজিস্ট্রেট, ঢাকা"),
    (CREDITS_IN + 15.0, END - 0.4, "Small",
     r"ছাদবাগান বাস্তবায়নে: গ্রীন সেভার্স\N\Nসংগীত: “A Kind of Hope” — Scott Buckley (CC BY 4.0)\Nশব্দ: ElevenLabs"),
]

if __name__ == "__main__":
    for s in SHOTS:
        print(f'{s["id"]:4} clip {s["clip"]:>3}  src {s["src_in"]:6.2f}+{(s["t1"]-s["t0"])/s["slow"]:5.2f}  '
              f'film {s["t0"]:7.3f} -> {s["t1"]:7.3f}  ({s["t1"]-s["t0"]:.2f}s, slow {s["slow"]:.3f})')
    print("SMASH", SMASH, "TITLE_IN", TITLE_IN, "REVEAL", REVEAL, "M2", round(M2, 3), "CREDITS", CREDITS_IN, "END", END)
