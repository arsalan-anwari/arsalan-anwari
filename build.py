#!/usr/bin/env python3
"""
Generates the animated daylight "old Japanese village" SVG assets + README.md.

Edit the DATA section, then run:  python3 build.py
Outputs:  README.md  and  assets/*.svg
Pure SVG + CSS/SMIL (no JS, no external fonts) so it animates inside GitHub's <img> sandbox.
"""
import json
import math
import os
import random
import urllib.request
from html import escape
from pathlib import Path
from urllib.parse import quote

# ───────────────────────────── DATA ─────────────────────────────
USER = "arsalan-anwari"
NAME = "ARSALAN ANWARI"
NAME_JP = "アルサラン・アンワリ"
ROLE = "AI Performance Engineer  ·  ZAL Analytics"
TAGLINES = [  # typed out one after another in the header
    "> squeezing models onto silicon, GB200 racks to embedded boards",
    "> Rust · C · C++ · CUDA · HIP · Vulkan · Python",
    "> low-bit inference · kernels · profiling · portability",
    "> knowledge graphs · entity resolution · RAG · MCP · agents",
]

SOCIALS = [  # (label, logo, colour, url)
    ("LinkedIn", "linkedin", "0A66C2", "https://www.linkedin.com/in/arsalan-anwari/"),
    ("Email", "gmail", "D14836", "mailto:arsalan@anwari.nl"),
]
ORGS = [  # (label, url)
    ("ZAL-Analytics", "https://github.com/ZAL-Analytics"),
    ("Compressor Systems Holland", "https://github.com/Compressor-Systems-Holland-B-V"),
]

SKILLS = [  # (kanji, title, [(label, simple-icons logo or "", hex colour)])
    ("言語", "Languages", [
        ("Rust", "rust", "CE422B"), ("C", "c", "A8B9CC"), ("C++", "cplusplus", "00599C"),
        ("Python", "python", "3776AB"), ("CUDA", "nvidia", "76B900"), ("HIP / ROCm", "amd", "ED1C24"),
        ("GLSL / SPIR-V", "vulkan", "A41E22"), ("x86 Assembly", "", "0071C5"), ("ARM Assembly", "arm", "0091BD"),
        ("PTX / SASS", "nvidia", "76B900"), ("AMDGPU ISA (GCN / RDNA)", "amd", "ED1C24")]),
    ("推論", "GPU · Inference", [
        ("vLLM", "", "30A2FF"), ("NVIDIA Triton", "nvidia", "76B900"), ("SGLang", "", "6D4C41"),
        ("TensorRT", "nvidia", "76B900"), ("TensorRT-LLM", "nvidia", "76B900"), ("Vulkan Compute", "vulkan", "A41E22"),
        ("ONNX Runtime", "onnx", "005CED"), ("llama.cpp", "", "444444"), ("Quantization", "", "B8860B"),
        ("Kernel Tuning", "", "C0392B"), ("Profiling", "", "8E44AD"), ("Embedded / Edge", "", "2E7D6B"),
        ("OpenCV", "opencv", "5C3EE8"), ("OpenGL", "opengl", "5586A4")]),
    ("知識", "AI · Knowledge", [
        ("LoRA", "", "7C3AED"), ("RAG", "", "C0392B"), ("MCP", "modelcontextprotocol", "222222"),
        ("AI Agents", "", "7C3AED"), ("Knowledge Graphs", "", "2E7D6B"), ("Entity Resolution", "", "B8860B"),
        ("AI Governance", "", "37474F"), ("PII Protection", "", "6D4C41"), ("AI Security", "", "C0392B"),
        ("Guardrails / Evals", "", "8E44AD")]),
    ("基盤", "Infra · Tools", [
        ("Linux", "linux", "FCC624"), ("Kubernetes", "kubernetes", "326CE5"), ("llm-d", "", "EE0000"),
        ("Docker", "docker", "2496ED"), ("containerd", "containerd", "575757"), ("Helm", "helm", "0F1689"),
        ("Git", "git", "F05032"), ("CI/CD", "githubactions", "2088FF"), ("GitLab CI", "gitlab", "FC6D26")]),
]

EXTRA_DOWNLOADS = 0  # downloads from sources not tracked automatically (PyPI, Docker, ...)
STATS_FALLBACK = {"stars": 141, "repos": 50, "downloads": 25246, "crates": 54, "followers": 8}  # used if the APIs are unreachable

# oldest → newest (current employer last)
JOURNEY = [("NXP", "壱"), ("Lucidy", "弐"), ("AIM Sport", "参"), ("Nscale", "肆"), ("Tether", "伍"), ("ZAL Analytics", "今")]

# palette (daylight)
INK, INK2 = "#22303c", "#55606b"
VERMILION, GOLD, SAKURA, WASHI = "#c0392b", "#b8860b", "#f6c1cc", "#fbf6ec"
ROOF, ROOF_HI, WALL, WOOD, WOOD_DK = "#3b434e", "#5a6472", "#f3ece0", "#7a5132", "#4e3320"

SERIF = "'Noto Serif JP','Noto Serif CJK JP','Hiragino Mincho ProN','Yu Mincho','Source Han Serif',Georgia,serif"
MONO = "'JetBrains Mono','SF Mono','Cascadia Code',Consolas,'Liberation Mono',monospace"

OUT = Path(__file__).parent
ASSETS = OUT / "assets"
ASSETS.mkdir(exist_ok=True)
rnd = random.Random(11)
REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def svg(w, h, body, style="", title="", defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(title)}"><title>{escape(title)}</title>'
            f'<style>{style}{REDUCED}</style><defs>{defs}</defs>{body}</svg>')


def lg(id_, stops, x2=0, y2=1):
    s = "".join(f'<stop offset="{st[0]}" stop-color="{st[1]}" stop-opacity="{st[2] if len(st) > 2 else 1}"/>' for st in stops)
    return f'<linearGradient id="{id_}" x1="0" y1="0" x2="{x2}" y2="{y2}">{s}</linearGradient>'


# ─────────────────────────── scenery ────────────────────────────
def ridge(x0, x1, base, top, amp, seed, step=6):
    """Mountain silhouette from summed sines: closed path down to `base`."""
    r = random.Random(seed)
    ph = [r.uniform(0, 6.28) for _ in range(4)]
    pts = []
    for x in range(int(x0), int(x1) + step, step):
        y = top + amp * (0.5 * math.sin(x / 140 + ph[0]) + 0.3 * math.sin(x / 57 + ph[1])
                         + 0.15 * math.sin(x / 23 + ph[2]) + 0.05 * math.sin(x / 9 + ph[3]))
        pts.append(f"{x},{y:.1f}")
    return f'M{x0},{base} L' + " L".join(pts) + f' L{x1},{base} Z'


def cloud(x, y, s, op=0.95):
    puffs = [(0, 0, 38), (34, -14, 30), (66, -2, 34), (-30, 6, 26), (98, 8, 24), (18, 14, 30), (56, 16, 28)]
    c = "".join(f'<ellipse cx="{x + dx*s:.0f}" cy="{y + dy*s:.0f}" rx="{r*s*1.25:.0f}" ry="{r*s*.8:.0f}"/>' for dx, dy, r in puffs)
    shade = f'<ellipse cx="{x + 34*s:.0f}" cy="{y + 22*s:.0f}" rx="{90*s:.0f}" ry="{10*s:.0f}" fill="#dbe7f1"/>'
    return f'<g fill="#fff" opacity="{op}">{shade}{c}</g>'


def cedar(x, base, h, c="#3e5f3f", hi="#557a4f"):
    w = h * 0.42
    tiers = []
    for i in range(4):
        ty = base - h + i * h * 0.2
        tw = w * (0.35 + i * 0.22)
        tiers.append(f'<path d="M{x},{ty:.1f} L{x + tw/2:.1f},{ty + h*0.32:.1f} Q{x},{ty + h*0.27:.1f} {x - tw/2:.1f},{ty + h*0.32:.1f} Z" fill="{c}"/>')
        tiers.append(f'<path d="M{x},{ty:.1f} L{x - tw/2:.1f},{ty + h*0.32:.1f} Q{x - tw*.15:.1f},{ty + h*0.3:.1f} {x},{ty + h*0.22:.1f} Z" fill="{hi}" opacity=".6"/>')
    return f'<rect x="{x - 1.5}" y="{base - h*0.2:.1f}" width="3" height="{h*0.2:.1f}" fill="{WOOD_DK}"/>' + "".join(tiers)


def pine(x, base, s=1.0):
    """Japanese black pine: crooked trunk with flat cloud-like foliage pads."""
    t = (f'<path d="M{x},{base} C{x + 6*s},{base - 30*s} {x - 14*s},{base - 50*s} {x - 4*s},{base - 78*s} '
         f'C{x + 4*s},{base - 92*s} {x + 18*s},{base - 96*s} {x + 26*s},{base - 104*s}" stroke="#5b4636" '
         f'stroke-width="{6*s:.1f}" fill="none" stroke-linecap="round"/>')
    pads = [(-22, -60, 26), (-4, -84, 30), (26, -104, 24), (12, -70, 18), (-34, -82, 16)]
    p = ""
    for dx, dy, r in pads:
        p += (f'<ellipse cx="{x + dx*s:.1f}" cy="{base + dy*s:.1f}" rx="{r*s:.1f}" ry="{r*s*.42:.1f}" fill="#2f4a33"/>'
              f'<ellipse cx="{x + dx*s - 3*s:.1f}" cy="{base + dy*s - 3*s:.1f}" rx="{r*s*.75:.1f}" ry="{r*s*.25:.1f}" fill="#4a6d45"/>')
    return t + p


PETAL = "M0,-5 C3,-6 6,-3 5,1 C4,5 1,6 0,7 C-1,6 -4,5 -5,1 C-6,-3 -3,-6 -1,-5 L0,-3 Z"


