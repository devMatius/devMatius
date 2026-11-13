"""Gera os cards SVG do README do perfil (tema oriental / japonês).

Tudo o que aparece no README sai daqui: os SVGs em cards/ e o próprio README.md.
Edite textos, links e cores no bloco CONFIG abaixo e rode:

    python scripts/render_cards.py           # dados reais (precisa de GITHUB_TOKEN)
    python scripts/render_cards.py --demo    # dados fictícios, só para pré-visualizar

Por que SVG: o GitHub remove CSS/JS do Markdown, mas renderiza SVG como imagem.
Dentro de um <img> o navegador bloqueia recursos externos, então as fontes são
baixadas do Google Fonts já recortadas (parâmetro text=) e embutidas em base64.
Animações são CSS @keyframes + SMIL; nada de JavaScript. Só usa a stdlib.
"""
from __future__ import annotations

import base64
import datetime as dt
import html
import json
import os
import random
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

# ───────────────────────────── CONFIG ─────────────────────────────
CONFIG = {
    "login": "devmatzz",  # sobrescrito por GITHUB_LOGIN ou GITHUB_REPOSITORY_OWNER
    "name": "Matheus",
    "role": "Analista de Suporte",
    "tagline": ("Resolvo problemas com ", "tecnologia, IA e automação", "."),
    "pills": ["Suporte · IA · Automação", "Brasil · UTC-3"],
    "prompt": ("matheus@souza", "~", "automate --one-step-at-a-time"),
    "vertical": "一歩ずつ",  # "um passo de cada vez", escrito na vertical
    "seal": "匠",  # carimbo hanko: "artesão"
    "about": [
        "Sou um jovem de **24 anos** atuando na área de tecnologia há cerca de **4 anos**, "
        "e amante de **Inteligências Artificiais e Automações**.",
    ],
    "about_rows": [  # opcional: ("chave", "valor") em linhas abaixo do texto
    ],
    "links": [
        # (arquivo, rótulo, valor exibido, url, kanji decorativo)
        ("github", "GitHub", "@devmatzz", "https://github.com/devmatzz", "庫"),
        ("linkedin", "LinkedIn", "/in/matheusdssouza", "https://www.linkedin.com/in/matheusdssouza/", "縁"),
        ("email", "Email", "matheusmsms93@gmail.com", "mailto:matheusmsms93@gmail.com", "文"),
    ],
    "footer": "Brasil",
}

# Paleta: sumi (tinta), washi (papel), shu (vermelhão), kin (ouro)
BG = "#0b0908"
CARD = "#12100e"
LINE = "rgba(242,232,216,.10)"
LINE2 = "rgba(242,232,216,.06)"
WASHI = "#f2e8d8"
MUTED = "#9d9385"
DIM = "#6b635a"
SHU = "#e0452b"
KIN = "#c9a35a"
SAKURA = "#f4b3c2"
MATCHA = "#8fa86a"
AI = "#5b7fb5"  # índigo
HEAT = ["#1c1815", "#47201a", "#7a2b1e", "#b23a24", SHU]
LANG_COLORS = [SHU, KIN, AI, MATCHA, SAKURA, "#9a86c9", "#7d746a"]

FONTS = {  # papel → (família no Google Fonts, peso)
    "serif": ("Shippori Mincho", 700),
    "sans": ("Zen Kaku Gothic New", 400),
    "sansb": ("Zen Kaku Gothic New", 700),
    "mono": ("IBM Plex Mono", 400),
}
MONO_ADV = 0.6  # IBM Plex Mono: avanço fixo de 600/1000 em

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cards"
DATA = ROOT / "data" / "github.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# ───────────────────────────── texto e fontes ─────────────────────────────
_used: dict[str, set[str]] = defaultdict(set)
_font_cache: dict[tuple[str, str], list[str]] = {}


def t(role: str, s: str) -> str:
    """Registra os caracteres usados por papel (para recortar a fonte) e escapa."""
    _used[role].update(s)
    return html.escape(s, quote=False)


def mono_w(s: str, size: float) -> float:
    return len(s) * size * MONO_ADV


