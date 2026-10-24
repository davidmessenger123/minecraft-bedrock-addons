"""
Species roster for the NZ Animals add-on.

MEASUREMENTS ARE REAL. The figures below come from published sources:

  NZBO   New Zealand Birds Online (nzbirdsonline.org.nz) - length, mass
  TP     Te Papa Tongarewa Collections Biostore - specimen medians (bill,
         tarsus, toe-and-claw, wing chord, tail) with n = 23..168 per species
  SRIR58 DOC Sci-Tech Report 58 - yellow-eyed penguin morphometrics
  WP     Wikipedia species pages
  DOC    Department of Conservation
  TEARA  Te Ara Encyclopedia of New Zealand
  NZHERP New Zealand Herpetology - tuatara
  MASSEY Massey University / wetageta - giant weta
  D      DERIVED by arithmetic from the published totals (head and torso
         sub-dimensions are not published directly)

All lengths are CENTIMETRES. The model builders lay the animal out in these
centimetres so its proportions are literally correct, and `target` says how
long it should be in Minecraft units (1 unit = 1/16 block). The generator
scales one to the other.

`target` is chosen so each species lands at a sensible Minecraft mob size
(a chicken is 16 units / 1 block) rather than at literal real-world scale,
which would make a kiwi four units tall and a sperm whale thirteen blocks
long.

Species note: the giant land snail is Powelliphanta (the largest NZ land
snail, shell ~9 cm) - "poranga" is not a NZ snail genus.
"""


def bird(body, bill, head, leg, foot, wing, tail, crest=0.0):
    """
    Derive builder parameters from published bird morphometrics.

    body  torso length, width, height
    bill  culmen length
    head  SKULL length, width, height (the bill is added separately)
    leg   total leg length (tarsus + toe)
    wing  wing chord
    tail  tail length
    """
    bl, bw, bh = body
    hl, hw, hh = head
    return dict(
        body_len=bl, body_h=bh, body_w=bw,
        head_len=hl, head_h=hh, head_w=hw,
        beak_len=bill, beak_w=max(0.8, bill * 0.32), beak_h=max(0.7, bill * 0.28),
        leg_upper=leg * 0.45, leg_lower=leg * 0.55, foot_len=foot,
        leg_d=max(1.2, leg * 0.17),
        wing_len=min(wing, bl * 0.85), wing_h=max(2.0, bh * 0.55), wing_t=max(1.0, bw * 0.14),
        tail_len=tail, tail_h=max(1.5, bh * 0.40), tail_w=max(2.0, bw * 0.60),
        crest=crest,
    )


def penguin(body, bill, head, leg, foot, flipper, tail, crest=0.0):
    """
    Penguins. `body` is the torso's length along the back, width and chest
    depth, all measured on the bird LYING DOWN. A standing penguin carries
    that long axis VERTICALLY, so it becomes the builder's height and the
    chest depth becomes the front-to-back depth.
    """
    back_len, bw, chest_d = body
    head_total, hw, hh = head
    return dict(
        body_h=back_len, body_len=chest_d, body_w=bw,
        head_len=max(1.5, head_total - bill), head_h=hh, head_w=hw,
        beak_len=bill, beak_w=max(0.8, bill * 0.34), beak_h=max(0.7, bill * 0.30),
        foot_len=foot, foot_w=max(3.0, foot * 0.45), foot_h=max(1.2, foot * 0.18),
        flipper_len=flipper, flipper_w=max(2.0, flipper * 0.30),
        tail_len=tail, tail_h=max(1.5, back_len * 0.10), tail_w=max(2.0, bw * 0.35),
        crest=crest,
    )