def petals(n, w, h, drift=-220, dur=(10, 18)):
    out = []
    for _ in range(n):
        x = rnd.uniform(0, w + 180)
        d = rnd.uniform(*dur)
        sc = rnd.uniform(0.6, 1.2)
        c = rnd.choice(["#f6c1cc", "#f3a9bb", "#fbd9e1"])
        out.append(f'<g transform="translate({x:.0f},0) scale({sc:.2f})"><path class="petal" d="{PETAL}" fill="{c}" '
                   f'style="animation-duration:{d:.1f}s;animation-delay:-{rnd.uniform(0, d):.1f}s"/></g>')
    css = (".petal{opacity:.9;transform-box:fill-box;transform-origin:center;animation:fall linear infinite}"
           f"@keyframes fall{{0%{{transform:translate(0,-20px) rotate(0)}}30%{{transform:translate({drift*.25:.0f}px,{h*.3:.0f}px) rotate(160deg)}}"
           f"60%{{transform:translate({drift*.6:.0f}px,{h*.62:.0f}px) rotate(300deg)}}100%{{transform:translate({drift}px,{h*1.25:.0f}px) rotate(560deg)}}}}")
    return "".join(out), css


def birds(n, w):
    o = []
    for i in range(n):
        y = rnd.uniform(40, 150)
        d = rnd.uniform(26, 40)
        flock = "".join(f'<path class="wing" style="animation-delay:-{rnd.uniform(0,1):.2f}s" d="M{dx},{dy} q5,-5 9,0 q4,-5 9,0" '
                        f'stroke="#33404c" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
                        for dx, dy in [(0, 0), (16, 8), (-14, 10)][: rnd.randint(1, 3)])
        o.append(f'<g class="flock" style="animation-duration:{d:.0f}s;animation-delay:-{rnd.uniform(0, d):.0f}s">'
                 f'<g transform="translate(0,{y:.0f})">{flock}</g></g>')
    css = (f".flock{{animation:fly linear infinite}}@keyframes fly{{from{{transform:translate(-60px,0)}}to{{transform:translate({w + 60}px,-40px)}}}}"
           ".wing{transform-box:fill-box;transform-origin:center;animation:flap .7s ease-in-out infinite}"
           "@keyframes flap{0%,100%{transform:scaleY(1)}50%{transform:scaleY(-.5)}}")
    return "".join(o), css


SCENE_CSS = (".cloud{animation:drift linear infinite}@keyframes drift{from{transform:translateX(-360px)}to{transform:translateX(1560px)}}"
             ".mist{animation:mist 22s ease-in-out infinite alternate}@keyframes mist{from{transform:translateX(-40px)}to{transform:translateX(40px)}}"
             ".noren{transform-box:fill-box;transform-origin:50% 0;animation:noren 3.2s ease-in-out infinite}"
             "@keyframes noren{0%,100%{transform:skewX(-5deg)}50%{transform:skewX(5deg)}}"
             ".lant{transform-box:fill-box;transform-origin:50% 0;animation:sway 3.6s ease-in-out infinite}"
             "@keyframes sway{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(5deg)}}"
             ".tree{animation:tree 7s ease-in-out infinite}@keyframes tree{0%,100%{transform:rotate(-.6deg)}50%{transform:rotate(.6deg)}}"
             ".sun{animation:sun 6s ease-in-out infinite}@keyframes sun{0%,100%{opacity:.75}50%{opacity:1}}")


def sky_defs(h):
    return (lg("sky", [(0, "#6fb2df"), (.5, "#b9dcf1"), (.85, "#f3ecdc"), (1, "#fbf1de")])
            + '<radialGradient id="sun"><stop offset="0" stop-color="#fffbe8"/><stop offset=".25" stop-color="#fff2c2" stop-opacity=".9"/>'
              '<stop offset="1" stop-color="#ffe9a8" stop-opacity="0"/></radialGradient>'
            + lg("far", [(0, "#9fb6cd"), (1, "#d2dfe9")]) + lg("mid", [(0, "#7d9cab"), (1, "#b7cbd3")])
            + lg("hill", [(0, "#5e8656"), (1, "#86a874")]) + lg("hill2", [(0, "#6f9461"), (1, "#97b583")])
            + lg("fuji", [(0, "#6a83a4"), (1, "#a9bdd2")]) + lg("haze", [(0, "#fff", 0), (1, "#fff", .75)])
            + lg("street", [(0, "#e6d6b6"), (1, "#cdb68c")]))


# ───────────────────────── isometric kit ─────────────────────────
C30 = math.cos(math.pi / 6)
ISO = {"ox": 0.0, "oy": 0.0, "k": 1.0}


def P(x, y, z=0.0):
    k = ISO["k"]
    return ISO["ox"] + (x - y) * C30 * k, ISO["oy"] + (x + y) * 0.5 * k - z * k


def pts(ps):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in ps)


def poly(ps, fill, extra=""):
    return f'<polygon points="{pts(ps)}" fill="{fill}" {extra}/>'


def line3(a, b, stroke, w=1.0, extra=""):
    (x1, y1), (x2, y2) = P(*a), P(*b)
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{w}" {extra}/>'


def shade(c, f):
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{max(0, min(255, int(v * f))):02x}" for v in (r, g, b))


def box(x0, y0, z0, x1, y1, z1, col, top=None):
    """Visible faces: top, front-left (plane y=y1, shaded), front-right (plane x=x1, sunlit)."""
    return (poly([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], shade(col, .78))
            + poly([P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)], col)
            + poly([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], top or shade(col, 1.1)))


def fy(y, u0, u1, z0, z1, fill, extra=""):  # quad on a front-left face
    return poly([P(u0, y, z0), P(u1, y, z0), P(u1, y, z1), P(u0, y, z1)], fill, extra)


def fx(x, u0, u1, z0, z1, fill, extra=""):  # quad on a front-right face
    return poly([P(x, u0, z0), P(x, u1, z0), P(x, u1, z1), P(x, u0, z1)], fill, extra)


def hull(ps):
    ps = sorted(set(ps))
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(p)
        return h[:-1]
    return half(ps) + half(ps[::-1])


def shadow(x0, y0, x1, y1, h, op=.2):
    """Sun is upper-right, so shadows fall toward the viewer's lower-left (+y)."""
    dx, dy = -0.15 * h, 0.6 * h
    c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return poly(hull([P(x, y) for x, y in c] + [P(x + dx, y + dy) for x, y in c]), "#24361f", f'opacity="{op}"')


def iso_text(ch, x, y, z, size, fill, plane="y", vertical=True):
    sx, sy = P(x, y, z)
    m = f"{C30:.3f},0.5,0,1" if plane == "y" else f"{C30:.3f},-0.5,0,1"
    s = "".join(f'<tspan x="0" dy="{size if i else 0}">{escape(c)}</tspan>' for i, c in enumerate(ch)) if vertical else escape(ch)
    return (f'<text transform="matrix({m},{sx:.1f},{sy:.1f})" font-family="{SERIF}" font-size="{size}" '
            f'font-weight="700" text-anchor="middle" fill="{fill}">{s}</text>')


def eave_curve(a, b, lift):
    """Path segment a→b (3D points) with upturned ends: control point sags the middle."""
    m = tuple((a[i] + b[i]) / 2 for i in range(3))
    (mx, my) = P(m[0], m[1], m[2] - lift * 2)
    (bx, by) = P(*b)
    return f"Q{mx:.1f},{my:.1f} {bx:.1f},{by:.1f}"


def tiles(a0, a1, b0, b1, n, col, w=.7, op=.55):
    """n lines interpolated between edge a0→a1 and edge b0→b1 (tile rows on a slope)."""
    o = []
    for i in range(1, n):
        t = i / n
        p = tuple(a0[j] + (a1[j] - a0[j]) * t for j in range(3))
        q = tuple(b0[j] + (b1[j] - b0[j]) * t for j in range(3))
        o.append(line3(p, q, col, w, f'opacity="{op}"'))
    return "".join(o)


def gable_roof(x0, y0, x1, y1, zt, rh, o, col, wall):
    ym, ze, lift = (y0 + y1) / 2, zt - .12, .07
    r0, r1 = (x0 - o, ym, zt + rh), (x1 + o, ym, zt + rh)
    bl, br = (x0 - o, y0 - o, ze + lift), (x1 + o, y0 - o, ze + lift)
    fl, fr = (x0 - o, y1 + o, ze + lift), (x1 + o, y1 + o, ze + lift)
    s = [poly([P(*bl), P(*br), P(*r1), P(*r0)], shade(col, 1.15))]
    s.append(poly([P(x1, y0, zt), P(x1, y1, zt), P(x1, ym, zt + rh * .9)], wall))
    s.append(line3((x1, ym, zt + rh * .85), (x1, ym, zt), WOOD_DK, 1.4) + line3((x1, y0 + .1, zt + .12), (x1, y1 - .1, zt + .12), WOOD_DK, 1.4))
    d = f'M{pts([P(*r0)])} L{pts([P(*r1)])} L{pts([P(*fr)])} {eave_curve(fr, fl, lift)} Z'
    s.append(f'<path d="{d}" fill="{col}"/>')
    s.append(tiles(r0, r1, fl, fr, int((x1 - x0 + 2 * o) / .11), shade(col, .62), .8, .6))
    s.append(tiles(r0, fl, r1, fr, 4, shade(col, 1.3), .9, .45))
    s.append(f'<path d="M{pts([P(*fr)])} {eave_curve(fr, fl, lift)}" stroke="{shade(col, .5)}" stroke-width="2.2" fill="none"/>')
    s.append(f'<polyline points="{pts([P(*br), P(*r1), P(*fr)])}" stroke="{shade(col, .55)}" stroke-width="2.4" fill="none" stroke-linejoin="round"/>')
    s.append(line3(r0, r1, shade(col, .5), 3.4, 'stroke-linecap="round"'))
    return "".join(s)


