#!/usr/bin/env python3
"""Generate the animated pixel-art profile assets.

  assets/hud.svg        player card: level, live stats, achievements
  assets/quest-map.svg  sky archipelago timeline with a blimp (and a cat)
                        flying over a city built from your contribution graph

Usage:  python3 scripts/gen.py [profile.json] [data/stats.json]
stats.json is written by scripts/fetch_stats.py (GitHub Action); without it
live numbers show as "--" and the city skyline is procedural.
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, text_width  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Palette: midnight sky, neon circuitry, warm cat ─────────────────────────
SKY = ["#060818", "#080c22", "#0b112d", "#0f1638", "#131c44", "#18224f",
       "#1e2759", "#262b63", "#30306c", "#3b3474"]
INK = "#e8ecff"
DIM = "#8a94c9"
CYAN = "#5ef2ff"
MINT = "#7cffc4"
PINK = "#ff5fd2"
GOLD = "#ffd166"
P = 4  # scene pixel size
BP = 3  # blimp pixel size

W, H = 1000, 460


def fmt(n):
    if n is None:
        return "--"
    if n >= 10000:
        return f"{n / 1000:.1f}K".replace(".0K", "K")
    return str(n)


# ── Shared bits ─────────────────────────────────────────────────────────────
def scanlines(w, h, uid):
    return (f'<defs><pattern id="scan{uid}" width="4" height="4" patternUnits="userSpaceOnUse">'
            f'<rect width="4" height="1" fill="#000" fill-opacity=".22"/></pattern></defs>'
            f'<rect width="{w}" height="{h}" fill="url(#scan{uid})" pointer-events="none"/>')


def brackets(c, w, h, color, inset=8, arm=24, t=4):
    for x, y, sx, sy in ((inset, inset, 1, 1), (w - inset, inset, -1, 1),
                         (inset, h - inset, 1, -1), (w - inset, h - inset, -1, -1)):
        c.rect(min(x, x + sx * arm), y if sy > 0 else y - t, arm, t, color)
        c.rect(x if sx > 0 else x - t, min(y, y + sy * arm), t, arm, color)


def sky_bands(c, w, h):
    band = h / len(SKY)
    for i, col in enumerate(SKY):
        y0 = round(i * band / P) * P
        y1 = round((i + 1) * band / P) * P
        c.rect(0, y0, w, y1 - y0, col)
        if i + 1 < len(SKY):  # checkerboard dither between bands
            nxt = SKY[i + 1]
            for x in range(0, w, P * 2):
                c.rect(x + ((y1 // P) % 2) * P, y1 - P, P, P, nxt)


# ── Sprites ────────────────────────────────────────────────────────────────
ICONS = {
    "dumbbell": ([
        ".hh......hh.",
        "hmm......mmh",
        "mmmhhhhhhmmm",
        "mmmssssssmmm",
        "smm......mms",
        ".ss......ss.",
    ], {"h": "#ffffff", "m": "#c3cbff", "s": "#6f79b8"}),
    "database": ([
        ".cccccc.",
        "cddddddc",
        "bccccccb",
        "bbbbbbbl",
        "bbbbbbbb",
        "cccccccc",
        "bbbbbbbl",
        "bbbbbbbb",
        "cccccccc",
        "bbbbbbbl",
        ".bbbbbb.",
    ], {"c": CYAN, "d": "#1aa9c4", "b": "#2c3f8f", "l": MINT}),
    "star": ([
        "s....y.....",
        ".....y.....",
        "....yWy....",
        "...yWWWy...",
        "yyyWWWWWyyy",
        "...yWWWy...",
        "....yWy....",
        ".....y.....",
        ".....y....s",
    ], {"y": "#fff3b0", "W": "#ffffff", "s": CYAN}),
    "trophy": ([
        "..ggggggg..",
        "gggwggggggg",
        "g.gwggggg.g",
        "g.gggggggdg",
        ".ggggggggd.",
        "..gggggdd..",
        "....ggd....",
        ".....g.....",
        "....ggg....",
        "...bbbbb...",
        "...bbbbb...",
    ], {"g": GOLD, "w": "#fff8dc", "d": "#d99a2b", "b": "#7a4fb8"}),
    "magnifier": ([
        "..mmmm....",
        ".mccccm...",
        "mcWccccm..",
        "mcWccccm..",
        "mccccccm..",
        "mccccccm..",
        ".mccccm...",
        "..mmmmhh..",
        "......hhh.",
        ".......hhh",
    ], {"m": "#c3cbff", "c": "#1aa9c4", "W": "#ffffff", "h": PINK}),
    "badge": ([
        "r.......r",
        ".r.....r.",
        "..r...r..",
        "...rbr...",
        ".bbbbbbb.",
        ".bwwwwwb.",
        ".bwccwwb.",
        ".bwwwwwb.",
        ".bccccwb.",
        ".bwwwwwb.",
        ".bbbbbbb.",
    ], {"r": PINK, "b": "#9aa6d8", "w": "#e8ecff", "c": CYAN}),
    "butterfly": ([
        "pp.......pp",
        "ppp.....ppp",
        "pWpp.b.ppWp",
        "ppppbbbpppp",
        ".pppbbbppp.",
        "..ccbbbcc..",
        ".cccbbbccc.",
        ".cWc.b.cWc.",
        "..c.....c..",
    ], {"p": PINK, "W": "#ffffff", "c": CYAN, "b": "#e8ecff"}),
    "book": ([
        "bbbbbbbbbb",
        "bggggggggb",
        "bbbbbbbbbb",
        ".rrrrrrrrr",
        ".rwwwwwwwr",
        ".rrrrrrrrr",
        "cccccccccc",
        "cwwwwwwwwc",
        "cccccccccc",
    ], {"b": "#7a4fb8", "g": GOLD, "r": PINK, "w": "#e8ecff", "c": CYAN}),
    "beacon": ([
        "...r...",
        "..rrr..",
        "...m...",
        "..m.m..",
        "..mmm..",
        ".m...m.",
        ".mmmmm.",
        "m.....m",
    ], {"r": PINK, "m": "#9aa6d8"}),
}


def island(c, glow, cx, top, w, depth, rng):
    half = w // (2 * P)
    ox = cx - half * P
    rows = depth // P
    for r in range(rows):
        if r == 0:
            c.cells([(x, 0) for x in range(1, 2 * half)], P, ox, top, "#9dffc8")
        elif r == 1:
            c.cells([(x, 0) for x in range(0, 2 * half + 1)], P, ox, top + P, "#3fcf8e")
        elif r == 2:
            c.cells([(x, 0) for x in range(0, 2 * half + 1)], P, ox, top + 2 * P, "#239669")
            for x in range(0, 2 * half + 1):  # grass drips
                if rng.random() < .3:
                    c.rect(ox + x * P, top + 3 * P, P, P, "#239669")
        else:
            t = (r - 3) / max(1, rows - 4)
            hw = max(0, half * (1 - t ** 1.5) + rng.choice((-1, 0, 0, 1)))
            x0, x1 = round(half - hw), round(half + hw)
            col = ("#3d3577", "#322b67", "#282257", "#1f1a47")[min(3, int(t * 4))]
            if r == 3:
                x0, x1 = 0, 2 * half
            if x1 >= x0:
                c.cells([(x, 0) for x in range(x0, x1 + 1)], P, ox, top + r * P, col)
                c.rect(ox + x0 * P, top + r * P, P, P, "#191338")
                # neon circuit veins
                if r % 3 == 1 and x1 - x0 > 4:
                    a = rng.randint(x0 + 1, x1 - 3)
                    glow.cells([(a, 0), (a + 1, 0), (a + 2, 0)], P, ox, top + r * P, CYAN + "@.8")
                    glow.rect(ox + (a + 2) * P, top + (r + 1) * P, P, P, CYAN + "@.8")
    # crystal tip
    tip = top + rows * P
    glow.cells([(half, 0), (half, 1), (half - 1, 0), (half + 1, 0)], P, ox, tip, CYAN)
    glow.rect(ox + half * P, tip + 2 * P, P, P, CYAN + "@.5")


def blimp_parts():
    """Return dict of canvases for the blimp body and its animated pieces."""
    body = Canvas()
    env = []
    cx, cy, rx, ry = 19, 6.5, 15.5, 6.6
    for y in range(0, 14):
        for x in range(3, 36):
            if ((x - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                env.append((x, y))
    envs = set(env)
    shade = {"edge": [], "hi": [], "lo": [], "base": []}
    for x, y in env:
        if any(n not in envs for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
            shade["edge"].append((x, y))
        elif y <= 2 or (y == 3 and x > 22):
            shade["hi"].append((x, y))
        elif y >= 10:
            shade["lo"].append((x, y))
        else:
            shade["base"].append((x, y))
    body.cells(shade["base"], BP, 0, 0, "#dfe6ff")
    body.cells(shade["hi"], BP, 0, 0, "#ffffff")
    body.cells(shade["lo"], BP, 0, 0, "#a3aedf")
    body.cells(shade["edge"], BP, 0, 0, "#5f68a8")
    body.cells([(x, 8) for x in range(5, 34) if (x, 8) in envs and (x, 8) not in shade["edge"]],
               BP, 0, 0, PINK)
    body.cells([(x, 9) for x in range(5, 34) if (x, 9) in envs and (x, 9) not in shade["edge"]],
               BP, 0, 0, "#b8399a")
    # paw-print emblem
    body.sprite([".p.p.", "p.p.p", ".ppp.", ".ppp."], {"p": PINK}, 21 * BP, 3 * BP, BP)
    # tail fins
    body.sprite([
        "ff....",
        "fff...",
        ".fff..",
        "..ff..",
    ], {"f": PINK}, 2 * BP, 1 * BP, BP)
    body.sprite([
        "..ff..",
        ".fff..",
        "fff...",
        "ff....",
    ], {"f": "#b8399a"}, 2 * BP, 9 * BP, BP)
    # ropes
    for x in (14, 24):
        body.cells([(x, y) for y in range(13, 19)], BP, 0, 0, "#5f68a8")
    # cat
    body.sprite([
        "o......o",
        "op....po",
        "oooddooo",
        "oeooooeo",
        "oooppooo",
        "wwoooooww",
    ], {"o": "#ffa94d", "p": "#ff8fb1", "d": "#e0761f", "e": "#1a1033", "w": "#fff1e0"},
        16 * BP, 13 * BP, BP)
    # gondola
    body.cells([(x, 19) for x in range(13, 26)], BP, 0, 0, "#9aa6d8")
    body.cells([(x, 19) for x in (17, 18, 21, 22)], BP, 0, 0, "#ffa94d")  # paws on rim
    body.cells([(x, y) for x in range(13, 26) for y in (20, 21)], BP, 0, 0, "#2b3570")
    body.cells([(x, 20) for x in range(14, 25, 2)], BP, 0, 0, CYAN)
    body.cells([(x, 22) for x in range(14, 25)], BP, 0, 0, "#1b2150")

    blink = Canvas()
    blink.cells([(17, 16), (22, 16)], BP, 0, 0, "#ffa94d")
    tail_a, tail_b = Canvas(), Canvas()
    tail_a.cells([(26, 19), (27, 18), (27, 17), (26, 16)], BP, 0, 0, "#ffa94d")
    tail_b.cells([(26, 19), (26, 18), (27, 17), (28, 17)], BP, 0, 0, "#ffa94d")
    prop_a, prop_b = Canvas(), Canvas()
    prop_a.cells([(11, y) for y in range(18, 24)], BP, 0, 0, "#dfe6ff")
    prop_b.cells([(11, 20), (11, 21), (10, 21), (12, 20)], BP, 0, 0, "#dfe6ff")
    for cv in (prop_a, prop_b):
        cv.rect(11 * BP, 21 * BP - 2, BP, BP, "#5f68a8")
    return body, blink, tail_a, tail_b, prop_a, prop_b


def cloud(c, x, y, w, color, rng):
    gw = w // P
    for i in range(gw):
        t = i / (gw - 1)
        h = int(2 + 3 * math.sin(math.pi * t) + rng.choice((0, 0, 1)))
        c.cells([(i, -j) for j in range(h)], P, x, y, color)


# ── Quest map ───────────────────────────────────────────────────────────────
def quest_map(profile, stats):
    rng = random.Random(88)
    quests = profile["quests"]
    n = len(quests)
    per_row = n if n <= 5 else math.ceil(n / 2)
    nrows = math.ceil(n / per_row)
    H = 445 + (nrows - 1) * 345
    jit = (8, -14, 16, -20, 2)
    xs, tops, rowof = [], [], []
    for i in range(n):
        r, k = divmod(i, per_row)
        cnt = min(per_row, n - r * per_row)
        xs.append(round((W / cnt) * (k + .5) / P) * P)
        tops.append(round((166 + r * 330 + jit[k % 5]) / P) * P)
        rowof.append(r)
    iw, depth = 120, 64

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
                 f'role="img" aria-labelledby="qt qd" shape-rendering="crispEdges">')
    parts.append('<title id="qt">Quest log: project timeline</title>')
    parts.append('<desc id="qd">A pixel-art blimp piloted by a cat flies over floating islands, one per project: '
                 + ", ".join(q["name"].title() for q in quests) + '.</desc>')

    # timing for the blimp tour
    dur = 6 * n + 10
    legs = n + 1 + (nrows - 1)
    hover = 45.0 / n
    travel = (100 - hover * n) / legs
    stops = []  # (arrive%, leave%)
    t = travel
    for i in range(n):
        stops.append((t, t + hover))
        t += hover + travel
    BW, BCX = 36 * BP, 19 * BP  # blimp sprite width, centre offset
    y_cruise = 10
    def icon_h(q):
        return len(ICONS.get(q.get("icon"), ICONS["beacon"])[0]) * 4
    y_hov = [max(4, tops[i] - icon_h(q) - 18 - 23 * BP) for i, q in enumerate(quests)]
    y_hover = y_hov[0]
    kf = [f"0%{{transform:translate({-BW - 20}px,{y_hov[0]}px)}}"]
    for i, (a, l) in enumerate(stops):
        x = xs[i] - BCX
        if i and rowof[i] != rowof[i - 1]:  # warp: exit right, re-enter left one row down
            pa_, pl_ = stops[i - 1][1], a
            mid = (pa_ + pl_) / 2
            kf.append(f"{mid:.2f}%{{transform:translate({W + 20}px,{y_hov[i - 1]}px)}}")
            kf.append(f"{mid + .01:.2f}%{{transform:translate({-BW - 20}px,{y_hov[i]}px)}}")
        kf.append(f"{a:.2f}%{{transform:translate({x}px,{y_hov[i]}px)}}")
        kf.append(f"{l:.2f}%{{transform:translate({x}px,{y_hov[i]}px)}}")
    kf.append(f"100%{{transform:translate({W + 20}px,{y_hov[-1]}px)}}")
    beam = ["0%{opacity:0}"]
    for a, l in stops:
        beam += [f"{a - .01:.2f}%{{opacity:0}}", f"{a + 1:.2f}%{{opacity:1}}",
                 f"{l - 1:.2f}%{{opacity:1}}", f"{l:.2f}%{{opacity:0}}"]
    beam.append("100%{opacity:0}")
    acts = []
    for i, (a, l) in enumerate(stops):
        acts.append(f"@keyframes act{i}{{0%,{a:.2f}%{{opacity:0}}{a + 1.5:.2f}%{{opacity:1}}"
                    f"{l:.2f}%{{opacity:.85}}{min(100, l + 3):.2f}%,100%{{opacity:0}}}}")

    css = f"""
