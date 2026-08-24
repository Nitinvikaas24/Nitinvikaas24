import math
from pixelfont import pixel_text_svg, measure_pixel_text
import xml.sax.saxutils as saxutils

def esc(s):
    return saxutils.escape(s)

# ---- Palette: Swiss International Style + 1-bit pixel dither -------------
PAPER   = "#F4F1E9"   # warm off-white "paper"
INK     = "#0E0E10"   # near-black ink
RED     = "#E6301E"   # swiss poster red
YELLOW  = "#FFC53D"   # sparing accent
GREY    = "#B9B4A6"   # rule/grid grey on paper
PAPER_D = "#EDE9DD"   # slightly darker paper (panel fill)

FONT_STACK = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO_STACK = "Consolas, Menlo, Monaco, monospace"


def svg_open(w, h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" role="img">')


def rect(x, y, w, h, fill, **extra):
    attrs = " ".join(f'{k.replace("_","-")}="{v}"' for k, v in extra.items())
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" {attrs}/>'


def line(x1, y1, x2, y2, stroke, width=1, **extra):
    attrs = " ".join(f'{k.replace("_","-")}="{v}"' for k, v in extra.items())
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}" {attrs}/>'


def text(x, y, s, size, fill, family=FONT_STACK, weight=400, anchor="start", spacing=None, style=None):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    st = f' font-style="{style}"' if style else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}{st}>{esc(s)}</text>')


def halftone_panel(x, y, w, h, rows, cols, base_r, colA, colB, bg, invert_grad=False):
    """A bordered panel filled with a dither/halftone dot grid whose radius
    ramps across the columns -> reads as a printed gradient texture."""
    out = [rect(x, y, w, h, bg), f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{INK}" stroke-width="2"/>']
    cw, ch = w / cols, h / rows
    for r in range(rows):
        for c in range(cols):
            t = c / max(cols - 1, 1)
            if invert_grad:
                t = 1 - t
            rad = base_r * (0.18 + 0.82 * t)
            cx = x + cw * (c + 0.5)
            cy = y + ch * (r + 0.5)
            col = RED if (r + c) % 5 == 0 else colA if (r + c) % 2 == 0 else colB
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.2f}" fill="{col}"/>')
    return "\n".join(out)