def hip_roof(x0, y0, x1, y1, zt, rh, o, col, lift=.12):
    ym, ze = (y0 + y1) / 2, zt - .1
    a = min((y1 - y0) / 2, (x1 - x0) / 2)
    R0, R1 = (x0 + a, ym, zt + rh), (x1 - a, ym, zt + rh)
    E00, E10 = (x0 - o, y0 - o, ze + lift), (x1 + o, y0 - o, ze + lift)
    E01, E11 = (x0 - o, y1 + o, ze + lift), (x1 + o, y1 + o, ze + lift)
    def face(e0, e1, r_a, r_b, c):
        return f'<path d="M{pts([P(*e0)])} {eave_curve(e0, e1, lift)} L{pts([P(*r_b)])} L{pts([P(*r_a)])} Z" fill="{c}"/>'
    s = [face(E00, E10, R0, R1, shade(col, 1.12)), face(E00, E01, R0, R0, shade(col, 1.0)),
         face(E10, E11, R1, R1, shade(col, 1.22)), face(E01, E11, R0, R1, shade(col, .88))]
    s.append(tiles(R1, E10, R1, E11, 7, shade(col, .8), .7, .5))
    s.append(tiles(R0, R1, E01, E11, max(4, int((x1 - x0) / .16)), shade(col, .62), .7, .55))
    for e0, e1 in ((E10, E11), (E01, E11)):
        s.append(f'<path d="M{pts([P(*e0)])} {eave_curve(e0, e1, lift)}" stroke="{shade(col, .45)}" stroke-width="2.4" fill="none"/>')
    for e in (E10, E11, E01):
        s.append(line3(e, R1 if e[0] > x0 else R0, shade(col, .5), 1.8))
    if x1 - x0 > y1 - y0:
        s.append(line3(R0, R1, shade(col, .45), 3.6, 'stroke-linecap="round"'))
    return "".join(s)


def house(x0, y0, x1, y1, two, wood, wall, roofc, noren, sign):
    """Machiya: lattice ground floor, noren, pent roof, plaster upper floor, tiled gable roof."""
    s = [box(x0, y0, 0, x1, y1, 1.0, wood)]
    for u in [x0 + .06 + i * .085 for i in range(int((x1 - x0 - .1) / .085))]:  # koshi lattice
        s.append(line3((u, y1, .12), (u, y1, .82), shade(wood, 1.35), .9, 'opacity=".8"'))
    for u in [y0 + .1 + i * .1 for i in range(int((y1 - y0 - .15) / .1))]:
        s.append(line3((x1, u, .12), (x1, u, .82), shade(wood, 1.4), .8, 'opacity=".55"'))
    d0 = x0 + (x1 - x0) * .38
    s.append(fy(y1, d0, d0 + .55, 0, .82, "#2b1f16"))
    s.append(fy(y1, d0 + .05, d0 + .5, .42, .8, "#e9d8b0", 'opacity=".25"'))
    s.append(f'<g class="noren" style="animation-delay:-{rnd.uniform(0, 3):.1f}s">'
             + "".join(fy(y1 + .01, d0 + .02 + i * .175, d0 + .175 + i * .175, .52, .82, noren) for i in range(3))
             + iso_text(sign[0], d0 + .27, y1 + .01, .73, 8, "#f6efe2", vertical=False) + "</g>")
    s.append(fy(y1 + .01, x0 + .12, x0 + .32, .38, .92, "#3a2a1c") + iso_text(sign, x0 + .22, y1 + .02, .82, 7.5, "#f2d9a0"))
    s.append(fx(x1, y0 + .3, y0 + .75, .45, .8, "#f2e6c9") + "".join(line3((x1, y0 + .3 + j * .09, .45), (x1, y0 + .3 + j * .09, .8), wood, .8) for j in range(1, 5)))
    z = 1.0
    if two:  # pent roof + upper floor
        s.append(poly([P(x0 - .08, y1, z + .12), P(x1 + .08, y1, z + .12), P(x1 + .08, y1 + .32, z - .05), P(x0 - .08, y1 + .32, z - .05)], roofc))
        s.append(tiles((x0 - .08, y1, z + .12), (x1 + .08, y1, z + .12), (x0 - .08, y1 + .32, z - .05), (x1 + .08, y1 + .32, z - .05), int((x1 - x0) / .11), shade(roofc, .6)))
        s.append(line3((x0 - .08, y1 + .32, z - .05), (x1 + .08, y1 + .32, z - .05), shade(roofc, .45), 2))
        s.append(box(x0 + .02, y0 + .02, z, x1 - .02, y1 - .02, z + .72, wall))
        s.append(line3((x0, y1 - .02, z + .7), (x1 - .02, y1 - .02, z + .7), WOOD_DK, 1.4))
        for u0 in (x0 + (x1 - x0) * .2, x0 + (x1 - x0) * .58):  # mushiko-mado slit windows
            s.append(fy(y1 - .02, u0, u0 + (x1 - x0) * .24, z + .2, z + .5, "#4a3a2c"))
            for j in range(1, 6):
                u = u0 + (x1 - x0) * .24 * j / 6
                s.append(line3((u, y1 - .02, z + .2), (u, y1 - .02, z + .5), wall, 2.2))
        s.append(fx(x1 - .02, y0 + .5, y0 + .9, z + .25, z + .5, "#4a3a2c"))
        z += .72
    if rnd.random() < .6:  # hanging chochin lantern at the eave
        lx, ly = P(x1 - .1, y1 + .18, 1.0 if two else .95)
        s.append(f'<g class="lant" style="animation-delay:-{rnd.uniform(0, 3):.1f}s"><line x1="{lx:.1f}" y1="{ly - 6:.1f}" x2="{lx:.1f}" y2="{ly:.1f}" stroke="#222"/>'
                 f'<ellipse cx="{lx:.1f}" cy="{ly + 7:.1f}" rx="4.4" ry="6.2" fill="{VERMILION}"/>'
                 f'<ellipse class="lglow" cx="{lx - 1:.1f}" cy="{ly + 6:.1f}" rx="2" ry="3.5" fill="#ffb26b"/>'
                 f'<rect x="{lx - 3:.1f}" y="{ly:.1f}" width="6" height="1.6" fill="#222"/><rect x="{lx - 3:.1f}" y="{ly + 12.4:.1f}" width="6" height="1.6" fill="#222"/></g>')
    s.append(gable_roof(x0, y0, x1, y1, z, .55, .2, roofc, wall))
    return "".join(s)


def pagoda_iso(cx, cy):
    s = [box(cx - 1.2, cy - 1.2, 0, cx + 1.2, cy + 1.2, .22, "#a8a196")]
    z, w = .22, 1.0
    for i in range(5):
        h = .78 - i * .04
        s.append(box(cx - w, cy - w, z, cx + w, cy + w, z + h, VERMILION))
        s.append(fy(cy + w, cx - w, cx + w, z + h * .62, z + h, WALL) + fx(cx + w, cy - w, cy + w, z + h * .62, z + h, WALL))
        for t in (-.5, 0, .5):  # pillars & doors
            s.append(line3((cx + t * w * 1.6, cy + w, z), (cx + t * w * 1.6, cy + w, z + h), "#7d2219", 1.6))
            s.append(line3((cx + w, cy + t * w * 1.6, z), (cx + w, cy + t * w * 1.6, z + h), "#7d2219", 1.6))
        s.append(fy(cy + w, cx - w * .25, cx + w * .25, z, z + h * .55, "#4e2a1c"))
        s.append(line3((cx - w - .05, cy + w + .05, z + .06), (cx + w + .05, cy + w + .05, z + .06), WOOD_DK, 2)
                 + line3((cx + w + .05, cy - w - .05, z + .06), (cx + w + .05, cy + w + .05, z + .06), WOOD_DK, 2))
        o = .4 - i * .02
        s.append(hip_roof(cx - w, cy - w, cx + w, cy + w, z + h + .05, .3, o, "#434c58", lift=.14))
        z += h + .28
        w *= .87
    s.append(f'<g class="spire">' + line3((cx, cy, z - .2), (cx, cy, z + 1.5), GOLD, 3.2)
             + "".join(line3((cx - .14, cy, z + .25 + j * .1), (cx + .14, cy, z + .25 + j * .1), GOLD, 2.4) for j in range(9))
             + f'<circle cx="{P(cx, cy, z + 1.55)[0]:.1f}" cy="{P(cx, cy, z + 1.55)[1]:.1f}" r="4" fill="{GOLD}"/></g>')
    return "".join(s)


def temple_iso(x0, y0, x1, y1):
    s = [box(x0 - .35, y0 - .35, 0, x1 + .35, y1 + .35, .32, "#b3ac9f")]
    for i in range(4):  # stone steps
        cx = (x0 + x1) / 2
        s.append(box(cx - .55, y1 + .35 + i * .14, 0, cx + .55, y1 + .35 + (i + 1) * .14, .32 - (i + 1) * .08, "#c4bcae"))
    z0, z1 = .32, 1.55
    s.append(box(x0, y0, z0, x1, y1, z1, WALL))
    s.append(fy(y1, x0, x1, z0, z0 + .55, "#8a5a36") + fx(x1, y0, y1, z0, z0 + .55, "#8a5a36"))
    nx = 6
    for k in range(nx + 1):
        u = x0 + (x1 - x0) * k / nx
        s.append(fy(y1 + .01, u - .06, u + .06, z0, z1, VERMILION))
        if k < nx:  # shoji with kumiko grid
            a, b = u + .12, u + (x1 - x0) / nx - .12
            s.append(fy(y1, a, b, z0 + .62, z1 - .2, "#f7f0e1"))
            for g in range(1, 4):
                s.append(line3((a + (b - a) * g / 4, y1, z0 + .62), (a + (b - a) * g / 4, y1, z1 - .2), "#9b7353", .8))
            s.append(line3((a, y1, z0 + .95), (b, y1, z0 + .95), "#9b7353", .8))
    for k in range(4):
        u = y0 + (y1 - y0) * k / 3
        s.append(fx(x1 + .01, u - .06, u + .06, z0, z1, VERMILION))
    s.append(box(x0 - .08, y0 - .08, z1, x1 + .08, y1 + .08, z1 + .14, WOOD_DK))
    s.append(fy(y1 + .09, (x0 + x1) / 2 - .4, (x0 + x1) / 2 + .4, z1 - .38, z1 - .02, "#2b2018")
             + iso_text("智", (x0 + x1) / 2, y1 + .1, z1 - .13, 13, GOLD, vertical=False))
    s.append(hip_roof(x0, y0, x1, y1, z1 + .14, 1.0, .5, "#4a5562", lift=.18))
    rx0, rx1 = P(x0 + (y1 - y0) / 2, (y0 + y1) / 2, z1 + 1.14), P(x1 - (y1 - y0) / 2, (y0 + y1) / 2, z1 + 1.14)
    for (x, y) in (rx0, rx1):  # shachi ridge ornaments
        s.append(f'<path d="M{x - 4:.1f},{y:.1f} q4,-12 8,-2 q-2,4 -8,2 Z" fill="{GOLD}"/>')
    return "".join(s)


