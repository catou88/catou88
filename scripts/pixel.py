"""Tiny pixel-art toolkit: bitmap font, sprites and run-merged SVG paths.

Everything is drawn as rectangles so the art stays crisp and needs no web
fonts (GitHub strips external fonts and scripts from README SVGs).
"""
from collections import defaultdict

FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    " ": "00000 00000 00000 00000 00000 00000 00000",
    ".": "00000 00000 00000 00000 00000 01100 01100",
    ":": "00000 01100 01100 00000 01100 01100 00000",
    "-": "00000 00000 00000 11111 00000 00000 00000",
    "/": "00001 00010 00010 00100 01000 01000 10000",
    "+": "00000 00100 00100 11111 00100 00100 00000",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    "?": "01110 10001 00001 00010 00100 00000 00100",
    "#": "01010 01010 11111 01010 11111 01010 01010",
    "&": "01100 10010 10100 01000 10101 10010 01101",
    ">": "01000 00100 00010 00001 00010 00100 01000",
    "=": "00000 00000 11111 00000 11111 00000 00000",
    "'": "00100 00100 01000 00000 00000 00000 00000",
    "%": "11001 11010 00010 00100 01000 01011 10011",
}


class Canvas:
    """Collects rectangles per fill colour and emits one merged <path> each."""

    def __init__(self):
        self.rects = defaultdict(list)  # color -> [(x, y, w, h)]

    def rect(self, x, y, w, h, color):
        if w > 0 and h > 0:
            self.rects[color].append((x, y, w, h))

    def cells(self, cells, p, ox, oy, color):
        """cells: iterable of (cx, cy) grid coords; merged into horizontal runs."""
        rows = defaultdict(list)
        for cx, cy in cells:
            rows[cy].append(cx)
        for cy, xs in rows.items():
            xs = sorted(set(xs))
            start = prev = xs[0]
            for x in xs[1:] + [None]:
                if x is not None and x == prev + 1:
                    prev = x
                    continue
                self.rect(ox + start * p, oy + cy * p, (prev - start + 1) * p, p, color)
                if x is not None:
                    start = prev = x

    def sprite(self, rows, palette, ox, oy, p):
        by_color = defaultdict(list)
        for cy, row in enumerate(rows):
            for cx, ch in enumerate(row):
                if ch in palette and palette[ch]:
                    by_color[palette[ch]].append((cx, cy))
        for color, cells in by_color.items():
            self.cells(cells, p, ox, oy, color)

    def text(self, s, ox, oy, p, color, spacing=1):
        cells = []
        x = 0
        for ch in s.upper():
            glyph = FONT.get(ch, FONT["?"]).split()
            for cy, row in enumerate(glyph):
                for cx, bit in enumerate(row):
                    if bit == "1":
                        cells.append((x + cx, cy))
            x += 5 + spacing
        if cells:
            self.cells(cells, p, ox, oy, color)

    def svg(self, extra_attrs=""):
        out = []
        for color, rects in self.rects.items():
            d = "".join(f"M{x:g} {y:g}h{w:g}v{h:g}h{-w:g}z" for x, y, w, h in rects)
            fill, _, op = color.partition("@")
            o = f' fill-opacity="{op}"' if op else ""
            out.append(f'<path fill="{fill}"{o} d="{d}"{extra_attrs}/>')
        return "".join(out)


def text_width(s, p, spacing=1):
    return (len(s) * (5 + spacing) - spacing) * p if s else 0


def draw(fn):
    """Run fn(canvas) and return the SVG markup."""
    c = Canvas()
    fn(c)
    return c.svg()


def text_svg(s, x, y, p, color, spacing=1):
    c = Canvas()
    c.text(s, x, y, p, color, spacing)
    return c.svg()