def approx_w(s: str, size: float, bold: bool = False) -> float:
    """Largura estimada para fontes proporcionais (só para quebra de linha)."""
    w = 0.0
    for ch in s:
        if ord(ch) > 0x2E80:
            w += 1.0
        elif ch == " ":
            w += 0.28
        elif ch in "mwMW@":
            w += 0.82
        elif ch in "il.,;:'!|ftj":
            w += 0.3
        elif ch.isupper():
            w += 0.66
        else:
            w += 0.54
    return w * size * (1.04 if bold else 1.0)


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def font_faces(role: str, chars: str) -> list[str]:
    key = (role, chars)
    if key in _font_cache:
        return _font_cache[key]
    family, weight = FONTS[role]
    q = urllib.parse.urlencode({"family": f"{family}:wght@{weight}", "text": chars, "display": "block"})
    css = _fetch(f"https://fonts.googleapis.com/css2?{q}").decode()
    urls = re.findall(r"url\((https://[^)]+)\)\s*format\('woff2'\)", css)
    if not urls:
        raise RuntimeError(f"Google Fonts não devolveu woff2 para {family} {weight}")
    faces = []
    for u in urls:
        b64 = base64.b64encode(_fetch(u)).decode()
        faces.append(f"@font-face{{font-family:'k-{role}';src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    _font_cache[key] = faces
    return faces


def font_css() -> str:
    out = []
    for role, chars in sorted(_used.items()):
        out += font_faces(role, "".join(sorted(chars)))
    return "\n".join(out)


BASE_CSS = f"""
.s{{font-family:'k-serif','Hiragino Mincho ProN','Yu Mincho',serif}}
.g{{font-family:'k-sans','Hiragino Sans','Yu Gothic',sans-serif}}
.gb{{font-family:'k-sansb','Hiragino Sans','Yu Gothic',sans-serif;font-weight:700}}
.m{{font-family:'k-mono',ui-monospace,Menlo,Consolas,monospace}}
.fade{{animation:fade .8s ease both}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
.rise{{animation:rise .9s cubic-bezier(.2,.8,.2,1) both}}
@keyframes rise{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
.pop{{transform-box:fill-box;transform-origin:center;animation:pop .5s cubic-bezier(.2,.8,.2,1) both}}
@keyframes pop{{from{{opacity:0;transform:scale(.4)}}to{{opacity:1;transform:none}}}}
.grow{{transform-box:fill-box;transform-origin:bottom;animation:grow 1s cubic-bezier(.2,.8,.2,1) both}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
.growx{{transform-box:fill-box;transform-origin:left;animation:growx .9s cubic-bezier(.2,.8,.2,1) both}}
@keyframes growx{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
.stamp{{transform-box:fill-box;transform-origin:center;animation:stamp .55s cubic-bezier(.3,1.6,.5,1) both}}
@keyframes stamp{{from{{opacity:0;transform:scale(1.8) rotate(-12deg)}}to{{opacity:1;transform:rotate(-4deg)}}}}
.petal{{transform-box:fill-box;transform-origin:center;animation:fall linear infinite}}
@keyframes fall{{0%{{transform:translate(0,-40px) rotate(0);opacity:0}}10%{{opacity:.9}}
 90%{{opacity:.8}}100%{{transform:translate(-90px,340px) rotate(540deg);opacity:0}}}}
.mist{{animation:mist 14s ease-in-out infinite alternate}}
@keyframes mist{{from{{transform:translateX(-20px)}}to{{transform:translateX(30px)}}}}
.ring{{transform-box:fill-box;transform-origin:center;animation:ring 2.4s ease-out infinite}}
@keyframes ring{{0%{{transform:scale(1);opacity:.7}}70%,100%{{transform:scale(2.6);opacity:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def d(sec: float) -> str:
    return f'style="animation-delay:{sec:.2f}s"'


def card_bg(w: float, h: float) -> str:
    return f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="14" fill="{CARD}" stroke="{LINE}"/>'


def seigaiha(pid: str, color: str = WASHI) -> str:
    """Padrão de ondas seigaiha (青海波). Ordem de desenho: linhas de cima para baixo."""
    def wave(cx, cy):
        rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{CARD if r == 20 else "none"}" stroke="{color}" stroke-width=".8"/>' for r in (20, 15, 10, 5))
        return rings
    body = wave(20, 0) + wave(0, 10) + wave(40, 10) + wave(20, 20) + wave(0, 30) + wave(40, 30)
    return f'<pattern id="{pid}" width="40" height="20" patternUnits="userSpaceOnUse">{body}</pattern>'


def section_head(x: float, y: float, num: str, title: str, kanji: str) -> str:
    return (f'<text x="{x}" y="{y}" class="s fade" font-size="15" fill="{SHU}">{t("serif", num)}</text>'
            f'<text x="{x+26}" y="{y}" class="gb fade" font-size="15" fill="{WASHI}" {d(.05)}>{t("sansb", title)}</text>'
            f'<text x="{x+26+approx_w(title, 15, True)+10}" y="{y}" class="s fade" font-size="13" fill="{DIM}" {d(.1)}>{t("serif", kanji)}</text>')


def svg_doc(w: float, h: float, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
            f'<style>{font_css()}{BASE_CSS}</style>{body}</svg>')


def typing_clip(uid: str, x: float, y_top: float, h: float, text: str, size: float, begin: float, dur: float) -> str:
    steps = ";".join(f"{mono_w(text[:i], size):.1f}" for i in range(len(text) + 1))
    return (f'<defs><clipPath id="{uid}"><rect x="{x}" y="{y_top}" width="0" height="{h}">'
            f'<animate attributeName="width" values="{steps}" calcMode="discrete" begin="{begin}s" dur="{dur}s" fill="freeze"/>'
            f'</rect></clipPath></defs>')


# ───────────────────────────── dados ─────────────────────────────
QUERY = """query($login:String!){user(login:$login){
 repositories(ownerAffiliations:OWNER,isFork:false,first:100,orderBy:{field:PUSHED_AT,direction:DESC}){
  nodes{languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}"""


def fetch_data(login: str) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN não definido. Use --demo para pré-visualizar com dados fictícios.")
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-cards"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    if res.get("errors") or not res.get("data", {}).get("user"):
        raise RuntimeError(f"GraphQL falhou: {res.get('errors')}")
    langs: dict[str, int] = defaultdict(int)
    for repo in res["data"]["user"]["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] += e["size"]
    return {"languages": dict(langs), "demo": False,
            "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def demo_data() -> dict:
    """Dados fictícios, só para pré-visualizar o layout (marcados como demo no card)."""
    langs = {"Python": 420_000, "C#": 310_000, "TSQL": 190_000, "JavaScript": 90_000, "PowerShell": 40_000, "HTML": 20_000, "Shell": 9_000}
    return {"languages": langs, "demo": True, "generated": "demo"}


def stats(data: dict) -> dict:
    total = sum(data["languages"].values()) or 1
    langs = sorted(data["languages"].items(), key=lambda x: -x[1])
    top = [(k, v / total) for k, v in langs[:6]]
    rest = sum(v for _, v in langs[6:]) / total
    if rest > 0.001:
        top.append(("Other", rest))
    return {"langs": top, "demo": data["demo"]}

# ───────────────────────────── cards ─────────────────────────────
def torii(cx: float, base: float) -> str:
    """Torii estilo myōjin: kasagi curvo, shimaki, nuki com cunhas, placa e pilares inclinados."""
    T = base - 138
    dk = "#96281a"  # vermelhão escuro (sombra)
    g = []
    for sgn in (-1, 1):
        xt, xb = cx + sgn * 50, cx + sgn * 57
        g.append(f'<polygon points="{xt-5.5},{T+20} {xt+5.5},{T+20} {xb+7},{base-7} {xb-7},{base-7}" fill="{SHU}"/>')
        g.append(f'<polygon points="{xt},{T+20} {xt+5.5},{T+20} {xb+7},{base-7} {xb},{base-7}" fill="#000" opacity=".2"/>')
        g.append(f'<polygon points="{xb-8},{base-9} {xb+8},{base-9} {xb+10},{base} {xb-10},{base}" fill="#453c36"/>')
    g.append(f'<rect x="{cx-80}" y="{T+52}" width="160" height="9" fill="{SHU}"/>')
    g.append(f'<rect x="{cx-80}" y="{T+59}" width="160" height="2" fill="#000" opacity=".22"/>')
    for sgn in (-1, 1):
        g.append(f'<rect x="{cx + sgn*62 - 2}" y="{T+50}" width="4" height="13" fill="{dk}"/>')
    g.append(f'<rect x="{cx-5}" y="{T+24}" width="10" height="28" fill="{SHU}"/>')
    g.append(f'<rect x="{cx-9}" y="{T+29}" width="18" height="18" rx="1.5" fill="#1d0f0c" stroke="{KIN}" stroke-width=".9"/>')
    g.append(f'<path d="M{cx-90},{T+9.5} Q{cx},{T+20.5} {cx+90},{T+9.5} L{cx+87},{T+19} Q{cx},{T+29} {cx-87},{T+19} Z" fill="{SHU}"/>')
    g.append(f'<path d="M{cx-98},{T} Q{cx},{T+13} {cx+98},{T} L{cx+94},{T+10} Q{cx},{T+21} {cx-94},{T+10} Z" fill="{dk}"/>')
    g.append(f'<path d="M{cx-97},{T+.8} Q{cx},{T+13.8} {cx+97},{T+.8}" fill="none" stroke="{KIN}" stroke-opacity=".7" stroke-width="1.2"/>')
    return f'<g class="rise" {d(.6)}>{"".join(g)}</g>'


def scenery(cx: float, base: float) -> str:
    """Sol do entardecer, montanhas em camadas, pássaros e caminho de pedra até o torii."""
    out = [f'<circle cx="{cx}" cy="{base-105}" r="100" fill="url(#sun)" class="fade" {d(.2)}/>',
           f'<circle cx="{cx}" cy="{base-105}" r="56" fill="url(#sunf)" class="pop" {d(.35)}/>']
    far = f"M{cx-140},{base} l50,-35 l28,11 l44,-38 l30,18 l48,-28 l48,38 l41,-16 V{base} Z"
    near = f"M{cx-175},{base} l55,-18 l50,10 l60,-18 l50,16 l50,-14 l59,12 V{base} Z"
    out.append(f'<g clip-path="url(#cc)" class="fade" {d(.3)}><path d="{far}" fill="#2a1f1b"/><path d="{near}" fill="#1c1513"/></g>')
    for bx, by, sc in ((cx - 62, base - 152, 1), (cx - 44, base - 164, .7), (cx + 70, base - 170, .8)):
        out.append(f'<path class="fade" {d(1.2)} transform="translate({bx},{by}) scale({sc})" d="M-7,0 q3.5,-5 7,0 q3.5,-5 7,0" '
                   f'fill="none" stroke="#3b2621" stroke-width="1.6" stroke-linecap="round"/>')
    path = f'<polygon points="{cx-24},{base+1} {cx+24},{base+1} {cx+66},300 {cx-66},300" fill="{WASHI}" opacity=".05"/>'
    for yy in (base + 12, base + 28, base + 46):
        half = 24 + (yy - base) * .7
        path += f'<line x1="{cx-half:.0f}" x2="{cx+half:.0f}" y1="{yy}" y2="{yy}" stroke="{WASHI}" stroke-opacity=".09"/>'
    out.append(f'<g clip-path="url(#cc)" class="fade" {d(.8)}>{path}</g>')
    return "".join(out)


PETAL = "M0,-5 C4,-6 6,-1 2,4 L0,2.5 L-2,4 C-6,-1 -4,-6 0,-5 Z"


def petals(n: int, x0: float, x1: float, seed: int) -> str:
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x = rnd.uniform(x0, x1)
        s = rnd.uniform(.7, 1.3)
        dur = rnd.uniform(7, 12)
        delay = -rnd.uniform(0, 12)
        out.append(f'<g transform="translate({x:.0f},0) scale({s:.2f})"><path class="petal" d="{PETAL}" fill="{SAKURA}" '
                   f'opacity=".85" style="animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s"/></g>')
    return "".join(out)


BARK = "#3b2621"
BLOSSOM = [SAKURA, "#f9d3dc", "#e98ca3", "#fbe4ea"]


def sakura_tree() -> str:
    """Cerejeira: tronco e galhos em traço de tinta, copa feita de cachos de flores."""
    trunk = ('M506,240 C514,214 510,196 520,176 C526,160 538,150 552,140 L557,146 '
             'C545,156 535,168 531,182 C525,202 528,220 536,240 Z')
    branches = [  # (path, espessura)
        ("M528,182 C506,166 484,152 462,126", 5), ("M548,146 C572,128 594,112 626,98", 4),
        ("M538,156 C538,124 530,102 518,80", 4), ("M478,146 C470,132 458,124 448,112", 2),
        ("M588,118 C594,106 598,96 604,86", 2), ("M522,92 C532,82 540,76 550,68", 2),
        ("M498,160 C488,166 476,170 466,170", 2),
    ]
    g = [f'<path d="{trunk}" fill="{BARK}"/>']
    g += [f'<path d="{p}" fill="none" stroke="{BARK}" stroke-width="{sw}" stroke-linecap="round"/>' for p, sw in branches]
    anchors = [(462, 122), (448, 108), (480, 140), (468, 168), (518, 76), (548, 64), (498, 98), (530, 110), (570, 122),
               (604, 84), (626, 96), (646, 104), (488, 70), (566, 94), (506, 130), (590, 140), (440, 136)]
    rnd = random.Random(11)
    blossoms = []
    for i, (ax, ay) in enumerate(anchors):
        dots = "".join(
            f'<circle cx="{ax + rnd.uniform(-15, 15):.0f}" cy="{ay + rnd.uniform(-11, 11):.0f}" r="{rnd.uniform(4, 9):.1f}" '
            f'fill="{rnd.choice(BLOSSOM)}" opacity="{rnd.uniform(.7, .95):.2f}"/>' for _ in range(8))
        blossoms.append(f'<g class="pop" {d(.5 + i * .05)}>{dots}</g>')
    shadow = f'<ellipse cx="520" cy="241" rx="60" ry="4" fill="{SAKURA}" opacity=".12"/>'
    return f'<g class="rise" {d(.3)}>{shadow}{"".join(g)}</g>' + "".join(blossoms)


def hero() -> str:
    w, h = 880, 300
    b = [card_bg(w, h), f'<defs>{seigaiha("sg")}<radialGradient id="sun"><stop offset="0" stop-color="{SHU}" stop-opacity=".35"/>'
         f'<stop offset=".7" stop-color="{SHU}" stop-opacity=".12"/><stop offset="1" stop-color="{SHU}" stop-opacity="0"/></radialGradient>'
         f'<linearGradient id="sunf" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#f8e0b4"/><stop offset="1" stop-color="#ea8a5c"/></linearGradient>'
         f'<clipPath id="cc"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14"/></clipPath>'
         f'<linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="{CARD}"/><stop offset=".55" stop-color="{CARD}" stop-opacity="0"/></linearGradient>'
         f'<linearGradient id="fadeT" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{CARD}"/><stop offset="1" stop-color="{CARD}" stop-opacity="0"/></linearGradient></defs>']
    # ondas seigaiha no rodapé direito, sumindo para a esquerda e para cima
    b.append(f'<g clip-path="url(#cc)"><rect x="440" y="230" width="440" height="70" fill="url(#sg)" opacity=".22"/>'
             f'<rect x="440" y="230" width="440" height="70" fill="url(#fadeL)"/>'
             f'<rect x="440" y="229" width="440" height="22" fill="url(#fadeT)"/></g>')
    # sol, névoa, torii e cerejeira
    b.append(scenery(730, 240))
    b.append(torii(730, 240))
    b.append(sakura_tree())
    b.append(f'<line x1="460" y1="240" x2="836" y2="240" stroke="{KIN}" stroke-opacity=".5" class="fade" {d(.7)}/>')
    for y, x, wid, op in ((178, 610, 150, .07), (205, 470, 170, .06)):
        b.append(f'<rect class="mist" x="{x}" y="{y}" width="{wid}" height="8" rx="4" fill="{WASHI}" opacity="{op}"/>')
    # texto vertical + hanko
    for i, ch in enumerate(CONFIG["vertical"]):
        b.append(f'<text x="846" y="{62 + i*24}" text-anchor="middle" class="s fade" font-size="18" fill="{MUTED}" {d(1.6 + i*.12)}>{t("serif", ch)}</text>')
    sy = 62 + len(CONFIG["vertical"]) * 24 - 6
    b.append(f'<g class="stamp" {d(2.3)}><rect x="830" y="{sy}" width="32" height="32" rx="4" fill="{SHU}"/>'
             f'<rect x="833" y="{sy+3}" width="26" height="26" rx="2" fill="none" stroke="{CARD}" stroke-opacity=".5"/>'
             f'<text x="846" y="{sy+24}" text-anchor="middle" class="s" font-size="20" fill="{CARD}">{t("serif", CONFIG["seal"])}</text></g>')
    # pílulas
    x = 44
    for i, text in enumerate(CONFIG["pills"]):
        dot = i == 0
        pw = mono_w(text, 12) + (40 if dot else 24)
        g = f'<rect x="{x+.5}" y="40.5" width="{pw:.1f}" height="27" rx="13.5" fill="none" stroke="rgba(242,232,216,.18)"/>'
        tx = x + 12
        if dot:
            g += (f'<circle cx="{x+16}" cy="54" r="3.5" fill="{MATCHA}"/>'
                  f'<circle class="ring" cx="{x+16}" cy="54" r="3.5" fill="none" stroke="{MATCHA}"/>')
            tx = x + 28
        g += f'<text x="{tx}" y="58" class="m" font-size="12" fill="{WASHI}">{t("mono", text)}</text>'
        b.append(f'<g class="fade" {d(.05 + i*.1)}>{g}</g>')
        x += pw + 8
    # nome revelado como uma pincelada (máscara que varre da esquerda)
    b.append(f'<defs><linearGradient id="brush" x1="0" x2="1"><stop offset=".85" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
             f'<mask id="nm"><rect x="30" y="80" height="90" width="0" fill="url(#brush)">'
             f'<animate attributeName="width" from="0" to="560" begin=".4s" dur="1.3s" fill="freeze" keySplines=".3 .7 .2 1" keyTimes="0;1" calcMode="spline"/></rect></mask></defs>')
    b.append(f'<text x="42" y="150" mask="url(#nm)" class="s" font-size="68" letter-spacing="-1" fill="{WASHI}">{t("serif", CONFIG["name"])}</text>')
    b.append(f'<rect x="44" y="166" width="56" height="3" fill="{SHU}" class="growx" {d(1.5)}/>')
    b.append(f'<text x="44" y="202" class="g rise" font-size="16" fill="{MUTED}" {d(1.6)}>{t("sans", CONFIG["role"])}</text>')
    a, bold, c = CONFIG["tagline"]
    b.append(f'<text x="44" y="232" font-size="16" class="rise" {d(1.75)}><tspan class="g" fill="{MUTED}">{t("sans", a)}</tspan>'
             f'<tspan class="gb" fill="{WASHI}">{t("sansb", bold)}</tspan><tspan class="g" fill="{MUTED}">{t("sans", c)}</tspan></text>')
    # prompt de terminal digitando
    user, path, cmd = CONFIG["prompt"]
    pre = f"{user}:{path}$ "
    cx = 44 + mono_w(pre, 12)
    b.append(f'<text x="44" y="270" class="m fade" font-size="12" {d(2.0)}><tspan fill="{MATCHA}">{t("mono", user)}</tspan>'
             f'<tspan fill="{DIM}">:</tspan><tspan fill="{AI}">{t("mono", path)}</tspan><tspan fill="{DIM}">$ </tspan></text>')
    b.append(typing_clip("tc", cx, 255, 22, cmd, 12, 2.3, len(cmd) * .05))
    b.append(f'<g clip-path="url(#tc)"><text x="{cx}" y="270" class="m" font-size="12" fill="{SHU}">{t("mono", cmd)}</text></g>')
    cur_end = cx + mono_w(cmd, 12) + 2
    b.append(f'<rect x="{cur_end:.1f}" y="259" width="7" height="14" fill="{SHU}" opacity="0">'
             f'<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1s" begin="{2.3 + len(cmd)*.05:.2f}s" repeatCount="indefinite"/></rect>')
    b.append(f'<g clip-path="url(#cc)">{petals(14, 420, 900, 3)}</g>')
    return svg_doc(w, h, "".join(b))


def rich_wrap(text: str, max_w: float, size: float) -> list[list[tuple[str, bool]]]:
    """Quebra texto com **negrito** em linhas. Cada token já carrega o espaço que o segue,
    então pontuação colada ao negrito ("**x**.") não ganha espaço extra."""
    tokens: list[tuple[str, bool]] = []
    for i, part in enumerate(text.split("**")):
        if part[:1].isspace() and tokens:  # espaço logo após o fechamento do negrito
            tokens[-1] = (tokens[-1][0].rstrip() + " ", tokens[-1][1])
        for m in re.finditer(r"\S+\s*", part):
            tokens.append((m.group(), i % 2 == 1))
    lines, cur, cur_w = [], [], 0.0
    for word, bold in tokens:
        ww = approx_w(word, size, bold)
        if cur and cur_w + ww > max_w and cur[-1][0].endswith(" "):
            lines.append(cur)
            cur, cur_w = [], 0.0
        cur.append((word, bold))
        cur_w += ww
    if cur:
        lines.append(cur)
    return [[(w.rstrip() if j == len(ln) - 1 else w, b) for j, (w, b) in enumerate(ln)] for ln in lines]


def about() -> str:
    w = 880
    size, lh, col = 17, 30, 500
    paras = [rich_wrap(p, col, size) for p in CONFIG["about"]]
    y = 70
    body = []
    delay = .2
    for lines in paras:
        for ln in lines:
            spans = ""
            for word, bold in ln:
                role = "sansb" if bold else "sans"
                spans += f'<tspan class="{"gb" if bold else "g"}" fill="{WASHI if bold else MUTED}">{t(role, word)}</tspan>'
            body.append(f'<text x="44" y="{y}" font-size="{size}" class="rise" {d(delay)}>{spans}</text>')
            y += lh
            delay += .06
        y += 10
    y += 4
    for i, (k, v) in enumerate(CONFIG["about_rows"]):
        body.append(f'<line x1="44" x2="{44+col}" y1="{y-16}" y2="{y-16}" stroke="{LINE2}"/>')
        body.append(f'<g class="fade" {d(delay + i*.1)}><text x="44" y="{y+2}" class="m" font-size="11" fill="{SHU}">{t("mono", "→ " + k)}</text>'
                    f'<text x="190" y="{y+2}" class="g" font-size="13.5" fill="{WASHI}">{t("sans", v)}</text></g>')
        y += 34
    h = max(y + 10, 280)
    # lago dentro de um ensō (円相): duas carpas koi nadando em círculo, vitórias-régias e ondulações
    ex, ey, r = 705, h / 2 - 4, 100
    circ = 2 * 3.14159 * r
    pond = (f'<defs><radialGradient id="pond"><stop offset="0" stop-color="#1b3147"/><stop offset="1" stop-color="#0e1a24"/></radialGradient>'
            f'<clipPath id="pc"><circle cx="{ex}" cy="{ey}" r="{r-7}"/></clipPath></defs>'
            f'<circle cx="{ex}" cy="{ey}" r="{r-7}" fill="url(#pond)" class="fade" {d(.3)}/>')
    for i in range(3):
        pond += (f'<circle cx="{ex}" cy="{ey}" r="6" fill="none" stroke="{WASHI}" stroke-opacity=".2">'
                 f'<animate attributeName="r" values="4;{r-10}" dur="7.5s" begin="{i*2.5}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="stroke-opacity" values=".28;0" dur="7.5s" begin="{i*2.5}s" repeatCount="indefinite"/></circle>')
    orbit = 50
    fish = ""
    for i, (kid, body_c, patch_c) in enumerate((("k1", "#f6efe2", SHU), ("k2", "#e2ab46", "#f6efe2"))):
        sx = ex + (orbit if i == 0 else -orbit)
        ox = ex - orbit if i == 0 else ex + orbit
        path = f"M{sx},{ey} A{orbit},{orbit} 0 1,1 {ox},{ey} A{orbit},{orbit} 0 1,1 {sx},{ey}"
        fish += (f'<g class="fade" {d(1.2 + i*.3)}><g>{koi(kid, body_c, patch_c)}'
                 f'<animateMotion path="{path}" dur="18s" repeatCount="indefinite" rotate="auto"/></g></g>')
    pond += f'<g clip-path="url(#pc)">{fish}</g>'
    for px, py, pr, rot, flower in ((ex + 62, ey - 52, 11, 30, True), (ex + 74, ey - 30, 7, 200, False), (ex - 70, ey + 46, 10, 120, False)):
        pond += f'<g class="pop" {d(1.6)}>{lily_pad(px, py, pr, rot, flower)}</g>'
    enso = (f'<circle cx="{ex}" cy="{ey}" r="{r}" fill="none" stroke="{WASHI}" stroke-opacity=".88" stroke-width="11" stroke-linecap="round" '
            f'transform="rotate(-70 {ex} {ey})" stroke-dasharray="{circ*.9:.0f} {circ:.0f}" stroke-dashoffset="{circ*.9:.0f}">'
            f'<animate attributeName="stroke-dashoffset" from="{circ*.9:.0f}" to="0" dur="1.6s" begin=".4s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".5 0 .2 1"/></circle>')
    enso += f'<text x="{ex}" y="{ey+r+26}" text-anchor="middle" class="m fade" font-size="10" fill="{DIM}" {d(1.8)}>{t("mono", "KOI · PERSEVERANCE")}</text>'
    head = section_head(44, 40, "一", "Sobre mim", "自己紹介")
    return svg_doc(w, h, card_bg(w, h) + head + "".join(body) + pond + enso)


def lily_pad(x: float, y: float, r: float, rot: float, flower: bool) -> str:
    pad = (f'<g transform="translate({x},{y}) rotate({rot})"><path d="M0,0 L{r},{-r*.28:.1f} A{r},{r} 0 1,0 {r},{r*.28:.1f} Z" fill="#5f7a48"/>'
           f'<path d="M0,0 L{-r*.8:.1f},0 M0,0 L{-r*.4:.1f},{r*.7:.1f} M0,0 L{-r*.4:.1f},{-r*.7:.1f}" stroke="#7f9a5a" stroke-width=".7" fill="none"/></g>')
    if flower:
        lotus = "".join(f'<ellipse cx="0" cy="-4" rx="2.2" ry="4.4" fill="{c}" transform="rotate({a})"/>'
                        for a, c in ((0, SAKURA), (72, "#f9d3dc"), (144, SAKURA), (216, "#f9d3dc"), (288, SAKURA)))
        pad += f'<g transform="translate({x - 2},{y + 1})">{lotus}<circle r="1.6" fill="{KIN}"/></g>'
    return pad


def koi(uid: str, body_c: str, patch_c: str, s: float = .78) -> str:
    """Carpa koi vista de cima, virada para +x e centrada na origem (animateMotion rotate=auto).
    Como nada em círculo no sentido horário, a cauda já vem curvada para dentro da curva."""
    body = "M35,0 C35,-7 27,-12.5 13,-12.5 C-3,-12.5 -18,-7 -30,-2.2 L-30,2.2 C-18,7 -3,12.5 13,12.5 C27,12.5 35,7 35,0 Z"
    tail = "M-28,0 C-36,-3 -45,-15 -58,-17 C-52,-9 -49,-4 -48,0 C-49,4 -52,9 -58,17 C-45,15 -36,3 -28,0 Z"
    fin_l = "M15,-10 C14,-21 3,-28 -7,-26 C-2,-19 2,-14 5,-10 Z"
    fin_r = "M15,10 C14,21 3,28 -7,26 C-2,19 2,14 5,10 Z"
    pelv_l = "M-10,-9 C-13,-15 -20,-16 -23,-12 C-19,-10 -15,-8 -12,-7 Z"
    pelv_r = "M-10,9 C-13,15 -20,16 -23,12 C-19,10 -15,8 -12,7 Z"

    def rot(vals: str, dur: float) -> str:
        return (f'<animateTransform attributeName="transform" type="rotate" values="{vals}" dur="{dur}s" repeatCount="indefinite" '
                f'calcMode="spline" keyTimes="0;.5;1" keySplines=".4 0 .6 1;.4 0 .6 1"/>')

    fins = (f'<path d="{fin_l}" fill="{body_c}" opacity=".55">{rot("-6 14 -10;8 14 -10;-6 14 -10", 1.5)}</path>'
            f'<path d="{fin_r}" fill="{body_c}" opacity=".55">{rot("6 14 10;-8 14 10;6 14 10", 1.5)}</path>'
            f'<path d="{pelv_l}" fill="{body_c}" opacity=".5"/><path d="{pelv_r}" fill="{body_c}" opacity=".5"/>')
    patches = (f'<g clip-path="url(#{uid})" fill="{patch_c}">'
               '<path d="M33,-3 C28,-12 16,-11 15,-3 C14,4 20,7 26,5 C30,4 34,1 33,-3 Z"/>'
               '<path d="M8,-13 C-4,-14 -12,-6 -8,2 C-5,8 4,6 8,1 C12,-4 12,-10 8,-13 Z"/>'
               '<path d="M-14,4 C-20,2 -26,4 -28,8 L-12,12 C-10,9 -11,6 -14,4 Z"/>'
               '<ellipse cx="-22" cy="-3" rx="5" ry="2.5"/></g>')
    shade = (f'<g clip-path="url(#{uid})"><path d="M30,0 C14,-3.5 -8,-3 -30,0 C-8,3 14,3.5 30,0 Z" fill="#fff" opacity=".28"/>'
             f'<path d="M35,6 C20,14 -8,12 -30,3 L-30,14 L35,14 Z" fill="#000" opacity=".14"/></g>')
    face = ('<circle cx="27.5" cy="-6" r="1.5" fill="#0b0908"/><circle cx="27.5" cy="6" r="1.5" fill="#0b0908"/>'
            f'<path d="M33.5,-2.5 q4,-1.5 5,-5 M33.5,2.5 q4,1.5 5,5" fill="none" stroke="{body_c}" stroke-width=".9" stroke-linecap="round" opacity=".8"/>')
    fish = (f'<defs><clipPath id="{uid}"><path d="{body}"/></clipPath></defs>'
            f'<path d="{tail}" fill="{body_c}" opacity=".7">{rot("-30 -28 0;-4 -28 0;-30 -28 0", 1.5)}</path>'
            f'{fins}<path d="{body}" fill="{body_c}"/>{patches}{shade}{face}')
    shadow = f'<path d="{body}" transform="translate(3,5)" fill="#000" opacity=".3"/>'
    return f'<g transform="scale({s})">{shadow}<g>{rot("3;-3;3", 1.5)}{fish}</g></g>'


def languages(s: dict) -> str:
    w = 880
    langs = s["langs"]
    rows = (len(langs) + 2) // 3
    h = 104 + rows * 30
    b = [card_bg(w, h), section_head(44, 40, "二", "Linguagens", "言語")]
    if s["demo"]:
        b.append(f'<text x="{w-44}" y="40" text-anchor="end" class="m" font-size="11" fill="{SHU}">{t("mono", "DEMO DATA")}</text>')
    x, bw = 44, w - 88
    b.append(f'<rect x="44" y="64" width="{bw}" height="12" rx="6" fill="#1c1815"/>')
    b.append(f'<defs><clipPath id="lb"><rect x="44" y="64" width="{bw}" height="12" rx="6"/></clipPath></defs><g clip-path="url(#lb)">')
    for i, (name, frac) in enumerate(langs):
        sw = bw * frac
        b.append(f'<rect class="growx" {d(.2 + i*.12)} x="{x:.1f}" y="64" width="{max(sw-2, 1):.1f}" height="12" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>')
        x += sw
    b.append("</g>")
    cw = bw / 3
    for i, (name, frac) in enumerate(langs):
        r, c = divmod(i, 3)
        lx, ly = 44 + c * cw, 112 + r * 30
        col = LANG_COLORS[i % len(LANG_COLORS)]
        b.append(f'<g class="fade" {d(.5 + i*.08)}><rect x="{lx}" y="{ly-9}" width="9" height="9" rx="2" fill="{col}"/>'
                 f'<text x="{lx+18}" y="{ly}" class="g" font-size="13.5" fill="{WASHI}">{t("sans", name)}</text>'
                 f'<text x="{lx+cw-24}" y="{ly}" text-anchor="end" class="m" font-size="11.5" fill="{MUTED}">{t("mono", f"{frac*100:.1f}%")}</text></g>')
    return svg_doc(w, h, "".join(b))


def contact_head() -> str:
    w, h = 880, 70
    b = [card_bg(w, h), section_head(44, 41, "三", "Contato", "連絡")]
    b.append(f'<rect x="220" y="35" width="560" height="1" fill="{LINE}" class="growx" {d(.2)}/>')
    b.append(f'<text x="836" y="50" text-anchor="end" class="s fade" font-size="30" fill="{SHU}" opacity=".9" {d(.4)}>{t("serif", "縁")}</text>')
    return svg_doc(w, h, "".join(b))


def link_tile(label: str, value: str, kanji: str, delay: float) -> str:
    w, h = 290, 118
    b = [card_bg(w, h)]
    b.append(f'<text x="{w-18}" y="{h-16}" text-anchor="end" class="s" font-size="70" fill="{WASHI}" opacity=".06">{t("serif", kanji)}</text>')
    b.append(f'<text x="22" y="36" class="m fade" font-size="11" fill="{SHU}" letter-spacing=".8" {d(delay)}>{t("mono", label.upper())}</text>')
    size = 17 if len(value) <= 20 else 14
    b.append(f'<text x="22" y="74" class="g rise" font-size="{size}" fill="{WASHI}" {d(delay + .1)}>{t("sans", value)}</text>')
    b.append(f'<g class="fade" {d(delay + .25)}><line x1="22" x2="58" y1="94" y2="94" stroke="{SHU}" stroke-width="1.5"/>'
             f'<path d="M54,90 L59,94 L54,98" fill="none" stroke="{SHU}" stroke-width="1.5"/></g>')
    return svg_doc(w, h, "".join(b))


def footer() -> str:
    w, h = 880, 96
    b = [card_bg(w, h), f'<defs>{seigaiha("fw")}<clipPath id="fc"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14"/></clipPath></defs>']
    b.append(f'<g clip-path="url(#fc)"><rect x="0" y="0" width="{w}" height="{h}" fill="url(#fw)" opacity=".13"/></g>')
    b.append(f'<rect x="300" y="26" width="280" height="44" rx="22" fill="{CARD}"/>')
    b.append(f'<text x="{w/2}" y="48" text-anchor="middle" class="s fade" font-size="18" fill="{WASHI}" letter-spacing="6">{t("serif", "一期一会")}</text>')
    copy = "© {} {} · {}".format(dt.date.today().year, CONFIG["name"], CONFIG["footer"])
    b.append(f'<text x="{w/2}" y="64" text-anchor="middle" class="m fade" font-size="10" fill="{DIM}" {d(.2)}>'
             f'{t("mono", copy)}</text>')
    return svg_doc(w, h, "".join(b))


# ───────────────────────────── saída ─────────────────────────────
def render(name: str, fn, *args) -> None:
    _used.clear()
    (OUT / f"{name}.svg").write_text(fn(*args), encoding="utf-8")
    print(f"  cards/{name}.svg")


def readme() -> str:
    login = CONFIG["login"]
    links = CONFIG["links"]
    tiles = "".join(f'<a href="{u}"><img width="33.33%" alt="{html.escape(lbl)}: {html.escape(v)}" src="./cards/link-{k}.svg"/></a>'
                    for k, lbl, v, u, _ in links)
    return f"""<!--
  Gerado por scripts/render_cards.py — edite o CONFIG do script, não este arquivo.
  Cards na mesma linha precisam ficar numa linha só, sem espaço entre as tags.
-->

<img width="100%" alt="{CONFIG['name']} — {CONFIG['role']}" src="./cards/hero.svg"/>

<img width="100%" alt="Sobre mim" src="./cards/about.svg"/>

<a href="https://github.com/{login}?tab=repositories"><img width="100%" alt="Linguagens mais usadas" src="./cards/languages.svg"/></a>

<img width="100%" alt="Contato" src="./cards/contact.svg"/>

{tiles}

<img width="100%" alt="© {CONFIG['name']}" src="./cards/footer.svg"/>
"""


def main() -> None:
    demo = "--demo" in sys.argv
    CONFIG["login"] = os.environ.get("GITHUB_LOGIN") or os.environ.get("GITHUB_REPOSITORY_OWNER") or CONFIG["login"]
    if demo:
        print("AVISO: usando dados fictícios (--demo). Não publique estes cards.")
        data = demo_data()
    else:
        try:
            data = fetch_data(CONFIG["login"])
            DATA.parent.mkdir(exist_ok=True)
            DATA.write_text(json.dumps(data), encoding="utf-8")
        except (RuntimeError, OSError) as e:
            if not DATA.exists():
                raise
            print(f"AVISO: API do GitHub falhou ({e}); usando cache de {DATA.name}", file=sys.stderr)
            data = json.loads(DATA.read_text(encoding="utf-8"))
    s = stats(data)
    OUT.mkdir(exist_ok=True)
    render("hero", hero)
    render("about", about)
    render("languages", languages, s)
    render("contact", contact_head)
    for i, (k, lbl, v, _, kanji) in enumerate(CONFIG["links"]):
        render(f"link-{k}", link_tile, lbl, v, kanji, .1 + i * .1)
    render("footer", footer)
    (ROOT / "README.md").write_text(readme(), encoding="utf-8")
    print("  README.md")


if __name__ == "__main__":
    main()