def torii_iso(xa, xb, y):
    s = []
    for x in (xa, xb):
        s.append(box(x - .08, y - .08, 0, x + .08, y + .08, 1.55, VERMILION) + box(x - .12, y - .12, 0, x + .12, y + .12, .12, "#2b2b2b"))
    s.append(box(xa - .3, y - .06, 1.12, xb + .3, y + .06, 1.24, VERMILION))
    s.append(box((xa + xb) / 2 - .06, y - .05, 1.24, (xa + xb) / 2 + .06, y + .05, 1.42, VERMILION))
    s.append(box(xa - .42, y - .1, 1.42, xb + .42, y + .1, 1.5, VERMILION))
    a, b = (xa - .55, y + .12, 1.62), (xb + .55, y + .12, 1.62)
    s.append(f'<path d="M{pts([P(*a)])} {eave_curve(a, b, .07)} L{pts([P(xb + .45, y + .12, 1.5)])} {eave_curve((xb + .45, y + .12, 1.5), (xa - .45, y + .12, 1.5), .07)} Z" fill="#2b2b2b"/>')
    return "".join(s)


def toro_iso(x, y):
    return (box(x - .16, y - .16, 0, x + .16, y + .16, .1, "#9a948a") + box(x - .06, y - .06, .1, x + .06, y + .06, .55, "#aaa498")
            + box(x - .14, y - .14, .55, x + .14, y + .14, .63, "#9a948a") + box(x - .1, y - .1, .63, x + .1, y + .1, .85, "#aaa498")
            + fy(y + .1, x - .05, x + .05, .67, .8, "#ffcf6a", 'class="flame"') + fx(x + .1, y - .05, y + .05, .67, .8, "#ffcf6a", 'class="flame"')
            + hip_roof(x - .1, y - .1, x + .1, y + .1, .87, .16, .1, "#8a847a", lift=.04))


def sakura_iso(x, y, s=1.0, seed=0):
    r = random.Random(seed)
    bx, by = P(x, y, 0)
    tx, ty = P(x, y, 1.25 * s)
    k = ISO["k"]
    o = [f'<ellipse cx="{bx - k * .45 * s:.1f}" cy="{by + k * .28 * s:.1f}" rx="{k * 1.25 * s:.1f}" ry="{k * .5 * s:.1f}" fill="#24361f" opacity=".2"/>',
         f'<g class="tree" style="transform-origin:{bx:.0f}px {by:.0f}px">',
         f'<path d="M{bx - 3:.1f},{by:.1f} C{bx - 1:.1f},{by - 15:.1f} {tx + 5:.1f},{ty + 12:.1f} {tx:.1f},{ty:.1f} L{tx + 4:.1f},{ty:.1f} C{tx + 8:.1f},{ty + 12:.1f} {bx + 4:.1f},{by - 15:.1f} {bx + 4:.1f},{by:.1f} Z" fill="#4a3328"/>']
    for ex, ey in ((-18, -14), (16, -18), (2, -26)):
        o.append(f'<path d="M{tx + 2:.1f},{ty:.1f} q{ex * .4:.0f},{ey * .2:.0f} {ex * s:.0f},{ey * s:.0f}" stroke="#4a3328" stroke-width="2.5" fill="none" stroke-linecap="round"/>')
    cols = [("#e994a8", "#eea8b8"), ("#f3b5c4", "#f6c1cc"), ("#f9d5dd", "#fde6eb")]
    for layer, (c1, c2) in enumerate(cols):  # dark underside → sunlit top-right
        for _ in range(38):
            a, d = r.uniform(0, 6.28), r.uniform(0, 1) ** .6
            cx = tx + math.cos(a) * k * 1.15 * s * d + layer * 3
            cy = ty - k * .55 * s + math.sin(a) * k * .7 * s * d - layer * 4
            o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r.uniform(3, 7) * s:.1f}" fill="{r.choice((c1, c2))}"/>')
    o.append("</g>")
    return "".join(o)


def cedar_iso(x, y, h=1.6, seed=0):
    r = random.Random(seed)
    bx, by = P(x, y, 0)
    k = ISO["k"]
    o = [f'<ellipse cx="{bx - k * .35:.1f}" cy="{by + k * .2:.1f}" rx="{k * .6:.1f}" ry="{k * .25:.1f}" fill="#24361f" opacity=".2"/>',
         f'<rect x="{bx - 1.5:.1f}" y="{by - k * .35:.1f}" width="3" height="{k * .35:.1f}" fill="{WOOD_DK}"/>']
    for i in range(5):
        ty = by - k * h + i * k * h * .17
        w = k * (.18 + i * .1)
        o.append(f'<path d="M{bx:.1f},{ty:.1f} L{bx + w:.1f},{ty + k * h * .3:.1f} Q{bx:.1f},{ty + k * h * .25:.1f} {bx - w:.1f},{ty + k * h * .3:.1f} Z" fill="#3c5c3b"/>')
        o.append(f'<path d="M{bx:.1f},{ty:.1f} L{bx + w:.1f},{ty + k * h * .3:.1f} Q{bx + w * .4:.1f},{ty + k * h * .26:.1f} {bx:.1f},{ty + k * h * .22:.1f} Z" fill="#5f8a55"/>')
    return "".join(o)


def walker(path, dur, delay, kimono, hat=True, umbrella=None):
    fig = (f'<ellipse cx="0" cy="0" rx="5" ry="2" fill="#000" opacity=".18"/>'
           f'<g class="bob"><path d="M-3.5,-1 L-2.5,-13 L2.5,-13 L3.5,-1 Z" fill="{kimono}"/><rect x="-3" y="-9" width="6" height="1.6" fill="#f2d9a0"/>'
           f'<circle cx="0" cy="-15.5" r="2.8" fill="#f1d3b3"/>'
           + (f'<path d="M-6.5,-15.5 L0,-20.5 L6.5,-15.5 Z" fill="#c8a45a"/>' if hat else '<path d="M-2.8,-16 a2.8,2.8 0 0,1 5.6,0 Z" fill="#222"/>')
           + (f'<line x1="2" y1="-11" x2="5" y2="-24" stroke="#5b4636" stroke-width="1"/><path d="M-6,-22 Q5,-32 16,-22 Z" fill="{umbrella}"/>' if umbrella else "")
           + "</g>")
    return (f'<g opacity="0"><animateMotion dur="{dur}s" begin="-{delay}s" repeatCount="indefinite" path="{path}"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.06;.94;1" dur="{dur}s" begin="-{delay}s" repeatCount="indefinite"/>{fig}</g>')


def nobori(x, y, text, col):
    bx, by = P(x, y, 0)
    k = ISO["k"]
    return (f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{bx:.1f}" y2="{by - k * 1.7:.1f}" stroke="#5b4636" stroke-width="1.6"/>'
            f'<g class="flag" style="animation-delay:-{rnd.uniform(0, 2):.1f}s"><rect x="{bx + 1:.1f}" y="{by - k * 1.62:.1f}" width="9" height="{k * 1.15:.1f}" fill="{col}"/>'
            f'<rect x="{bx + 1:.1f}" y="{by - k * 1.62:.1f}" width="9" height="3" fill="#fff" opacity=".8"/>'
            + "".join(f'<text x="{bx + 5.5:.1f}" y="{by - k * 1.62 + 13 + i * 10:.1f}" text-anchor="middle" font-family="{SERIF}" font-size="8" font-weight="700" fill="#fff">{c}</text>' for i, c in enumerate(text))
            + "</g>")


def boat(path, dur):
    """Hull drawn top-down (bow at +u) and mapped onto the iso ground plane, so it lies along the canal."""
    m = f"matrix({C30:.3f},0.5,{-C30:.3f},0.5,0,0)"
    shape = "M32,0 C24,-7 -18,-8 -26,-6 L-26,6 C-18,8 24,7 32,0 Z"
    inner = "M26,0 C20,-4.5 -15,-5 -22,-3.8 L-22,3.8 C-15,5 20,4.5 26,0 Z"
    hull_ = (f'<g transform="{m}"><ellipse cx="-38" cy="0" rx="26" ry="9" fill="#fff" opacity=".22"/></g>'
             f'<g transform="translate(0,5) {m}"><path d="{shape}" fill="#4e3320"/></g>'
             f'<g transform="{m}"><path d="{shape}" fill="#8a6440"/><path d="{inner}" fill="#5e4129"/>'
             '<line x1="-6" y1="-4.6" x2="-6" y2="4.6" stroke="#8a6440" stroke-width="2"/><line x1="10" y1="-4.4" x2="10" y2="4.4" stroke="#8a6440" stroke-width="2"/>'
             '<rect x="2" y="-3" width="6" height="6" fill="#c8a45a"/></g>')  # a little cargo crate
    sx, sy = -21 * C30, -10.5  # stern, in screen coordinates
    man = (f'<g transform="translate({sx:.1f},{sy:.1f})"><g class="bob"><path d="M-4,0 L-3,-14 L2,-14 L3,0 Z" fill="#2c4a7a"/>'
           '<circle cx="0" cy="-16.5" r="2.6" fill="#f1d3b3"/><path d="M-7,-16 L0,-21 L7,-16 Z" fill="#c8a45a"/>'
           '<line x1="-2" y1="-11" x2="-17" y2="10" stroke="#5b4636" stroke-width="1.4"/></g></g>')
    return (f'<g opacity="0"><animateMotion dur="{dur}s" repeatCount="indefinite" path="{path}"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.05;.95;1" dur="{dur}s" repeatCount="indefinite"/>{hull_}{man}</g>')