def ruler(x, y, w, step, tick_h, color, big_every=5, labels=False, label_size=9):
    out = [line(x, y, x + w, y, color, 2)]
    n = int(w // step)
    for i in range(n + 1):
        px = x + i * step
        big = (i % big_every == 0)
        th = tick_h * (1.8 if big else 1)
        out.append(line(px, y, px, y + th, color, 2 if big else 1))
        if labels and big:
            out.append(text(px, y + th + 12, f"{i*step:02d}", 9, color, family=MONO_STACK))
    return "\n".join(out)


def pixel_wave(x, y, w, n, amp, base, color):
    out = []
    bar_w = w / n
    for i in range(n):
        t = i / (n - 1)
        h = base + amp * (0.5 + 0.5 * math.sin(t * math.pi * 3.1))
        h = round(h / 4) * 4  # quantize -> chunky pixel steps
        out.append(rect(x + i * bar_w, y - h, bar_w - 2, h, color))
    return "\n".join(out)


def wrap(w, h, body, bg=None):
    bgrect = rect(0, 0, w, h, bg) if bg else ""
    return svg_open(w, h) + bgrect + body + "</svg>"


# ============================= 1. BANNER ===================================
def build_banner():
    W, H = 1200, 340
    body = []
    body.append(rect(0, 0, W, H, PAPER))

    # framing bars (Swiss ruled frame)
    body.append(rect(0, 0, W, 8, INK))
    body.append(rect(0, H - 8, W, 8, INK))

    # top-left index tab
    body.append(rect(56, 34, 26, 26, RED))
    ptxt, pw, ph = pixel_text_svg("N24", 92, 40, 4, INK)
    body.append(ptxt)
    body.append(text(56, 100, "GITHUB PROFILE — SPECIAL REPO README", 12, INK,
                      family=MONO_STACK, spacing="1.5px"))

    # big pixel headline, two lines, asymmetric left column
    scale = 9
    row_h = 7 * scale  # 63
    line1_y = 116
    line2_y = line1_y + row_h + 8  # 187
    line1, w1, h1 = pixel_text_svg("NITIN", 58, line1_y, scale, RED, id_prefix="l1")
    line2, w2, h2 = pixel_text_svg("VIKAAS", 58, line2_y, scale, INK, id_prefix="l2")
    body.append(line1)
    body.append(line2)

    # halftone texture panel, right column
    panel_x, panel_y, panel_w, panel_h = 800, 40, 344, 216
    body.append(halftone_panel(panel_x, panel_y, panel_w, panel_h, rows=11, cols=14,
                                base_r=6.4, colA=INK, colB=PAPER_D, bg=PAPER))
    # corner bracket marks on the panel (Swiss crop-mark motif)
    for (cx, cy, dx, dy) in [(panel_x, panel_y, 1, 1), (panel_x + panel_w, panel_y, -1, 1),
                              (panel_x, panel_y + panel_h, 1, -1), (panel_x + panel_w, panel_y + panel_h, -1, -1)]:
        body.append(line(cx, cy, cx + dx * 16, cy, INK, 3))
        body.append(line(cx, cy, cx, cy + dy * 16, INK, 3))

    # baseline rule + caption row
    rule_y = line2_y + row_h + 20  # sits safely below the pixel headline
    body.append(line(56, rule_y, W - 56, rule_y, INK, 2))
    body.append(text(56, rule_y + 22, "CLOUD-NATIVE + FULL-STACK ENGINEER — K8S / AWS / AI", 13, INK, weight=700))
    body.append(text(W - 56, rule_y + 22, "GITHUB.COM/NITINVIKAAS24", 13, INK, anchor="end", family=MONO_STACK))

    # ruler ticks along the very bottom, inside the frame
    body.append(ruler(56, rule_y + 40, W - 112, 24, 4, GREY))

    return wrap(W, H, "\n".join(body))


# ============================= 2. DIVIDER ===================================
def build_divider():
    W, H = 1200, 26
    body = []
    body.append(line(0, 4, W, 4, INK, 2))
    body.append(line(0, H - 4, W, H - 4, INK, 1))
    # barcode-like pixel strip
    import random
    rnd = random.Random(24)
    x = 0
    while x < W:
        bw = rnd.choice([4, 4, 8, 12, 4, 20, 4, 4, 8])
        if rnd.random() < 0.14:
            col = RED
        elif rnd.random() < 0.5:
            col = INK
        else:
            col = "none"
        if col != "none":
            body.append(rect(x, 9, bw, 8, col))
        x += bw
    return wrap(W, H, "\n".join(body))


# ============================= 3. FOOTER ===================================
def build_footer():
    W, H = 1200, 230
    body = []
    body.append(rect(0, 0, W, H, INK))
    body.append(rect(0, 0, W, 8, RED))

    t, w, h = pixel_text_svg("THANKS FOR STOPPING BY", 58, 46, 6, PAPER, id_prefix="f1")
    body.append(t)
    body.append(text(58, 132, "BUILT WITH PIXELS AND A SWISS GRID — NO FRAMEWORKS, JUST RECTANGLES", 12, GREY,
                      family=MONO_STACK))

    body.append(line(58, 150, W - 58, 150, "#3A3A3E", 1))
    body.append(pixel_wave(58, 205, W - 116, 40, 26, 10, RED))

    body.append(text(58, 222, "N24", 10, GREY, family=MONO_STACK))
    body.append(text(W - 58, 222, "EOF", 10, GREY, family=MONO_STACK, anchor="end"))

    return wrap(W, H, "\n".join(body))


# ============================= 4. SECTION TAGS ==============================
def build_tag(index, label, fname):
    label_w, label_h = measure_pixel_text(label, 5)
    idx_str = f"{index:02d}"
    idx_scale = 4
    idx_w_text, idx_h_text = measure_pixel_text(idx_str, idx_scale)
    idx_pad = 10
    idx_w = int(idx_w_text + idx_pad * 2)

    pad_x, pad_y = 20, 16
    W = int(idx_w + label_w + pad_x * 2)
    H = int(max(label_h, idx_h_text) + pad_y * 2)

    body = []
    body.append(rect(0, 0, W, H, INK))
    body.append(rect(0, 0, idx_w, H, RED))
    idx_txt, _, _ = pixel_text_svg(idx_str, idx_pad, (H - idx_h_text) / 2, idx_scale, INK, id_prefix="idx")
    body.append(idx_txt)
    label_svg, _, _ = pixel_text_svg(label, idx_w + pad_x, (H - label_h) / 2, 5, PAPER, id_prefix="lbl")
    body.append(label_svg)
    svg = wrap(W, H, "\n".join(body))
    with open(f"assets/{fname}", "w") as f:
        f.write(svg)
    print(fname, W, H)


if __name__ == "__main__":
    import os
    os.makedirs("assets", exist_ok=True)
    with open("assets/banner.svg", "w") as f:
        f.write(build_banner())
    with open("assets/divider.svg", "w") as f:
        f.write(build_divider())
    with open("assets/footer.svg", "w") as f:
        f.write(build_footer())
    print("banner.svg, divider.svg, footer.svg written")

    build_tag(1, "ABOUT", "tag-about.svg")
    build_tag(2, "EXPERIENCE", "tag-experience.svg")
    build_tag(3, "STACK", "tag-stack.svg")
    build_tag(4, "PROJECTS", "tag-projects.svg")
    build_tag(5, "PIPELINE", "tag-pipeline.svg")
    build_tag(6, "STATS", "tag-stats.svg")
    build_tag(7, "CONNECT", "tag-connect.svg")