<style>
.fly{{animation:fly {dur}s ease-in-out infinite}}
@keyframes fly{{{''.join(kf)}}}
.bob{{animation:bob 1.6s steps(2) infinite alternate}}
@keyframes bob{{to{{transform:translateY(4px)}}}}
.beam{{opacity:0;animation:beam {dur}s linear infinite}}
@keyframes beam{{{''.join(beam)}}}
{''.join(acts)}
.act{{opacity:0}}
.fa{{animation:fa .24s steps(1) infinite}} .fb{{animation:fb .24s steps(1) infinite}}
@keyframes fa{{50%{{opacity:0}}}} @keyframes fb{{0%{{opacity:0}}50%{{opacity:1}}}}
.ta{{animation:fa 1.2s steps(1) infinite}} .tb{{animation:fb 1.2s steps(1) infinite}}
.blink{{opacity:0;animation:blink 4.5s steps(1) infinite}}
@keyframes blink{{0%,92%{{opacity:0}}93%,96%{{opacity:1}}97%{{opacity:0}}}}
.isl{{animation:isl 3.2s steps(2) infinite alternate}}
@keyframes isl{{to{{transform:translateY(-4px)}}}}
.glow{{animation:glow 2.4s ease-in-out infinite alternate}}
@keyframes glow{{from{{opacity:.45}}to{{opacity:1}}}}
.tw{{animation:tw 3s steps(2) infinite}}
@keyframes tw{{50%{{opacity:.15}}}}
.aur{{animation:aur 50s linear infinite}}
@keyframes aur{{to{{transform:translateX(-{W}px)}}}}
.c1{{animation:aur 140s linear infinite}} .c2{{animation:aur 80s linear infinite}}
.route{{animation:route 1.2s linear infinite}}
@keyframes route{{to{{stroke-dashoffset:-24}}}}
.win{{animation:tw 2.2s steps(2) infinite}}
.exh{{animation:exh .6s steps(3) infinite}}
@keyframes exh{{to{{transform:translateX(-12px);opacity:0}}}}
.cur{{animation:fa 1s steps(1) infinite}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.act,.beam{{opacity:0}}}}
</style>"""
    parts.append(css)

    # sky
    c = Canvas()
    sky_bands(c, W, H)
    parts.append(c.svg())

    # stars
    s1, s2 = Canvas(), Canvas()
    for i in range(50 + 25 * nrows):
        x, y = rng.randrange(0, W, P), rng.randrange(0, H - 160, P)
        (s1 if i % 3 else s2).rect(x, y, P if rng.random() < .25 else 2, P if rng.random() < .25 else 2,
                                   "#ffffff@" + str(rng.choice((.5, .7, .9))))
    parts.append(s1.svg())
    parts.append(f'<g class="tw">{s2.svg()}</g>')

    # aurora ribbons (drawn over 2W so the scroll loops seamlessly)
    au = Canvas()
    for col, base, amp, per, thick, op in ((MINT, 70, 22, W / 2, 5, .10), (CYAN, 110, 16, W / 4, 3, .08)):
        for x in range(0, 2 * W, P):
            y = base + amp * math.sin(2 * math.pi * x / per)
            y = round(y / P) * P
            for j in range(thick):
                fade = op * (1 - abs(j - thick / 2) / thick)
                au.rect(x, y + j * P, P, P, f"{col}@{fade:.3f}")
    parts.append(f'<g class="aur">{au.svg()}</g>')

    # far clouds
    cf = Canvas()
    for k in range(2):
        for i in range(6):
            cloud(cf, k * W + i * 170 + rng.randrange(0, 60, P), H - 180 + rng.randrange(0, 40, P),
                  rng.choice((64, 88, 112)), "#2a2f6e", rng)
    parts.append(f'<g class="c1" opacity=".8">{cf.svg()}</g>')

    # contribution city
    weeks = (stats or {}).get("weeks") or []
    real = len(weeks) >= 10
    if not real:
        weeks = [max(0, int(8 + 7 * math.sin(i / 4) + rng.randrange(-4, 10))) for i in range(52)]
    weeks = weeks[-52:]
    mx = max(1, max(weeks))
    city, lit, blink_w = Canvas(), Canvas(), Canvas()
    bw = W / len(weeks)
    for i, v in enumerate(weeks):
        x0 = round(i * bw / P) * P
        wdt = max(P * 2, round((bw - 3) / P) * P)
        h = round((16 + 60 * (v / mx) ** .8) / P) * P
        y0 = H - h
        city.rect(x0, y0, wdt, h, "#0c1030")
        city.rect(x0, y0, wdt, P, "#232a63")
        if v == mx:
            city.rect(x0 + wdt // 2 - 2, y0 - 12, P, 12, "#9aa6d8")  # antenna on the peak week
            lit.rect(x0 + wdt // 2 - 2, y0 - 16, P, P, PINK)
        frac = .2 + .7 * (v / mx)
        for wy in range(y0 + 8, H - 8, 8):
            for wx in range(x0 + 4, x0 + wdt - 4, 8):
                if rng.random() < frac:
                    col = rng.choice((CYAN, CYAN, PINK, GOLD)) + "@.85"
                    (blink_w if rng.random() < .12 else lit).rect(wx, wy, P, P, col)
    parts.append(city.svg() + lit.svg() + f'<g class="win">{blink_w.svg()}</g>')

    # near clouds
    cn = Canvas()
    for k in range(2):
        for i in range(4):
            cloud(cn, k * W + i * 260 + rng.randrange(0, 80, P), H - 60 + rng.randrange(0, 30, P),
                  rng.choice((96, 128)), "#3b3f86", rng)
    parts.append(f'<g class="c2" opacity=".55">{cn.svg()}</g>')

    # route between islands
    pts = []
    for i in range(n - 1):
        x1, y1 = xs[i], tops[i] - 6
        x2, y2 = xs[i + 1], tops[i + 1] - 6
        if rowof[i] != rowof[i + 1]:
            pts.append(f"M{x1} {y1}Q{(x1 + W) / 2} {y1 - 40} {W} {y1 - 10}")
            pts.append(f"M0 {y2 - 10}Q{x2 / 2} {y2 - 40} {x2} {y2}")
            continue
        mxp, myp = (x1 + x2) / 2, min(y1, y2) - 40
        pts.append(f"M{x1} {y1}Q{mxp} {myp} {x2} {y2}")
    parts.append(f'<path class="route" d="{"".join(pts)}" fill="none" stroke="{CYAN}" stroke-opacity=".45" '
                 f'stroke-width="4" stroke-dasharray="4 8"/>')

    # islands
    for i, q in enumerate(quests):
        r2 = random.Random(i * 31 + 7)
        ic, glow = Canvas(), Canvas()
        island(ic, glow, xs[i], tops[i], iw, depth, r2)
        rows, pal = ICONS.get(q.get("icon"), ICONS["beacon"])
        ip = 4
        iwid = len(rows[0]) * ip
        ihei = len(rows) * ip
        icon = Canvas()
        icon.sprite(rows, pal, xs[i] - iwid // 2, tops[i] - ihei - 2, ip)
        # arrival ring
        ring = Canvas()
        rx0, ry0 = xs[i] - iwid // 2 - 12, tops[i] - ihei - 14
        rw, rh = iwid + 24, ihei + 16
        for bx_, by_, sx, sy in ((rx0, ry0, 1, 1), (rx0 + rw, ry0, -1, 1),
                                 (rx0, ry0 + rh, 1, -1), (rx0 + rw, ry0 + rh, -1, -1)):
            ring.rect(bx_ if sx > 0 else bx_ - 10, by_ if sy > 0 else by_ - 3, 10, 3, GOLD)
            ring.rect(bx_ if sx > 0 else bx_ - 3, by_ if sy > 0 else by_ - 10, 3, 10, GOLD)
        # labels
        lab = Canvas()
        ly = max(t for t, r_ in zip(tops, rowof) if r_ == rowof[i]) + depth + 26
        num = f"{i + 1:02d}"
        lab.text(num, xs[i] - text_width(num, 2) // 2, ly, 2, CYAN)
        lab.text(q["name"], xs[i] - text_width(q["name"], 2) // 2, ly + 22, 2, INK)
        lab.text(q["tech"], xs[i] - text_width(q["tech"], 2) // 2, ly + 42, 2, DIM)
        tag = q.get("tag") or ""
        tcol = {"WINNER": GOLD, "CO-OP": PINK, "HACKATHON": CYAN}.get(tag, MINT)
        if tag:
            tw_ = text_width(tag, 2)
            lab.rect(xs[i] - tw_ // 2 - 6, ly + 58, tw_ + 12, 22, tcol + "@.14")
            lab.text(tag, xs[i] - tw_ // 2, ly + 62, 2, tcol)
        extra = ""
        if tag == "NOW BUILDING":
            dot = Canvas()
            dot.rect(xs[i] - text_width(tag, 2) // 2 - 16, ly + 66, 6, 6, MINT)
            extra += f'<g class="cur">{dot.svg()}</g>'
        if q.get("icon") == "beacon":
            dots = Canvas()
            dots.rect(xs[i] + text_width(q["tech"], 2) // 2 + 4, ly + 54, 4, 2, DIM)
            extra += f'<g class="cur">{dots.svg()}</g>'
        delay = f"animation-delay:-{i * .7:.1f}s"
        icon_cls = "glow" if q.get("icon") in ("trophy", "star", "beacon", "butterfly") else ""
        body = (f'<g class="isl" style="{delay}">{ic.svg()}<g class="glow">{glow.svg()}</g>'
                f'<g class="{icon_cls}">{icon.svg()}</g>'
                f'<g class="act" style="animation:act{i} {dur}s linear infinite">{ring.svg()}</g></g>'
                f'{lab.svg()}{extra}')
        if q.get("repo"):
            body = f'<a href="{q["repo"]}">{body}</a>'
        parts.append(body)

    # blimp
    body, blink, ta, tb, pa, pb = blimp_parts()
    beam_svg = (f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{CYAN}" stop-opacity=".55"/>'
                f'<stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient></defs>'
                f'<path class="beam" d="M{19 * BP - 8} {23 * BP}h16l40 76h-96z" fill="url(#bg)"/>')
    exh = Canvas()
    exh.rect(9 * BP, 20 * BP, 4, 4, CYAN + "@.8")
    exh.rect(7 * BP, 21 * BP, 4, 4, CYAN + "@.5")
    rest_x = xs[0] - BCX
    parts.append(
        f'<g class="fly" transform="translate({rest_x},{y_hover})"><g class="bob">{beam_svg}{body.svg()}'
        f'<g class="blink">{blink.svg()}</g>'
        f'<g class="ta">{ta.svg()}</g><g class="tb">{tb.svg()}</g>'
        f'<g class="exh">{exh.svg()}</g><g class="fa">{pa.svg()}</g><g class="fb">{pb.svg()}</g></g></g>')

    # HUD chrome
    hud = Canvas()
    brackets(hud, W, H, CYAN + "@.7")
    hud.text("QUEST LOG", 24, 22, 2, CYAN)
    sub = "CITY = YOUR LAST 52 WEEKS OF CONTRIBUTIONS" if real else "SKY ARCHIPELAGO"
    hud.text(sub, W - 24 - text_width(sub, 2), 22, 2, DIM)
    cur = Canvas()
    cur.rect(24 + text_width("QUEST LOG", 2) + 6, 22, 8, 14, CYAN)
    parts.append(hud.svg() + f'<g class="cur">{cur.svg()}</g>')
    parts.append(scanlines(W, H, "q"))
    parts.append("</svg>")
    return "".join(parts)


# ── Quest log cards ─────────────────────────────────────────────────────────
TAG_COLORS = {"WINNER": GOLD, "CO-OP": PINK, "HACKATHON": CYAN}
CW, CH = 500, 176  # card size


def wrap(s, width):
    lines, cur = [], ""
    for word in s.upper().split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    return lines + [cur] if cur else lines


def stepped_panel(c, w, h, color, step=4):
    c.rect(2 * step, 0, w - 4 * step, h, color)
    c.rect(0, 2 * step, w, h - 4 * step, color)
    c.rect(step, step, w - 2 * step, h - 2 * step, color)


def quest_card(q, i):
    """One save-slot card per quest; its viewport shows the same island as the banner."""
    tag = q.get("tag") or ""
    tcol = TAG_COLORS.get(tag, MINT)
    num = f"{i + 1:02d}"
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" width="{CW}" height="{CH}" '
         f'role="img" aria-labelledby="t{num} d{num}" shape-rendering="crispEdges">',
         f'<title id="t{num}">Quest {num}: {q["name"].title()}</title>',
         f'<desc id="d{num}">{q.get("blurb", "")}</desc>',
         """<style>