ISO_CSS = (".bob{animation:bob .5s ease-in-out infinite alternate}@keyframes bob{to{transform:translateY(-1.2px)}}"
           ".flag{transform-box:fill-box;transform-origin:0 0;animation:flag 2.2s ease-in-out infinite}@keyframes flag{0%,100%{transform:skewY(-4deg)}50%{transform:skewY(5deg) scaleX(.85)}}"
           ".flame,.lglow{animation:flame 1.8s ease-in-out infinite}@keyframes flame{0%,100%{opacity:.7}50%{opacity:1}}"
           ".smoke{animation:smoke 6s ease-out infinite;opacity:0}@keyframes smoke{0%{opacity:0;transform:translate(0,0) scale(.4)}"
           "15%{opacity:.55}100%{opacity:0;transform:translate(-18px,-70px) scale(2.2)}}"
           ".ripple{animation:ripple 4s ease-in-out infinite}@keyframes ripple{0%,100%{transform:translate(0,0);opacity:.2}50%{transform:translate(10px,5px);opacity:.8}}")


def diorama():
    ISO.update(ox=884, oy=168, k=26)
    X, Y = 12, 9
    b = []
    # floating earth slab (soil strata on the two visible sides)
    cx, cy = P(X / 2, Y / 2)
    b.append(f'<ellipse cx="{cx:.0f}" cy="{cy + 120:.0f}" rx="300" ry="34" fill="#4d6b7a" opacity=".18"/>')
    for z0, z1, c in ((-1.3, -.75, "#7a5b3e"), (-.75, -.3, "#8e6b47"), (-.3, -.08, "#a07a50"), (-.08, 0, "#6f9a53")):
        b.append(poly([P(0, Y, z0), P(X, Y, z0), P(X, Y, z1), P(0, Y, z1)], shade(c, .82)))
        b.append(poly([P(X, 0, z0), P(X, Y, z0), P(X, Y, z1), P(X, 0, z1)], c))
    for _ in range(26):  # pebbles in the soil
        u, z = rnd.uniform(0, 1), rnd.uniform(-1.2, -.2)
        p = P(u * X, Y, z) if rnd.random() < .55 else P(X, u * Y, z)
        b.append(f'<ellipse cx="{p[0]:.1f}" cy="{p[1]:.1f}" rx="{rnd.uniform(2, 4.5):.1f}" ry="{rnd.uniform(1.2, 2.5):.1f}" fill="#5e4630" opacity=".7"/>')
    b.append(poly([P(0, 0), P(X, 0), P(X, Y), P(0, Y)], "url(#grass)"))
    for _ in range(170):  # grass tufts & tiny flowers
        x, y = rnd.uniform(.1, X - .1), rnd.uniform(.1, Y - .1)
        sx, sy = P(x, y)
        if rnd.random() < .2:
            b.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="1.3" fill="{rnd.choice(["#fff", "#f6c1cc", "#f2d26b"])}"/>')
        else:
            b.append(f'<path d="M{sx - 2:.1f},{sy:.1f} l1,-4 l1,3 l1,-5 l1,6" stroke="#5c8a4a" stroke-width=".9" fill="none"/>')
    # street, approach path, canal
    b.append(poly([P(0, 4.1), P(X, 4.1), P(X, 5.2), P(0, 5.2)], "#dccdab"))
    for _ in range(90):
        sx, sy = P(rnd.uniform(.1, X - .1), rnd.uniform(4.15, 5.15))
        b.append(f'<ellipse cx="{sx:.1f}" cy="{sy:.1f}" rx="{rnd.uniform(1, 2.6):.1f}" ry="{rnd.uniform(.6, 1.3):.1f}" fill="#b9a67e" opacity=".7"/>')
    for i in range(int(X / .5)):  # stepping stones down the middle
        x = .2 + i * .5
        b.append(poly([P(x, 4.5), P(x + .38, 4.5), P(x + .38, 4.8), P(x, 4.8)], "#c3b597", 'stroke="#a8987a" stroke-width=".6"'))
    b.append(poly([P(7.05, 2.9), P(8.35, 2.9), P(8.35, 4.1), P(7.05, 4.1)], "#d2c3a1"))
    for j in range(5):
        y = 2.95 + j * .23
        b.append(poly([P(7.25, y), P(8.15, y), P(8.15, y + .18), P(7.25, y + .18)], "#bfb08e"))
    b.append(poly([P(0, 7.9), P(X, 7.9), P(X, 8.8), P(0, 8.8)], "url(#canal)"))
    b.append(poly([P(0, 8.8, 0), P(X, 8.8, 0), P(X, 8.8, -.25), P(0, 8.8, -.25)], "#4f8ea3"))
    for x0 in range(0, X):  # stone embankment
        b.append(box(x0 + .02, 7.75, -.05, x0 + .98, 7.9, .08, "#a7a092"))
    for _ in range(14):
        x = rnd.uniform(.3, X - .8)
        b.append(f'<g class="ripple" style="animation-delay:-{rnd.uniform(0, 4):.1f}s">{line3((x, rnd.uniform(8.05, 8.65), 0), (x + .6, 8.3, 0), "#fff", 1.2)}</g>')
    # shadows first, objects painter-sorted afterwards
    fronts = [(.3, 5.75, 2.1, 7.05, True), (2.4, 5.8, 3.9, 6.95, False), (4.2, 5.75, 6.0, 7.05, True), (6.3, 5.8, 7.8, 6.95, False), (8.1, 5.75, 9.9, 7.05, True)]
    backs = [(3.75, 1.5, 5.35, 3.3, True), (10.0, 2.4, 11.6, 3.85, False)]
    for x0, y0, x1, y1, two in fronts + backs:
        b.append(shadow(x0, y0, x1, y1, 2.2 if two else 1.5))
    b.append(shadow(1.0, 1.0, 3.4, 3.4, 3.2, .16) + shadow(5.6, .5, 9.9, 2.6, 2.5, .16))
    pal = [("#7a5132", "#f3ece0", "#454e5b", "#2c4a7a", "茶屋"), ("#6a462c", "#efe5d2", "#3b434e", "#7a2c2c", "酒蔵"),
           ("#86593a", "#f6efe3", "#4a5260", "#3d5a40", "宿屋"), ("#6f4b30", "#f1e8d6", "#3f4753", "#2c4a7a", "書店"),
           ("#7d5434", "#f3ece0", "#454e5b", "#7a2c2c", "米屋"), ("#6a462c", "#efe5d2", "#3b434e", "#3d5a40", "茶")]
    back_objs = [(1.2, cedar_iso(.5, .6, 1.9, 1)), (.9, cedar_iso(.4, 2.4, 1.5, 2)), (2.0, cedar_iso(1.4, .3, 1.7, 3)),
                 (4.4, pagoda_iso(2.2, 2.2)), (7.3, house(*backs[0][:4], True, *pal[5][:4], pal[5][4])),
                 (7.6, temple_iso(5.9, .8, 9.6, 2.4)), (8.2, cedar_iso(10.3, .7, 1.8, 4)), (10.2, cedar_iso(11.4, .5, 1.6, 5)),
                 (10.7, toro_iso(6.75, 3.6)), (11.9, toro_iso(8.65, 3.6)), (11.2, torii_iso(7.15, 8.25, 3.75)),
                 (12.9, house(*backs[1][:4], False, *pal[2][:4], "蕎麦")), (5.0, sakura_iso(.9, 3.6, .9, 7)), (13.6, sakura_iso(12.0, 1.4, .95, 8))]
    # incense burner + smoke in front of the hall
    ix, iy = 7.7, 3.25
    sx, sy = P(ix, iy, .55)
    back_objs.append((10.95, box(ix - .18, iy - .12, 0, ix + .18, iy + .12, .45, "#5b5148")
                      + "".join(f'<circle class="smoke" cx="{sx:.1f}" cy="{sy:.1f}" r="5" fill="#f4f1ea" style="animation-delay:-{d:.1f}s"/>' for d in (0, 1.5, 3, 4.5))))
    b.extend(o for _, o in sorted(back_objs, key=lambda t: t[0]))
    # street life (between back row and front row)
    for yy, dirn, dur, dl, kim, hat, umb in ((4.35, 1, 34, 0, "#7a2c2c", True, None), (4.35, 1, 34, 17, "#3d5a40", False, "#c0392b"),
                                            (4.95, -1, 40, 8, "#2c4a7a", True, None), (4.95, -1, 40, 28, "#8e5a9e", False, "#f2d9a0")):
        a, c = P(.2, yy), P(X - .2, yy)
        if dirn < 0:
            a, c = c, a
        b.append(walker(f"M{a[0]:.1f},{a[1]:.1f} L{c[0]:.1f},{c[1]:.1f}", dur, dl, kim, hat, umb))
    front_objs = [(x0 + 6, house(x0, y0, x1, y1, two, *pal[i][:4], pal[i][4])) for i, (x0, y0, x1, y1, two) in enumerate(fronts)]
    front_objs += [(5.3 + x, nobori(x, 5.3, t, c)) for x, t, c in ((2.3, "団子", VERMILION), (6.42, "甘味", "#2c4a7a"), (10.45, "祭り", VERMILION))]
    front_objs.append((17.5, sakura_iso(11.2, 6.4, 1.0, 9)))
    b.extend(o for _, o in sorted(front_objs, key=lambda t: t[0]))
    a, c = P(.6, 8.35), P(X - .8, 8.35)
    b.append(boat(f"M{a[0]:.1f},{a[1]:.1f} L{c[0]:.1f},{c[1]:.1f}", 36))
    defs = lg("grass", [(0, "#8fb56f"), (1, "#7aa35e")], 1, 1) + lg("canal", [(0, "#8cc6d4"), (1, "#5d9fb3")], 1, 1)
    return "".join(b), defs