def quadruped(body, head, snout, limb, foot, tail, flipper=False, crest=0.0):
    bl, bw, bh = body
    hl, hw, hh = head
    return dict(
        body_len=bl, body_h=bh, body_w=bw,
        head_len=hl, head_h=hh, head_w=hw, snout_len=snout,
        leg_upper=limb * 0.45, leg_lower=limb * 0.55, foot_len=foot,
        leg_d=max(1.5, limb * 0.55),
        tail_len=tail, tail_h=max(1.2, bh * 0.28), tail_w=max(1.5, bw * 0.22),
        flipper=flipper, crest=crest,
    )


def swimmer(total, body, head, rostrum, flipper, dorsal, fluke, shark=False):
    tl, bw, bh = body
    hl, hw, hh = head
    return dict(
        total_len=total, body_h=bh, body_w=bw,
        rostrum_len=rostrum,
        flipper_len=flipper[0], flipper_w=flipper[1],
        dorsal_h=dorsal, fluke_len=fluke[0], fluke_w=fluke[1],
        shark=shark,
    )


# ---------------------------------------------------------------------------
# palettes
# ---------------------------------------------------------------------------
# body, head, back, belly, beak, leg, foot, wing, wing_top, tail, crest, brow,
# muzzle, neck, fin, antenna, shell, shell2, shell_top, spine, flipper