.isl{animation:isl 3.2s steps(2) infinite alternate}@keyframes isl{to{transform:translateY(-4px)}}
.glow{animation:glow 2.4s ease-in-out infinite alternate}@keyframes glow{from{opacity:.45}to{opacity:1}}
.cur{animation:cur 1s steps(1) infinite}@keyframes cur{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style>"""]
    bg = Canvas()
    stepped_panel(bg, CW, CH, "#080b22")
    grid = Canvas()
    for x in range(8, CW, 24):
        grid.rect(x, 0, 1, CH, "#1a2150@.5")
    for y in range(8, CH, 24):
        grid.rect(0, y, CW, 1, "#1a2150@.5")
    p.append(bg.svg() + grid.svg())

    # viewport: a slice of the banner sky with this quest's island
    vx, vy, vw, vh = 16, 16, 136, CH - 32
    view = Canvas()
    band = vh / len(SKY)
    for k, col in enumerate(SKY):
        view.rect(vx, vy + round(k * band / P) * P, vw, round(band / P + 1) * P, col)
    rng = random.Random(i * 13 + 5)
    for _ in range(14):
        view.rect(vx + rng.randrange(0, vw - 4, P), vy + rng.randrange(0, vh - 60, P), 2, 2,
                  "#ffffff@" + str(rng.choice((.4, .7, .9))))
    p.append(f'<clipPath id="v{num}"><rect x="{vx}" y="{vy}" width="{vw}" height="{vh}"/></clipPath>'
             + view.svg())
    ic, glow = Canvas(), Canvas()
    cx, top = vx + vw // 2, vy + 84
    island(ic, glow, cx, top, 96, 44, random.Random(i * 31 + 7))
    rows, pal = ICONS.get(q.get("icon"), ICONS["beacon"])
    icon = Canvas()
    icon.sprite(rows, pal, cx - len(rows[0]) * 2, top - len(rows) * 4 - 2, 4)
    icon_cls = "glow" if q.get("icon") in ("trophy", "star", "beacon", "butterfly") else ""
    p.append(f'<g clip-path="url(#v{num})"><g class="isl" style="animation-delay:-{i * .7:.1f}s">'
             f'{ic.svg()}<g class="glow">{glow.svg()}</g><g class="{icon_cls}">{icon.svg()}</g></g></g>')
    fr = Canvas()
    for (x, y, w, h) in ((vx - 4, vy - 4, vw + 8, 4), (vx - 4, vy + vh, vw + 8, 4),
                         (vx - 4, vy - 4, 4, vh + 8), (vx + vw, vy - 4, 4, vh + 8)):
        fr.rect(x, y, w, h, "#232a63")
    brackets(fr, CW, CH, tcol + "@.8", inset=4, arm=16, t=3)
    p.append(fr.svg())

    # text column
    tx = vx + vw + 20
    t = Canvas()
    t.text(num, tx, 24, 2, CYAN)
    if tag:
        tw_ = text_width(tag, 2)
        t.rect(CW - 20 - tw_ - 12, 19, tw_ + 12, 22, tcol + "@.14")
        t.text(tag, CW - 20 - tw_ - 6, 23, 2, tcol)
    t.text(q["name"], tx, 50, 3, INK)
    t.text(q["tech"], tx, 82, 2, DIM)
    t.rect(tx, 102, CW - 20 - tx, 2, "#232a63")
    lines = wrap(q.get("blurb", ""), (CW - 20 - tx + 2) // 12)
    if len(lines) > 3:
        print(f"warning: blurb for {q['name']} needs {len(lines)} lines; only 3 fit", file=sys.stderr)
    for k, line in enumerate(lines[:3]):
        t.text(line, tx, 116 + k * 18, 2, "#c3cbff")
    p.append(t.svg())
    if tag == "NOW BUILDING":
        dot = Canvas()
        dot.rect(CW - 20 - text_width(tag, 2) - 24, 27, 6, 6, MINT)
        p.append(f'<g class="cur">{dot.svg()}</g>')
    p.append(scanlines(CW, CH, num))
    p.append("</svg>")
    return "".join(p)


def strip(title, sub, label):
    """A thin HUD bar that matches the banner, used above and below the cards."""
    w, h = 1000, 64
    c = Canvas()
    stepped_panel(c, w, h, "#080b22")
    brackets(c, w, h, CYAN + "@.7", inset=4, arm=18, t=3)
    c.text(title, 24, 22, 3, CYAN)
    c.text(sub, w - 24 - text_width(sub, 2), 26, 2, DIM)
    cur = Canvas()
    cur.rect(24 + text_width(title, 3) + 8, 22, 10, 21, CYAN)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{label}" shape-rendering="crispEdges">'
            '<style>.cur{animation:cur 1s steps(1) infinite}@keyframes cur{50%{opacity:0}}'
            '@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style>'
            f'{c.svg()}<g class="cur">{cur.svg()}</g>{scanlines(w, h, title[:2])}</svg>')


# ── HUD card ────────────────────────────────────────────────────────────────
CAT_AVATAR = [
    "..o..........o..",
    ".ooo........ooo.",
    ".opoo......oopo.",
    ".oppoooooooooppo",
    "oooooddooddooooo",
    "oooooooooooooooo",
    "oooooooooooooooo",
    "oooeeooooooeeooo",
    "oooeWooooooeWooo",
    "oooooooooooooooo",
    "wwoooooppoooooww",
    "oowwoooooooowwoo",
    "oooooodoodoooooo",
    ".oooooooooooooo.",
    "..oooooooooooo..",
    "....oooooooo....",
]


def hud(profile, stats):
    st = stats or {}
    ms = profile.get("manual_stats", {})
    contrib = st.get("total_contributions")
    level = int(math.sqrt(contrib / 2)) + 1 if contrib else None
    prog = (math.sqrt(contrib / 2) % 1) if contrib else .62
    HW, HH = 1000, 270
    tiles = [
        ("LIFETIME CONTRIBS", st.get("total_contributions"), CYAN),
        ("COMMITS", st.get("total_commits"), CYAN),
        ("COLLAB REPOS", st.get("repos_contributed_to"), CYAN),
        ("HACKATHON WINS", ms.get("hackathon_wins"), GOLD),
        ("HACKATHON ENTRIES", ms.get("hackathons"), GOLD),
        ("TEAM PROJECTS", ms.get("team_projects"), PINK),
    ]
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {HW} {HH}" width="{HW}" height="{HH}" '
             f'role="img" aria-labelledby="ht hd" shape-rendering="crispEdges">')
    p.append(f'<title id="ht">{profile["display_name"]} player card</title>')
    p.append('<desc id="hd">' + "; ".join(f"{t[0].title()}: {fmt(t[1])}" for t in tiles) + '</desc>')
    p.append(f"""<style>
.sweep{{animation:sweep 6s cubic-bezier(.6,0,.4,1) infinite}}
@keyframes sweep{{0%{{transform:translateX(-200px)}}60%,100%{{transform:translateX({HW + 200}px)}}}}
.gl1,.gl2{{opacity:0;animation:gl 5s steps(1) infinite}}
.gl2{{animation-delay:.08s}}
@keyframes gl{{0%,90%{{opacity:0;transform:none}}91%{{opacity:.9;transform:translateX(-4px)}}93%{{opacity:.9;transform:translateX(4px)}}95%,100%{{opacity:0}}}}
.xp{{animation:xp 2.4s cubic-bezier(.2,.8,.2,1) both}}
@keyframes xp{{from{{transform:scaleX(0)}}}}
.xp{{transform-box:fill-box;transform-origin:left}}
.blink{{opacity:0;animation:blink 4.5s steps(1) infinite}}
@keyframes blink{{0%,92%{{opacity:0}}93%,96%{{opacity:1}}97%{{opacity:0}}}}
.cur{{animation:cur 1s steps(1) infinite}}
@keyframes cur{{50%{{opacity:0}}}}
.pulse{{animation:pulse 2s ease-in-out infinite alternate}}
@keyframes pulse{{from{{opacity:.35}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.gl1,.gl2{{opacity:0}}}}
</style>""")
    bg = Canvas()
    # stepped-corner panel
    bg.rect(8, 0, HW - 16, HH, "#080b22")
    bg.rect(0, 8, HW, HH - 16, "#080b22")
    bg.rect(4, 4, HW - 8, HH - 8, "#080b22")
    grid = Canvas()
    for x in range(24, HW, 32):
        grid.rect(x, 0, 1, HH, "#1a2150@.6")
    for y in range(12, HH, 32):
        grid.rect(0, y, HW, 1, "#1a2150@.6")
    p.append(bg.svg() + grid.svg())
    p.append(f'<defs><linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>'
             f'<stop offset=".5" stop-color="{CYAN}" stop-opacity=".12"/><stop offset="1" stop-color="{CYAN}" '
             f'stop-opacity="0"/></linearGradient></defs>'
             f'<rect class="sweep" x="0" y="0" width="160" height="{HH}" fill="url(#sw)"/>')
    fr = Canvas()
    brackets(fr, HW, HH, CYAN, inset=6, arm=28)
    p.append(fr.svg())

    # avatar
    av = Canvas()
    ax, ay, ap = 36, 30, 9
    av.rect(ax - 8, ay - 8, 16 * ap + 16, 16 * ap + 16, "#11173d")
    av.sprite(CAT_AVATAR, {"o": "#ffa94d", "p": "#ff8fb1", "d": "#e0761f", "e": "#1a1033", "W": "#ffffff",
                           "w": "#fff1e0"}, ax, ay, ap)
    frame = Canvas()
    for (x, y, w, h) in ((ax - 8, ay - 8, 16 * ap + 16, 4), (ax - 8, ay + 16 * ap + 4, 16 * ap + 16, 4),
                         (ax - 8, ay - 8, 4, 16 * ap + 16), (ax + 16 * ap + 4, ay - 8, 4, 16 * ap + 16)):
        frame.rect(x, y, w, h, PINK)
    blink = Canvas()
    for ex in (3, 11):
        blink.rect(ax + ex * ap, ay + 7 * ap, 2 * ap, 2 * ap, "#ffa94d")
    p.append(av.svg() + f'<g class="pulse">{frame.svg()}</g><g class="blink">{blink.svg()}</g>')
    lo = Canvas()
    lx = ax - 8
    ly = ay + 16 * ap + 22
    for tag in profile.get("loadout", []):
        tw_ = text_width(tag, 2)
        lo.rect(lx, ly - 4, tw_ + 12, 22, MINT + "@.14")
        lo.text(tag, lx + 6, ly, 2, MINT)
        lx += tw_ + 18
    p.append(lo.svg())

    # name block
    nx = 228
    name = profile["display_name"]
    for cls, col in (("gl1", PINK), ("gl2", CYAN)):
        g = Canvas()
        g.text(name, nx, 34, 6, col)
        p.append(f'<g class="{cls}">{g.svg()}</g>')
    nm = Canvas()
    nm.text(name, nx, 34, 6, INK)
    nm.text("PLAYER 1", nx, 92, 2, PINK)
    nm.text(profile.get("role", ""), nx + text_width("PLAYER 1", 2) + 16, 92, 2, CYAN)
    p.append(nm.svg())
    # level + xp bar
    lv = Canvas()
    lvl = f"LV {level}" if level else "LV --"
    lv.text(lvl, nx, 124, 3, GOLD)
    bx = nx + text_width(lvl, 3) + 16
    bwid = 560 - bx
    lv.rect(bx, 126, bwid, 16, "#1a2150")
    p.append(lv.svg())
    fill = Canvas()
    segs = int(bwid * prog / 8)
    for k in range(segs):
        fill.rect(bx + 2 + k * 8, 128, 6, 12, GOLD if k < segs - 1 else "#fff3b0")
    p.append(f'<g class="xp">{fill.svg()}</g>')
    xpl = Canvas()
    label = "XP TO NEXT LEVEL" if level else "XP SYNCS DAILY"
    xpl.text(label, bx, 150, 2, DIM)
    p.append(xpl.svg())

    # achievements
    ac = Canvas()
    ac.text("ACHIEVEMENTS", nx, 178, 2, DIM)
    cx_, cy_ = nx, 202
    for a in profile.get("achievements", []):
        tw_ = text_width(a, 2)
        if cx_ + tw_ + 12 > 560:
            cx_, cy_ = nx, cy_ + 30
        ac.rect(cx_, cy_ - 5, tw_ + 14, 24, "#1a2150")
        ac.rect(cx_, cy_ - 5, 3, 24, GOLD)
        ac.text(a, cx_ + 9, cy_, 2, INK)
        cx_ += tw_ + 24
    p.append(ac.svg())

    # stat tiles
    tx0, ty0, tw, th, gap = 590, 26, 124, 104, 10
    for k, (lab, val, col) in enumerate(tiles):
        r, cidx = divmod(k, 3)
        x = tx0 + cidx * (tw + gap)
        y = ty0 + r * (th + gap)
        t = Canvas()
        t.rect(x, y, tw, th, "#0f1438")
        t.rect(x, y, tw, 3, col + "@.9")
        t.rect(x, y + th - 3, 12, 3, col + "@.6")
        words = lab.split(" ")
        t.text(words[0], x + 10, y + 14, 2, DIM)
        if len(words) > 1:
            t.text(" ".join(words[1:]), x + 10, y + 32, 2, DIM)
        v = fmt(val)
        vp = 4 if text_width(v, 4) <= tw - 20 else 3
        t.text(v, x + 10, y + th - 14 - 7 * vp, vp, col)
        p.append(t.svg())
    p.append(scanlines(HW, HH, "h"))
    p.append("</svg>")
    return "".join(p)


def main():
    prof_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "profile.json")
    stats_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "data", "stats.json")
    profile = json.load(open(prof_path))
    stats = json.load(open(stats_path)) if os.path.exists(stats_path) else None
    out = os.path.join(ROOT, "assets")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "hud.svg"), "w") as f:
        f.write(hud(profile, stats))
    with open(os.path.join(out, "quest-map.svg"), "w") as f:
        f.write(quest_map(profile, stats))
    qdir = os.path.join(out, "quests")
    os.makedirs(qdir, exist_ok=True)
    for name in os.listdir(qdir):  # drop cards for quests that were removed
        if name.endswith(".svg"):
            os.remove(os.path.join(qdir, name))
    with open(os.path.join(qdir, "header.svg"), "w") as f:
        f.write(strip("QUEST DETAILS", "SAME ORDER AS THE ISLANDS. SELECT A CARD TO OPEN IT",
                      "Quest details: select a card to open its repo"))
    with open(os.path.join(qdir, "footer.svg"), "w") as f:
        f.write(strip("SYNC OK", "SKYLINE = LAST 52 WEEKS. TALLER = BUSIER. UPDATES DAILY",
                      "The skyline shows the last 52 weeks of contributions and updates daily"))
    for i, q in enumerate(profile["quests"]):
        with open(os.path.join(qdir, f"{i + 1:02d}.svg"), "w") as f:
            f.write(quest_card(q, i))
    sync_readme(profile["quests"])
    print(f"wrote assets/hud.svg, assets/quest-map.svg, assets/quests/ ({len(profile['quests'])} cards)")


def sync_readme(quests):
    """Rewrite the card grid between the quest markers in README.md, two cards per row."""
    path = os.path.join(ROOT, "README.md")
    start, end = "<!-- quests:start -->", "<!-- quests:end -->"
    if not os.path.exists(path):
        return
    text = open(path).read()
    if start not in text or end not in text:
        return
    cells = []
    for i, q in enumerate(quests):
        n = f"{i + 1:02d}"
        alt = f'Quest {n}, {q["name"]}: {q.get("blurb", q["tech"])}'.replace('"', "'")
        img = f'<img src="assets/quests/{n}.svg" width="49%" alt="{alt}">'
        cells.append(f'<a href="{q["repo"]}">{img}</a>' if q.get("repo") else img)
    rows = [" ".join(cells[k:k + 2]) for k in range(0, len(cells), 2)]
    block = (f'{start}\n<img src="assets/quests/header.svg" width="100%" alt="Quest details: select a card to open its repo">\n\n'
             + "\n\n".join(rows)
             + '\n\n<img src="assets/quests/footer.svg" width="100%" alt="The skyline shows the last 52 weeks '
             + f'of contributions and updates daily">\n{end}')
    head, rest = text.split(start, 1)
    with open(path, "w") as f:
        f.write(head + block + rest.split(end, 1)[1])


if __name__ == "__main__":
    main()