# ─────────────────────────── header ────────────────────────────
def header(linkedin=False):
    """README header (1200x500), or with linkedin=True a 1584x396 LinkedIn banner re-composed from the same parts."""
    W, H = 1200, 500
    b = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
         f'<circle class="sun" cx="1040" cy="92" r="130" fill="url(#sun)"/><circle cx="1040" cy="92" r="30" fill="#fff8de"/>']
    for i, (y, s, d) in enumerate([(70, .9, 120), (120, .6, 95), (52, .5, 140), (150, .75, 110), (95, .45, 160)]):
        b.append(f'<g class="cloud" style="animation-duration:{d}s;animation-delay:-{d*i/5 + 13:.0f}s">{cloud(0, y, s)}</g>')
    fl, fcss = birds(4, W)
    b.append(fl)
    # Mt. Fuji
    b.append('<path d="M330,330 C470,262 600,160 668,124 Q690,116 712,124 C780,160 910,262 1050,330 Z" fill="url(#fuji)"/>')
    b.append('<path d="M668,124 Q690,116 712,124 C735,136 760,154 784,172 L770,180 L756,170 L742,186 L728,172 L712,190 L698,174 '
             'L684,192 L670,176 L654,188 L642,174 L626,182 L612,170 C630,156 650,140 668,124 Z" fill="#fbfdff"/>')
    b.append('<path d="M690,118 C700,150 704,170 700,186" stroke="#d6e1ec" stroke-width="3" fill="none" opacity=".8"/>')
    b.append(f'<path d="{ridge(0, W, H, 268, 46, 3)}" fill="url(#far)" opacity=".9"/>')
    b.append(f'<rect class="mist" x="-60" y="270" width="{W + 120}" height="90" fill="url(#haze)"/>')
    b.append(f'<path d="{ridge(0, W, H, 330, 34, 8)}" fill="url(#mid)"/>')
    b.append(f'<path d="{ridge(0, W, H, 395, 22, 15)}" fill="#8fae94" opacity=".55"/>')
    b.append(f'<rect x="0" y="380" width="{W}" height="{H - 380}" fill="url(#haze)"/>')
    b.append("".join(f'<g class="cloud" style="animation-duration:{d}s;animation-delay:-{d * i / 6:.0f}s">{cloud(0, y, s, .85)}</g>'
                     for i, (y, s, d) in enumerate([(455, 1.1, 150), (485, .9, 130), (440, .8, 170), (478, 1.2, 190), (465, .7, 120), (492, 1.0, 160)])))
    scene, sdefs = diorama()
    if linkedin:  # sky/mountains scaled to full width and cropped, village shrunk to fit on the right
        b = [f'<g transform="translate(0,-135) scale(1.32)">{"".join(b)}</g>',
             f'<g transform="translate(660,-12) scale(.8)">{scene}</g>']
        W, H = 1584, 396
    else:
        b.append(scene)
    pt, pcss = petals(30, W, H)
    b.append(pt)

    # ── text ──
    T = 5.0 * len(TAGLINES)
    fs, cw = 13.5, 13.5 * 0.6
    tx, ty = 64, 238
    text = [
        f'<rect x="40" y="38" width="560" height="226" rx="14" fill="#fffaf0" opacity=".8"/>',
        f'<rect x="40" y="38" width="560" height="226" rx="14" fill="none" stroke="#e4d5b5" stroke-width="1.2"/>',
        f'<g class="up" style="animation-delay:.1s"><text x="64" y="84" font-family="{SERIF}" font-size="19" letter-spacing="6" fill="{VERMILION}">{NAME_JP}</text></g>',
        f'<g class="up" style="animation-delay:.35s"><text x="62" y="146" font-family="{SERIF}" font-size="52" font-weight="700" letter-spacing="1" fill="{INK}">{NAME}</text></g>',
        f'<path class="brush" d="M64,162 C200,156 400,170 540,160" stroke="{VERMILION}" stroke-width="5" fill="none" stroke-linecap="round" pathLength="1"/>',
        f'<g class="up" style="animation-delay:.9s"><text x="64" y="196" font-family="{SERIF}" font-size="21" fill="{INK2}">{escape(ROLE)}</text></g>',
        # hanko seal
        f'<g class="seal"><rect x="536" y="56" width="44" height="44" rx="5" fill="{VERMILION}"/>'
        f'<rect x="540" y="60" width="36" height="36" rx="3" fill="none" stroke="#fbe9e2" stroke-width="1.3"/>'
        f'<text x="558" y="87" text-anchor="middle" font-family="{SERIF}" font-size="24" font-weight="700" fill="#fbe9e2">安</text></g>',
        f'<rect x="56" y="216" width="528" height="32" rx="6" fill="{INK}" opacity=".9"/>',
    ]
    if linkedin:  # no typing tagline in a still; card kept top-left, clear of the profile photo
        text = text[:7]  # card, kana, name, brush, role, seal
        text[:2] = [t.replace('height="226"', 'height="180"') for t in text[:2]]
        text = [f'<g transform="translate(16,-14) scale(.9)">{"".join(text)}</g>']
    for i, line in enumerate(TAGLINES if not linkedin else []):
        s0 = i * 5.0 / T
        k = f"0;{s0:.4f};{s0 + 1.8/T:.4f};{s0 + 4.3/T:.4f};{s0 + 4.8/T:.4f};1"
        wfull = len(line) * cw + 2
        text.append(f'<clipPath id="tl{i}"><rect x="{tx}" y="{ty - 18}" height="26" width="0">'
                    f'<animate attributeName="width" values="0;0;{wfull:.0f};{wfull:.0f};0;0" keyTimes="{k}" dur="{T}s" repeatCount="indefinite"/></rect></clipPath>')
        text.append(f'<text clip-path="url(#tl{i})" x="{tx}" y="{ty}" font-family="{MONO}" font-size="{fs}" fill="#f3ece0" xml:space="preserve">{escape(line)}</text>')
        text.append(f'<rect class="caret" x="{tx}" y="{ty - 13}" width="8" height="16" fill="#f2c14e" opacity="0">'
                    f'<animate attributeName="x" values="{tx};{tx};{tx + wfull:.0f};{tx + wfull:.0f};{tx};{tx}" keyTimes="{k}" dur="{T}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;{s0:.4f};{s0 + 4.9/T:.4f};{min(1, s0 + 4.95/T):.4f}" dur="{T}s" repeatCount="indefinite" calcMode="discrete"/></rect>')
    css = (SCENE_CSS + fcss + pcss
           + ".up{opacity:0;animation:up 1s ease-out forwards}@keyframes up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}"
           + ".brush{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1.2s .8s ease-in-out forwards}@keyframes draw{to{stroke-dashoffset:0}}"
           + ".seal{transform-box:fill-box;transform-origin:center;opacity:0;animation:stamp .5s 1.4s cubic-bezier(.3,1.6,.6,1) forwards}"
           + "@keyframes stamp{from{opacity:0;transform:scale(2) rotate(-12deg)}to{opacity:1;transform:rotate(-4deg)}}")
    return svg(W, H, "".join(b + text), css + ISO_CSS, f"{NAME} — {ROLE}", sky_defs(H) + sdefs)