ROSTER = [
    # ---------------- birds ----------------
    dict(id="tui", name="Tui", kind="ground", motion="bird_ground",
         biome=["forest", "plains"], arch="bird", hp=10, speed=0.35,
         weight=6, herd=(1, 4), brightness=(7, 15), target=16,
         drops=[("minecraft:feather", 1, 3)],
         real=bird(body=(12.1, 5.1, 7.3), bill=2.4, head=(3.5, 3.5, 4.0),
                   leg=7.0, foot=3.1, wing=15.0, tail=11.6, crest=2.0),
         pal=dict(body=(30, 36, 56), head=(26, 30, 44), back=(22, 26, 40),
                  belly=(214, 216, 226), beak=(24, 26, 34), leg=(30, 36, 56),
                  foot=(26, 30, 46), wing=(24, 28, 46), wing_top=(54, 78, 104),
                  tail=(30, 36, 56), brow=(20, 24, 38), crest=(236, 238, 244),
                  neck=(30, 36, 56))),
    dict(id="kiwi", name="Kiwi", kind="ground", motion="bird_ground",
         biome=["forest", "plains"], arch="bird", hp=10, speed=0.2,
         weight=4, herd=(1, 1), brightness=(0, 15), target=24,
         drops=[("minecraft:egg", 0, 1), ("minecraft:feather", 1, 3)],
         real=bird(body=(26.6, 14.0, 18.6), bill=11.5, head=(6.0, 5.5, 6.0),
                   leg=17.1, foot=8.5, wing=12.0, tail=2.0),
         pal=dict(body=(146, 108, 58), head=(162, 124, 70), back=(118, 86, 50),
                  belly=(138, 108, 76), beak=(198, 182, 142), leg=(196, 152, 120),
                  foot=(180, 138, 108), wing=(96, 68, 44), wing_top=(112, 82, 54),
                  tail=(88, 62, 40), brow=(96, 68, 44), neck=(104, 74, 47))),
    dict(id="kakapo", name="Kakapo", kind="ground", motion="bird_ground",
         biome=["forest"], arch="bird", hp=16, speed=0.16,
         weight=2, herd=(1, 1), brightness=(0, 15), target=30,
         drops=[("minecraft:feather", 2, 4)],
         real=bird(body=(29.0, 19.7, 23.2), bill=3.5, head=(5.5, 5.9, 6.8),
                   leg=12.5, foot=7.0, wing=26.0, tail=21.8),
         pal=dict(body=(74, 107, 58), head=(107, 138, 74), back=(64, 92, 50),
                  belly=(124, 150, 96), beak=(150, 140, 110), leg=(74, 107, 58),
                  foot=(70, 100, 54), wing=(84, 118, 64), wing_top=(96, 130, 76),
                  tail=(74, 107, 58), brow=(88, 118, 68), neck=(80, 112, 62))),
    dict(id="kea", name="Kea", kind="fly", motion="bird_fly",
         biome=["cold", "hills"], arch="bird", hp=12, speed=0.35,
         weight=4, herd=(1, 3), brightness=(7, 15), target=26,
         drops=[("minecraft:feather", 1, 3)],
         real=bird(body=(20.9, 9.1, 13.0), bill=4.8, head=(6.0, 6.3, 7.2),
                   leg=10.3, foot=5.6, wing=31.4, tail=15.9),
         pal=dict(body=(107, 90, 62), head=(138, 112, 74), back=(88, 74, 50),
                  belly=(150, 122, 84), beak=(230, 146, 44), leg=(107, 90, 62),
                  foot=(120, 100, 74), wing=(122, 102, 70), wing_top=(148, 124, 86),
                  tail=(96, 80, 54), brow=(126, 102, 68), neck=(112, 94, 66))),
    dict(id="kaka", name="Kaka", kind="fly", motion="bird_fly",
         biome=["forest"], arch="bird", hp=12, speed=0.35,
         weight=6, herd=(1, 3), brightness=(7, 15), target=24,
         drops=[("minecraft:feather", 1, 3)],
         real=bird(body=(16.2, 7.0, 10.0), bill=4.5, head=(5.5, 5.9, 6.8),
                   leg=8.5, foot=4.9, wing=26.7, tail=15.2),
         pal=dict(body=(92, 70, 48), head=(116, 112, 106), back=(76, 58, 40),
                  belly=(134, 104, 68), beak=(58, 48, 40), leg=(92, 70, 48),
                  foot=(104, 80, 54), wing=(104, 80, 54), wing_top=(128, 98, 64),
                  tail=(92, 70, 48), brow=(112, 86, 56), neck=(98, 76, 52))),
    dict(id="hihi", name="Hihi", kind="fly", motion="bird_fly",
         biome=["forest"], arch="bird", hp=8, speed=0.35,
         weight=5, herd=(1, 3), brightness=(7, 15), target=13,
         drops=[("minecraft:feather", 0, 2)],
         real=bird(body=(6.1, 2.8, 3.9), bill=1.6, head=(3.0, 2.8, 3.2),
                   leg=4.8, foot=2.0, wing=9.6, tail=6.9),
         pal=dict(body=(126, 102, 70), head=(114, 92, 64), back=(94, 76, 54),
                  belly=(232, 232, 234), beak=(52, 48, 44), leg=(204, 148, 138),
                  foot=(194, 140, 130), wing=(106, 86, 60), wing_top=(98, 78, 56),
                  tail=(86, 70, 52), brow=(104, 84, 60), neck=(118, 96, 66))),
    dict(id="kereru", name="Kereru", kind="fly", motion="bird_fly",
         biome=["forest", "plains"], arch="bird", hp=12, speed=0.32,
         weight=6, herd=(1, 3), brightness=(7, 15), target=26,
         drops=[("minecraft:feather", 1, 3)],
         real=bird(body=(22.2, 9.3, 13.3), bill=2.6, head=(5.0, 4.7, 5.4),
                   leg=8.2, foot=4.5, wing=26.1, tail=19.4),
         pal=dict(body=(92, 104, 118), head=(86, 110, 92), back=(78, 90, 106),
                  belly=(140, 148, 158), beak=(58, 53, 48), leg=(140, 78, 70),
                  foot=(132, 74, 66), wing=(88, 100, 116), wing_top=(104, 136, 116),
                  tail=(88, 100, 116), brow=(76, 96, 82), neck=(92, 104, 118))),
    dict(id="pukeko", name="Pukeko", kind="fly", motion="bird_fly",
         biome=["swamp", "river"], arch="bird", hp=12, speed=0.3,
         weight=6, herd=(2, 5), brightness=(7, 15), target=26,
         drops=[("minecraft:feather", 1, 3), ("minecraft:egg", 0, 1)],
         real=bird(body=(27.5, 13.1, 18.7), bill=6.7, head=(7.0, 7.8, 9.0),
                   leg=18.9, foot=9.8, wing=25.8, tail=10.1),
         pal=dict(body=(28, 36, 54), head=(26, 32, 50), back=(22, 28, 44),
                  belly=(52, 62, 84), beak=(198, 52, 40), leg=(196, 74, 52),
                  foot=(180, 66, 46), wing=(26, 32, 50), wing_top=(44, 54, 78),
                  tail=(28, 36, 54), brow=(22, 28, 44), neck=(28, 36, 54))),
    dict(id="morepork", name="Morepork", kind="fly", motion="bird_fly",
         biome=["forest"], arch="bird", hp=10, speed=0.3,
         weight=5, herd=(1, 2), brightness=(0, 15), target=19,
         drops=[("minecraft:feather", 1, 2)],
         real=bird(body=(10.3, 5.8, 7.7), bill=1.5, head=(4.5, 3.8, 4.4),
                   leg=6.7, foot=3.1, wing=19.3, tail=12.35),
         pal=dict(body=(104, 92, 74), head=(120, 108, 88), back=(84, 74, 60),
                  belly=(152, 142, 120), beak=(48, 44, 40), leg=(104, 92, 74),
                  foot=(116, 102, 82), wing=(88, 78, 64), wing_top=(124, 110, 90),
                  tail=(84, 74, 60), brow=(92, 82, 66), neck=(104, 92, 74))),
    dict(id="kotare", name="Kotare", kind="fly", motion="bird_fly",
         biome=["river", "beach"], arch="bird", hp=8, speed=0.35,
         weight=5, herd=(1, 2), brightness=(7, 15), target=15,
         drops=[("minecraft:feather", 0, 2), ("minecraft:cod", 0, 1)],
         real=bird(body=(8.0, 3.6, 5.2), bill=4.15, head=(4.0, 4.9, 5.6),
                   leg=3.6, foot=2.1, wing=10.2, tail=6.6),
         pal=dict(body=(46, 124, 140), head=(58, 142, 156), back=(36, 104, 118),
                  belly=(214, 146, 72), beak=(38, 34, 30), leg=(196, 110, 62),
                  foot=(186, 104, 58), wing=(40, 110, 124), wing_top=(70, 150, 164),
                  tail=(46, 124, 140), brow=(36, 104, 118), neck=(46, 124, 140))),
    dict(id="tieke", name="Tieke", kind="fly", motion="bird_fly",
         biome=["forest"], arch="bird", hp=8, speed=0.33,
         weight=5, herd=(1, 3), brightness=(7, 15), target=17,
         drops=[("minecraft:feather", 0, 2)],
         real=bird(body=(9.0, 4.1, 5.9), bill=3.25, head=(4.0, 4.4, 5.0),
                   leg=6.9, foot=2.9, wing=9.4, tail=8.4),
         pal=dict(body=(28, 28, 30), head=(26, 26, 28), back=(22, 22, 24),
                  belly=(48, 48, 52), beak=(48, 44, 40), leg=(28, 28, 30),
                  foot=(26, 26, 28), wing=(28, 28, 30), wing_top=(168, 96, 48),
                  tail=(28, 28, 30), brow=(26, 26, 28), neck=(28, 28, 30))),
    dict(id="whio", name="Whio", kind="ground", motion="bird_ground",
         biome=["river", "swamp"], arch="bird", hp=12, speed=0.22,
         weight=4, herd=(2, 4), brightness=(7, 15), target=24,
         drops=[("minecraft:feather", 2, 4), ("minecraft:egg", 0, 1)],
         real=bird(body=(31.9, 13.4, 19.1), bill=4.4, head=(5.0, 5.6, 6.4),
                   leg=11.2, foot=6.4, wing=23.1, tail=11.0),
         pal=dict(body=(76, 92, 110), head=(236, 236, 236), back=(64, 78, 94),
                  belly=(214, 190, 176), beak=(48, 44, 40), leg=(58, 68, 82),
                  foot=(52, 62, 76), wing=(70, 84, 100), wing_top=(88, 104, 122),
                  tail=(64, 78, 94), brow=(216, 218, 220), neck=(76, 92, 110))),
    dict(id="huia", name="Huia", kind="fly", motion="bird_fly",
         biome=["forest"], arch="bird", hp=10, speed=0.32,
         weight=3, herd=(1, 2), brightness=(7, 15), target=26,
         drops=[("minecraft:feather", 1, 3)],
         real=bird(body=(11.2, 4.7, 6.7), bill=6.0, head=(5.5, 8.0, 9.2),
                   leg=7.8, foot=3.5, wing=21.0, tail=20.0),
         pal=dict(body=(26, 26, 28), head=(24, 24, 26), back=(22, 22, 24),
                  belly=(48, 48, 52), beak=(38, 38, 40), leg=(26, 26, 28),
                  foot=(24, 24, 26), wing=(24, 24, 26), wing_top=(54, 52, 52),
                  tail=(26, 26, 28), brow=(22, 22, 24), neck=(26, 26, 28))),
    dict(id="haasts_eagle", name="Haast's Eagle", kind="fly", motion="bird_fly",
         biome=["forest", "hills"], arch="bird", hp=26, speed=0.38,
         weight=2, herd=(1, 2), brightness=(7, 15), target=50,
         drops=[("minecraft:feather", 2, 4), ("minecraft:beef", 0, 1)],
         real=bird(body=(56.0, 24.0, 34.0), bill=11.4, head=(20.0, 18.0, 21.0),
                   leg=15.0, foot=8.0, wing=60.0, tail=50.0, crest=6.0),
         pal=dict(body=(88, 58, 32), head=(70, 46, 26), back=(64, 42, 24),
                  belly=(156, 112, 70), beak=(78, 68, 56), leg=(178, 160, 118),
                  foot=(168, 150, 110), wing=(80, 52, 28), wing_top=(126, 88, 52),
                  tail=(70, 46, 26), brow=(60, 40, 22), crest=(60, 40, 22),
                  neck=(78, 52, 30))),

    # ---------------- penguins ----------------
    dict(id="rockhopper_penguin", name="Rockhopper Penguin", kind="amphib",
         motion="penguin", biome=["cold", "shore"], arch="penguin", hp=12, speed=0.2,
         weight=4, herd=(2, 6), brightness=(7, 15), target=26,
         drops=[("minecraft:cod", 0, 2), ("minecraft:feather", 0, 1)],
         scale_by="height", real=penguin(body=(29.5, 11.1, 14.7), bill=4.77, head=(7.0, 9.4, 8.3),
                      leg=11.8, foot=7.8, flipper=16.8, tail=6.95, crest=3.5),
         pal=dict(body=(38, 38, 42), head=(34, 34, 38), back=(28, 28, 32),
                  belly=(238, 238, 234), beak=(214, 96, 40), leg=(206, 132, 130),
                  foot=(200, 124, 124), wing=(30, 30, 34), wing_top=(52, 52, 58),
                  tail=(38, 38, 42), brow=(44, 44, 50), crest=(232, 190, 72),
                  neck=(38, 38, 42))),
    dict(id="yellow_eyed_penguin", name="Yellow-eyed Penguin", kind="amphib",
         motion="penguin", biome=["forest", "beach", "shore"], arch="penguin",
         hp=12, speed=0.2, weight=3, herd=(2, 5), brightness=(7, 15), target=32,
         drops=[("minecraft:cod", 0, 2)],
         scale_by="height", real=penguin(body=(48.9, 18.3, 24.5), bill=5.36, head=(8.5, 11.1, 9.7),
                      leg=14.9, foot=13.2, flipper=20.7, tail=7.1),
         pal=dict(body=(30, 30, 34), head=(28, 28, 32), back=(24, 24, 28),
                  belly=(238, 238, 232), beak=(38, 38, 40), leg=(212, 140, 140),
                  foot=(212, 140, 140), wing=(22, 22, 26), wing_top=(44, 44, 50),
                  tail=(30, 30, 34), brow=(228, 206, 92), neck=(30, 30, 34))),
    dict(id="little_penguin", name="Little Penguin", kind="amphib",
         motion="penguin", biome=["beach", "shore"], arch="penguin", hp=8, speed=0.2,
         weight=4, herd=(2, 6), brightness=(7, 15), target=20,
         drops=[("minecraft:cod", 0, 1)],
         scale_by="height", real=penguin(body=(19.5, 7.3, 9.7), bill=3.55, head=(5.3, 6.2, 7.1),
                      leg=7.2, foot=5.2, flipper=11.9, tail=3.3),
         pal=dict(body=(54, 60, 78), head=(48, 58, 70), back=(44, 54, 66),
                  belly=(240, 240, 238), beak=(38, 38, 40), leg=(38, 38, 40),
                  foot=(34, 34, 36), wing=(46, 56, 68), wing_top=(72, 84, 100),
                  tail=(54, 60, 78), brow=(44, 54, 66), neck=(54, 60, 78))),

    # ---------------- land vertebrates & invertebrates ----------------
    dict(id="tuatara", name="Tuatara", kind="ground", motion="quadruped",
         biome=["forest", "hills"], arch="quadruped", hp=14, speed=0.16,
         weight=3, herd=(1, 2), brightness=(0, 15), target=28,
         drops=[("minecraft:leather", 0, 1)],
         real=quadruped(body=(18.0, 5.0, 6.0), head=(6.5, 5.0, 4.5),
                       snout=3.5, limb=4.5, foot=2.0, tail=24.0, crest=1.5),
         pal=dict(body=(98, 106, 76), head=(112, 120, 88), back=(80, 88, 62),
                  belly=(158, 164, 128), beak=(40, 36, 32), leg=(122, 126, 100),
                  foot=(112, 116, 92), tail=(86, 94, 68), brow=(84, 92, 66),
                  muzzle=(112, 120, 88), crest=(206, 198, 152),
                  neck=(98, 106, 76))),
    dict(id="powelliphanta", name="Powelliphanta", kind="ground", motion="snail",
         biome=["forest", "swamp"], arch="snail", hp=8, speed=0.06,
         weight=3, herd=(1, 1), brightness=(0, 15), target=16,
         drops=[],
         real=dict(shell_w=9.0, shell_h=7.0, shell_d=9.0,
                   foot_len=11.0, foot_h=2.0, foot_w=7.0,
                   head_len=2.5, tentacle_len=3.0, tentacle_d=0.5),
         pal=dict(body=(150, 138, 118), shell=(126, 86, 48), shell2=(100, 66, 36),
                  shell_top=(140, 98, 56), back=(150, 138, 118))),
    dict(id="weta", name="Weta", kind="ground", motion="insect",
         biome=["forest", "plains"], arch="insect", hp=8, speed=0.18,
         weight=5, herd=(1, 3), brightness=(0, 15), target=16,
         drops=[],
         real=dict(segments=((1.5, 1.2, 1.4), (1.8, 1.6, 1.8), (6.0, 1.8, 2.0)),
                   leg_upper=8.0, leg_lower=8.0, leg_d=0.4,
                   antenna_len=12.0, antenna_segments=4, spines=True, stand=3.0),
         pal=dict(body=(108, 74, 44), body2=(84, 56, 32), leg=(58, 44, 28),
                  antenna=(52, 38, 24), spine=(40, 30, 18), back=(70, 50, 32))),
    dict(id="huhu", name="Huhu", kind="ground", motion="insect",
         biome=["forest", "plains"], arch="insect", hp=10, speed=0.16,
         weight=5, herd=(1, 2), brightness=(0, 15), target=14,
         drops=[],
         real=dict(segments=((0.9, 0.9, 1.0), (1.6, 1.1, 2.0), (2.6, 1.3, 2.4)),
                   leg_upper=1.5, leg_lower=1.5, leg_d=0.4,
                   antenna_len=1.8, antenna_segments=3, spines=False, stand=0.8),
         pal=dict(body=(88, 74, 46), body2=(66, 54, 34), leg=(30, 24, 18),
                  antenna=(28, 22, 16), spine=(30, 24, 18), back=(36, 28, 20))),

    # ---------------- marine ----------------
    dict(id="nz_sea_lion", name="New Zealand Sea Lion", kind="amphib",
         motion="seal", biome=["shore", "beach", "ocean"], arch="quadruped",
         hp=20, speed=0.25, weight=6, herd=(1, 6), brightness=(0, 15), target=62,
         drops=[("minecraft:cod", 1, 3), ("minecraft:beef", 0, 2)],
         real=quadruped(body=(205.0, 110.0, 49.0), head=(46.0, 36.0, 30.0),
                       snout=12.0, limb=16.0, foot=47.0, tail=30.0, flipper=True),
         pal=dict(body=(150, 112, 78), head=(162, 124, 86), back=(128, 96, 68),
                  belly=(196, 172, 142), beak=(52, 46, 42), leg=(96, 86, 76),
                  foot=(88, 78, 70), tail=(100, 90, 80), brow=(106, 96, 86),
                  muzzle=(132, 120, 106), flipper=(96, 86, 76),
                  neck=(116, 104, 92))),
    dict(id="nz_fur_seal", name="New Zealand Fur Seal", kind="amphib",
         motion="seal", biome=["ocean", "shore"], arch="quadruped",
         hp=18, speed=0.24, weight=6, herd=(1, 6), brightness=(0, 15), target=46,
         drops=[("minecraft:cod", 1, 3), ("minecraft:beef", 0, 1)],
         real=quadruped(body=(100.0, 32.0, 35.0), head=(30.0, 24.0, 22.0),
                       snout=8.0, limb=12.0, foot=44.0, tail=10.0, flipper=True),
         pal=dict(body=(104, 82, 62), head=(116, 92, 68), back=(86, 68, 52),
                  belly=(136, 104, 76), beak=(44, 38, 34), leg=(74, 54, 40),
                  foot=(68, 50, 38), tail=(74, 54, 40), brow=(80, 58, 42),
                  muzzle=(106, 80, 56), flipper=(74, 54, 40),
                  neck=(88, 64, 46))),
    dict(id="hectors_dolphin", name="Hectors Dolphin", kind="swim", motion="swim",
         biome=["ocean"], arch="swimmer", hp=14, speed=0.14,
         weight=6, herd=(1, 5), brightness=(0, 15), target=40,
         drops=[("minecraft:cod", 0, 2)],
         real=swimmer(total=120.0, body=(85.8, 25.2, 30.0), head=(14.7, 11.0, 10.0),
                      rostrum=12.0, flipper=(21.0, 7.65), dorsal=14.0, fluke=(20.0, 35.0)),
         pal=dict(body=(118, 122, 128), head=(128, 132, 138), back=(100, 104, 110),
                  belly=(196, 200, 206), fin=(98, 102, 108), tail=(98, 102, 108))),
    dict(id="dusky_dolphin", name="Dusky Dolphin", kind="swim", motion="swim",
         biome=["ocean"], arch="swimmer", hp=14, speed=0.15,
         weight=6, herd=(1, 5), brightness=(0, 15), target=52,
         drops=[("minecraft:cod", 0, 2)],
         real=swimmer(total=170.0, body=(124.4, 36.5, 42.0), head=(21.3, 13.0, 12.0),
                      rostrum=18.0, flipper=(30.4, 11.1), dorsal=18.0, fluke=(28.0, 50.7)),
         pal=dict(body=(108, 112, 118), head=(118, 122, 128), back=(94, 98, 104),
                  belly=(188, 192, 196), fin=(92, 96, 100), tail=(92, 96, 100))),
    dict(id="orca", name="Orca", kind="swim", motion="swim",
         biome=["ocean"], arch="swimmer", hp=30, speed=0.18,
         weight=3, herd=(1, 4), brightness=(0, 15), target=84,
         drops=[("minecraft:cod", 2, 5)],
         real=swimmer(total=650.0, body=(582.0, 135.0, 150.0), head=(127.0, 60.0, 55.0),
                      rostrum=55.0, flipper=(55.0, 25.0), dorsal=65.0, fluke=(55.0, 200.0)),
         pal=dict(body=(26, 26, 28), head=(30, 30, 32), back=(20, 20, 22),
                  belly=(236, 236, 236), fin=(22, 22, 24), tail=(22, 22, 24))),
    dict(id="sperm_whale", name="Sperm Whale", kind="swim", motion="swim",
         biome=["ocean"], arch="swimmer", hp=34, speed=0.16,
         weight=2, herd=(1, 3), brightness=(0, 15), target=96,
         drops=[("minecraft:cod", 2, 5)],
         real=swimmer(total=1600.0, body=(1067.0, 300.0, 260.0), head=(514.0, 150.0, 130.0),
                      rostrum=400.0, flipper=(172.0, 74.0), dorsal=0.0, fluke=(120.0, 410.0)),
         pal=dict(body=(94, 90, 86), head=(102, 98, 94), back=(74, 72, 70),
                  belly=(160, 156, 150), fin=(72, 70, 68), tail=(72, 70, 68))),
    dict(id="blue_shark", name="Blue Shark", kind="swim", motion="swim",
         biome=["ocean"], arch="swimmer", hp=24, speed=0.16,
         weight=3, herd=(1, 3), brightness=(0, 15), target=58,
         drops=[("minecraft:pufferfish", 0, 1), ("minecraft:cod", 1, 3)],
         real=swimmer(total=310.0, body=(170.0, 26.0, 40.0), head=(68.0, 22.0, 20.0),
                      rostrum=55.0, flipper=(62.0, 22.0), dorsal=45.0, fluke=(45.0, 65.0),
                      shark=True),
         pal=dict(body=(78, 106, 140), head=(96, 124, 156), back=(66, 92, 124),
                  belly=(226, 232, 238), fin=(66, 92, 124), tail=(66, 92, 124))),

    # ---------------- extinct ----------------
    dict(id="moa", name="Moa", kind="ground", motion="ratite",
         biome=["forest", "plains"], arch="ratite", hp=24, speed=0.2,
         weight=2, herd=(1, 3), brightness=(7, 15), target=40,
         drops=[("minecraft:beef", 1, 3), ("minecraft:leather", 0, 2)],
         scale_by="height", real=dict(body_len=110.0, body_h=70.0, body_w=65.0,
                   head_len=25.0, head_h=20.0, head_w=20.0,
                   neck_len=95.0, neck_w=24.0,
                   beak_len=12.0, beak_w=5.0, beak_h=3.0,
                   leg_upper=40.0, leg_lower=40.0, foot_len=22.0, leg_d=16.0,
                   tail_len=20.0, tail_h=10.0, tail_w=12.0),
         pal=dict(body=(124, 104, 74), head=(134, 112, 80), back=(104, 86, 60),
                  belly=(176, 158, 124), beak=(40, 36, 32), leg=(134, 116, 92),
                  foot=(124, 108, 86), tail=(104, 86, 60), neck=(124, 104, 74),
                  brow=(112, 94, 66))),
]