# ─────────────────────── section banners ────────────────────────
def banner(kanji, title, cmd):
    W, H = 1200, 84
    rr = random.Random(title)
    blossoms = "".join(f'<g class="bl" style="animation-delay:-{rr.uniform(0,4):.1f}s">'
                       + "".join(f'<circle cx="{bx + 5*math.cos(a):.1f}" cy="{by + 5*math.sin(a):.1f}" r="4" fill="#f6c1cc"/>' for a in [j*1.2566 for j in range(5)])
                       + f'<circle cx="{bx}" cy="{by}" r="2" fill="#e0607e"/></g>'
                       for bx, by in [(1050, 28), (1088, 54), (1126, 20), (1141, 44), (1170, 52)])  # on the branch or at twig tips
    body = (f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12" fill="url(#washi)" stroke="#e4d5b5"/>'
            f'<path d="M1020,18 C1070,40 1120,30 1190,60" stroke="#5b4636" stroke-width="3" fill="none" stroke-linecap="round"/>'
            f'<path d="M1073,32 L1088,54 M1114,39 L1126,20" stroke="#5b4636" stroke-width="2" stroke-linecap="round"/>{blossoms}'
            f'<g class="seal"><rect x="24" y="18" width="48" height="48" rx="6" fill="{VERMILION}"/>'
            f'<text x="48" y="{50 if len(kanji) == 1 else 49}" text-anchor="middle" font-family="{SERIF}" font-size="{26 if len(kanji) == 1 else 19}" font-weight="700" fill="#fbe9e2">{kanji}</text></g>'
            f'<text x="92" y="50" font-family="{SERIF}" font-size="28" font-weight="700" fill="{INK}">{escape(title)}</text>'
            f'<path class="brush" d="M92,62 C260,58 420,66 560,60" stroke="{VERMILION}" stroke-width="3.5" fill="none" stroke-linecap="round" pathLength="1" opacity=".85"/>'
            f'<text x="600" y="50" font-family="{MONO}" font-size="15" fill="{INK2}">{escape(cmd)}<tspan class="blink" fill="{VERMILION}">▌</tspan></text>')
    css = (".brush{stroke-dasharray:1;animation:draw 7s ease-in-out infinite}@keyframes draw{0%{stroke-dashoffset:1;opacity:.85}25%,88%{stroke-dashoffset:0;opacity:.85}100%{stroke-dashoffset:0;opacity:0}}"
           ".seal{transform-box:fill-box;transform-origin:center;transform:rotate(-4deg);animation:stamp 7s ease-out infinite}"
           "@keyframes stamp{0%{transform:scale(1.5) rotate(-14deg);opacity:0}6%,100%{transform:rotate(-4deg);opacity:1}}"
           ".blink{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
           ".bl{transform-box:fill-box;transform-origin:center;animation:bl 4s ease-in-out infinite}@keyframes bl{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(8deg) scale(1.06)}}")
    return svg(W, H, body, css, title, lg("washi", [(0, "#fffaf0"), (1, "#f5ecd9")], 1, 0))


# ─────────────────────────── journey ────────────────────────────
def toro(x, base, i, n, T):
    """Stone lantern that lights up when the pilgrim passes."""
    s0 = (i + 0.5) / n
    light = (f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{max(0, s0 - .03):.3f};{s0:.3f};.97;1" dur="{T}s" repeatCount="indefinite"/>')
    return (f'<g><rect x="{x - 16}" y="{base - 6}" width="32" height="6" fill="#8f8a80"/>'
            f'<rect x="{x - 5}" y="{base - 40}" width="10" height="34" fill="#a7a196"/>'
            f'<rect x="{x - 13}" y="{base - 46}" width="26" height="7" fill="#8f8a80"/>'
            f'<rect x="{x - 10}" y="{base - 66}" width="20" height="20" fill="#a7a196"/>'
            f'<rect x="{x - 5}" y="{base - 62}" width="10" height="12" fill="#5a554d"/>'
            f'<g opacity="0">{light}<circle cx="{x}" cy="{base - 56}" r="16" fill="url(#glow)"/><rect x="{x - 5}" y="{base - 62}" width="10" height="12" fill="#ffd36b"/></g>'
            f'<path d="M{x - 22},{base - 64} Q{x},{base - 84} {x + 22},{base - 64} Z" fill="#7d786e"/>'
            f'<circle cx="{x}" cy="{base - 80}" r="4" fill="#7d786e"/></g>')


def journey():
    W, H, n, T = 1200, 300, len(JOURNEY), 16
    xs = [110 + i * (W - 220) / (n - 1) for i in range(n)]
    path = "M40,232 " + " ".join(f"Q{(xs[i] + xs[i+1])/2:.0f},{200 if i % 2 else 250} {xs[i+1]:.0f},232" for i in range(n - 1)) + f" L{W - 20},232"
    path = f"M40,232 L{xs[0]:.0f},232 " + path[len("M40,232 "):]
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="url(#jsky)"/>',
         f'<path d="{ridge(0, W, 180, 120, 26, 21)}" fill="#c9d8df" opacity=".8"/>',
         f'<path d="M0,170 C300,150 700,175 1200,150 L1200,{H} L0,{H} Z" fill="url(#grass)"/>',
         ''.join(cedar(x, 172 + rnd.uniform(-6, 4), rnd.uniform(26, 40), "#4f7a4d", "#6a9462") for x in range(0, W, 23)),
         f'<path d="{path}" stroke="#e9dcc0" stroke-width="30" fill="none" stroke-linecap="round"/>',
         f'<path d="{path}" stroke="#d3c19b" stroke-width="2" stroke-dasharray="2 22" fill="none" stroke-linecap="round"/>']
    for i, (name, num) in enumerate(JOURNEY):
        x = xs[i]
        cur = i == n - 1
        b.append(toro(x, 214, i, n, T))
        b.append(f'<rect x="{x - 70}" y="254" width="140" height="34" rx="5" fill="{VERMILION if cur else WOOD}" />'
                 f'<text x="{x}" y="276" text-anchor="middle" font-family="{SERIF}" font-size="16" font-weight="700" fill="#fff8ec">'
                 f'<tspan font-size="13" fill="#f2d9a0">{num}</tspan>  {escape(name)}</text>')
    b.append(f'<g><animateMotion dur="{T}s" repeatCount="indefinite" path="{path}" keyPoints="0;1;1" keyTimes="0;.94;1" calcMode="linear"/>'
             f'<g transform="translate(0,-14)"><ellipse cx="0" cy="14" rx="9" ry="3" fill="#000" opacity=".15"/>'
             f'<rect x="-5" y="-6" width="10" height="18" rx="3" fill="#2c4a7a"/><circle cx="0" cy="-9" r="4.5" fill="#f1d3b3"/>'
             f'<path d="M-13,-10 L0,-20 L13,-10 Z" fill="#c8a45a"/><line x1="8" y1="-6" x2="12" y2="14" stroke="{WOOD_DK}" stroke-width="2"/></g></g>')
    b.append(f'<text x="40" y="40" font-family="{SERIF}" font-size="22" font-weight="700" fill="{INK}">道 <tspan font-size="16" font-weight="400" fill="{INK2}">the road so far · NL · CH · FR · BE · NO</tspan></text>')
    pt, pcss = petals(12, W, H, drift=-160)
    b.append(pt)
    defs = (lg("jsky", [(0, "#cfe6f4"), (1, "#f8f1e2")]) + lg("grass", [(0, "#9cbc86"), (1, "#7fa36c")])
            + '<radialGradient id="glow"><stop offset="0" stop-color="#ffd36b" stop-opacity=".9"/><stop offset="1" stop-color="#ffd36b" stop-opacity="0"/></radialGradient>')
    return svg(W, H, "".join(b), pcss, "Career: " + " → ".join(j[0] for j in JOURNEY), defs)


# ─────────────────────────── footer ────────────────────────────
KOI_BODY = "M20,0 C20,-5 13,-7.5 4,-7 C-5,-6.5 -12,-3.5 -17,0 C-12,3.5 -5,6.5 4,7 C13,7.5 20,5 20,0 Z"
KOI_TAIL = "M-15,0 C-20,-1.5 -24,-8 -31,-9 C-27,-3 -27,3 -31,9 C-24,8 -20,1.5 -15,0 Z"


def koi(i, path, dur, delay, base, spots, s=1.0):
    """Top-down koi: shaded body, flowing tail and fins, colour patches clipped to the body."""
    fin = '<path d="M5,-6 C1,-13 -5,-13 -4,-6 Z" fill="{c}" opacity=".7"/><path d="M5,6 C1,13 -5,13 -4,6 Z" fill="{c}" opacity=".7"/>'.format(c=base)
    wag = lambda a, d: f'<animateTransform attributeName="transform" type="rotate" values="-{a} {d};{a} {d};-{a} {d}" dur=".9s" repeatCount="indefinite"/>'
    return (f'<clipPath id="koi{i}"><path d="{KOI_BODY}"/></clipPath>'
            f'<g opacity=".93"><animateMotion dur="{dur}s" begin="-{delay}s" repeatCount="indefinite" rotate="auto" path="{path}"/><g transform="scale({s})">'
            f'<path d="{KOI_BODY}" transform="translate(3,5)" fill="#1d4a5c" opacity=".22"/>'
            f'<g><path d="{KOI_TAIL}" fill="{base}" opacity=".85"/>{wag(16, "-15 0")}</g>'
            f'<g>{fin}{wag(10, "2 0")}</g>'
            f'<path d="{KOI_BODY}" fill="{base}"/>'
            f'<g clip-path="url(#koi{i})">' + "".join(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{c}"/>' for x, y, rx, ry, c in spots)
            + '<path d="M18,0 C10,-2 -6,-2 -16,0" stroke="#fff" stroke-width="1.6" fill="none" opacity=".35"/></g>'
            '<circle cx="15" cy="-3.3" r="1" fill="#1a1a1a"/><circle cx="15" cy="3.3" r="1" fill="#1a1a1a"/></g></g>')


def footer():
    W, H = 1200, 230
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="url(#fsky)"/>',
         f'<path d="{ridge(0, W, 120, 78, 22, 33)}" fill="#bccdd6"/>',
         f'<path d="M0,110 C300,96 900,120 1200,100 L1200,{H} L0,{H} Z" fill="#8fb27c"/>',
         f'<path d="M0,140 C300,128 900,150 1200,132 L1200,{H} L0,{H} Z" fill="url(#water)"/>']
    for i in range(14):
        y = rnd.uniform(150, 220)
        x = rnd.uniform(0, W)
        b.append(f'<path class="rip" style="animation-delay:-{rnd.uniform(0,6):.1f}s" d="M{x:.0f},{y:.0f} q12,-4 24,0 t24,0" stroke="#ffffff" stroke-width="1.5" fill="none" opacity=".55"/>')
    for x, y in [(160, 200), (240, 186), (980, 196), (1060, 210)]:
        b.append(f'<path d="M{x},{y} m-14,0 a14,6 0 1,0 28,0 a14,6 0 1,0 -28,0" fill="#5f8f55"/><path d="M{x},{y} l12,-3" stroke="#7fae6f" stroke-width="2"/>')
    kohaku = [(10, -3, 7, 6, "#d8401f"), (-4, 4, 6, 5, "#d8401f"), (-12, -2, 4, 3.5, "#d8401f")]
    showa = [(12, 0, 8, 7, "#1f1f1f"), (0, -4, 7, 5, "#f4f1ea"), (-10, 3, 6, 5, "#1f1f1f"), (4, 5, 5, 3, "#d8401f")]
    tancho = [(14, 0, 4, 4, "#d8401f")]
    b.append(koi(0, "M150,190 C350,165 650,215 900,185 C1080,165 1110,214 900,212 C650,208 350,222 150,205 C60,200 60,192 150,190 Z", 46, 0, "#f6f1e7", kohaku))
    b.append(koi(1, "M1050,175 C850,200 620,168 420,196 C250,220 120,182 230,170 C420,150 820,205 1050,175 Z", 52, 20, "#f08a24", [], .9))
    b.append(koi(2, "M330,205 C520,180 760,218 960,195 C1020,188 990,170 900,172 C700,176 520,166 330,180 C260,186 270,210 330,205 Z", 38, 8, "#e9e3d6", showa, .85))
    b.append(koi(3, "M700,215 C850,200 1000,220 1100,200 C1150,190 1120,175 1050,182 C900,195 800,178 700,190 C640,198 650,218 700,215 Z", 30, 4, "#f8f5ee", tancho, .8))
    # taiko-bashi arched bridge
    b.append(f'<path d="M470,150 Q600,60 730,150 L716,150 Q600,78 484,150 Z" fill="{VERMILION}"/>'
             f'<path d="M466,128 Q600,40 734,128" stroke="{VERMILION}" stroke-width="4" fill="none"/>'
             + "".join(f'<line x1="{x}" y1="{150 - (1 - ((x - 600) / 130) ** 2) * 45:.0f}" x2="{x}" y2="{128 - (1 - ((x - 600) / 134) ** 2) * 44:.0f}" stroke="{VERMILION}" stroke-width="3"/>'
                       for x in range(486, 720, 26))
             + '<path d="M470,150 Q600,60 730,150" stroke="#7d2219" stroke-width="2" fill="none"/>'
             f'<path d="M484,152 Q600,240 716,152" stroke="#e89a8f" stroke-width="2" fill="none" opacity=".45"/>')
    b.append(pine(110, 132, .8) + pine(1110, 128, .7))
    b.append(f'<text x="600" y="34" text-anchor="middle" font-family="{SERIF}" font-size="24" font-weight="700" fill="{INK}">また会いましょう</text>'
             f'<text x="600" y="58" text-anchor="middle" font-family="{SERIF}" font-size="15" fill="{INK2}">thanks for walking through the village · see you again</text>')
    pt, pcss = petals(14, W, H, drift=-140)
    b.append(pt)
    css = (pcss + ".rip{animation:rip 6s ease-in-out infinite}@keyframes rip{0%,100%{transform:translateX(0);opacity:.15}50%{transform:translateX(18px);opacity:.7}}")
    defs = lg("fsky", [(0, "#d6ebf6"), (1, "#f8f1e2")]) + lg("water", [(0, "#8fc3cf"), (1, "#5d9fb3")])
    return svg(W, H, "".join(b), css, "Thanks for visiting", defs)


# ─────────────────────────── stats ────────────────────────────
def get(url):
    h = {"User-Agent": "profile-readme-builder", "Accept": "application/json"}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok and "api.github.com" in url:
        h["Authorization"] = f"Bearer {tok}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=20) as r:
        return json.load(r)


def fetch_stats():
    """Stars / repos / release downloads across the user + orgs, plus crates.io downloads."""
    try:
        gh = "https://api.github.com"
        owners = [f"users/{USER}"] + [f"orgs/{u.rstrip('/').rsplit('/', 1)[1]}" for _, u in ORGS]
        repos = [r for o in owners for r in get(f"{gh}/{o}/repos?per_page=100&type=public") if not r["fork"]]
        rel = sum(a["download_count"] for r in repos
                  for rl in get(f"{gh}/repos/{r['full_name']}/releases?per_page=100") for a in rl["assets"])
        uid = get(f"https://crates.io/api/v1/users/{USER}")["user"]["id"]
        crates = get(f"https://crates.io/api/v1/crates?user_id={uid}&per_page=100")["crates"]
        return {"stars": sum(r["stargazers_count"] for r in repos), "repos": len(repos),
                "downloads": rel + sum(c["downloads"] for c in crates) + EXTRA_DOWNLOADS,
                "crates": len(crates), "followers": get(f"{gh}/users/{USER}")["followers"]}
    except Exception as e:  # offline / rate-limited: keep the README buildable
        print("stats fetch failed, using fallback:", e)
        return STATS_FALLBACK


def stats_card(st):
    W, H = 1200, 170
    tiles = [("星", "stars", st["stars"]), ("荷", "downloads", st["downloads"]), ("蔵", "public repos", st["repos"]),
             ("箱", "crates published", st["crates"]), ("友", "followers", st["followers"])]
    tw = (W - 40 - 4 * 16) / 5
    b = [f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="url(#washi)" stroke="#e4d5b5"/>']
    for i, (k, label, n) in enumerate(tiles):
        x = 20 + i * (tw + 16)
        b.append(f'<rect x="{x:.0f}" y="20" width="{tw:.0f}" height="130" rx="10" fill="#fffdf7" stroke="#eadcbc"/>'
                 f'<g class="seal" style="animation-delay:-{i * .7:.1f}s"><rect x="{x + tw / 2 - 20:.0f}" y="34" width="40" height="40" rx="6" fill="{VERMILION}"/>'
                 f'<text x="{x + tw / 2:.0f}" y="62" text-anchor="middle" font-family="{SERIF}" font-size="22" font-weight="700" fill="#fbe9e2">{k}</text></g>'
                 f'<text x="{x + tw / 2:.0f}" y="112" text-anchor="middle" font-family="{SERIF}" font-size="32" font-weight="700" fill="{INK}">{n:,}</text>'
                 f'<path class="brush" style="animation-delay:-{i * .9:.1f}s" d="M{x + tw / 2 - 34:.0f},{121} C{x + tw / 2 - 10:.0f},118 {x + tw / 2 + 10:.0f},124 {x + tw / 2 + 34:.0f},120" '
                 f'stroke="{VERMILION}" stroke-width="2.5" fill="none" stroke-linecap="round" pathLength="1"/>'
                 f'<text x="{x + tw / 2:.0f}" y="140" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{INK2}">{label}</text>')
    css = (".brush{stroke-dasharray:1;animation:draw 7s ease-in-out infinite}@keyframes draw{0%{stroke-dashoffset:1;opacity:.85}25%,88%{stroke-dashoffset:0;opacity:.85}100%{stroke-dashoffset:0;opacity:0}}"
           ".seal{transform-box:fill-box;transform-origin:center;animation:bob 4s ease-in-out infinite}@keyframes bob{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(4deg) translateY(-2px)}}")
    return svg(W, H, "".join(b), css, f"{st['stars']} stars · {st['downloads']} downloads · {st['repos']} public repos · {st['crates']} crates · {st['followers']} followers",
               lg("washi", [(0, "#fffaf0"), (1, "#f5ecd9")], 1, 0))


# ─────────────────────────── README ────────────────────────────
def shield(label, color, logo="", style="flat-square", logo_color="white"):
    lab = quote(label.replace("-", "--").replace("_", "__"), safe="")
    q = f"style={style}" + (f"&logo={logo}&logoColor={logo_color}" if logo else "")
    return f'<img src="https://img.shields.io/badge/{lab}-{color}?{q}" alt="{escape(label)}" />'


def readme():
    socials = "\n".join(f'<a href="{u}">{shield(l, c, logo, "for-the-badge")}</a>' for l, logo, c, u in SOCIALS)
    orgs = "\n".join(f'<a href="{u}">{shield("GitHub · " + l, "24292F", "github", "for-the-badge")}</a>' for l, u in ORGS)
    cells = [f'<td width="50%" valign="top" align="center">\n<h4>{k} &nbsp;·&nbsp; {escape(t)}</h4>\n'
             + "\n".join(shield(l, c, logo) for l, logo, c in items) + "\n<br/><br/>\n</td>" for k, t, items in SKILLS]
    skills = "<table>\n" + "".join(f"<tr>\n{cells[i]}\n{cells[i + 1]}\n</tr>\n" for i in range(0, len(cells), 2)) + "</table>"
    return f"""<!-- generated by build.py — edit the DATA section there and re-run -->
<div align="center">

<img src="./assets/header.svg" alt="{NAME} — {escape(ROLE)}" width="100%" />

{socials}

{orgs}

</div>

<img src="./assets/sec-about.svg" alt="About" width="100%" />

AI Engineer with a background in **low-power and low-bit inference**: squeezing models onto whatever silicon is in front of me, optimised for latency or power, from **GB200 racks** down to **low-power embedded boards**.

I also build the layer between raw data and the AI that reasons over it: **entity resolution, knowledge graphs, RAG and MCP tooling**, plus the pipelines, CI/CD and infrastructure to run them in production. I'm comfortable sitting with domain experts and turning their knowledge into explicit, testable definitions.

I care about the parts most people skip: **profiling, kernels, portability across heterogeneous back-ends, and reproducibility.**

- 🏯 **Now:** AI Performance Engineer at [ZAL Analytics](https://www.zal-analytics.ch) — air-gapped AI & data intelligence
- 🔩 **Also:** building with [Compressor Systems Holland](https://github.com/Compressor-Systems-Holland-B-V)
- 🌍 Dutch citizen · 5+ years across NL, CH, FR, BE and NO
- 🗣️ English · Dutch · French · German
- 🎓 MSc Data Science · BSc Technical Informatics

<img src="./assets/sec-skills.svg" alt="Skills" width="100%" />

{skills}

<img src="./assets/sec-journey.svg" alt="Journey" width="100%" />

<img src="./assets/journey.svg" alt="Career: {' → '.join(j[0] for j in JOURNEY)}" width="100%" />

<img src="./assets/sec-stats.svg" alt="Stats" width="100%" />

<img src="./assets/stats.svg" alt="Stars, downloads, repositories, crates and followers" width="100%" />

<p align="center">
<img src="https://streak-stats.demolab.com/?user={USER}&hide_border=true&background=FBF6EC&ring=C0392B&fire=C0392B&currStreakLabel=C0392B&sideLabels=22303C&currStreakNum=22303C&sideNums=22303C&dates=55606B&stroke=E4D5B5&border_radius=12" alt="GitHub streak" width="60%" />
</p>

<div align="center">

<img src="./assets/footer.svg" alt="Thanks for visiting" width="100%" />

<img src="https://komarev.com/ghpvc/?username={USER}&style=flat-square&color=c0392b&label=visitors" alt="profile views" />

</div>
"""


if __name__ == "__main__":
    files = {
        "header": header(), "journey": journey(), "footer": footer(),
        "sec-about": banner("己", "About me", "$ whoami"),
        "sec-skills": banner("技", "Skills & Tools", "$ ls ~/stack"),
        "sec-journey": banner("道", "Journey", "$ git log --oneline career"),
        "sec-stats": banner("統", "GitHub stats", "$ git stats"),
    }
    files["stats"] = stats_card(fetch_stats())
    files["linkedin-banner"] = header(linkedin=True)  # last: keeps the shared rng sequence of the other assets unchanged
    for old in ASSETS.glob("*.svg"):
        old.unlink()
    for name, content in files.items():
        (ASSETS / f"{name}.svg").write_text(content, encoding="utf-8")
    (OUT / "README.md").write_text(readme(), encoding="utf-8")
    print("wrote", len(files), "svgs + README.md")
