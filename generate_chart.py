#!/usr/bin/env python3
"""github-candles — daily contribution candlesticks, current month session.
Zero config in Actions: GH_USER auto = repo owner.
"""
import os, json, datetime, urllib.request

GH_USER  = os.environ.get("GH_USER", "octocat")
GH_TOKEN = os.environ.get("GH_TOKEN", "")
OUT      = os.environ.get("OUT", "chart.svg")

# ── Binance-grade palette ─────────────────────────
BG, FRAME   = "#0B0E11", "#1B2130"
GRID, AXIS  = "#161C26", "#242B38"
TEXT, SUB   = "#EAECEF", "#6E7887"
GREEN, RED  = "#0ECB81", "#F6465D"
SANS = "ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"
MONO = "ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,monospace"

def fetch_days():
    today = datetime.date.today()
    frm = (today.replace(day=1) - datetime.timedelta(days=2)).isoformat() + "T00:00:00Z"
    to  = today.isoformat() + "T23:59:59Z"
    q = {"query": """query($login:String!,$from:DateTime!,$to:DateTime!){
        user(login:$login){contributionsCollection(from:$from,to:$to){
        contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}""",
        "variables": {"login": GH_USER, "from": frm, "to": to}}
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps(q).encode(),
        headers={"Authorization": f"bearer {GH_TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    days = sorted((d["date"], d["contributionCount"])
        for w in data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        for d in w["contributionDays"])
    return days

def mock_days():
    import random; random.seed(42)
    today = datetime.date.today(); first = today.replace(day=1)
    days = [((first - datetime.timedelta(days=1)).isoformat(), 6)]
    v, d = 6, first
    while d <= first + datetime.timedelta(days=21):
        v = max(0, v + random.choice([-4,-2,-1,1,2,3,4,6]))
        days.append((d.isoformat(), v)); d += datetime.timedelta(days=1)
    return days

def build(days):
    month = datetime.date.today().strftime("%Y-%m")
    prev, out = None, []
    for date, c in days:
        if date[:7] < month: prev = c; continue
        o = prev if prev is not None else c
        out.append({"day": int(date[8:10]), "o": o, "h": max(o,c), "l": min(o,c), "c": c, "v": c})
        prev = c
    return out, month

def render(cd, month, path):
    W, H = 920, 430
    PL, AXIS_W, HEAD, VOL_H, XAX, GAP = 18, 64, 88, 56, 30, 12
    plot_w  = W - PL - AXIS_W
    price_h = H - HEAD - VOL_H - XAX - GAP
    vol_top = HEAD + price_h + GAP

    hi   = max(max(c["h"] for c in cd), 1) * 1.15
    vmax = max(max(c["v"] for c in cd), 1)
    DIM  = 31
    slot = plot_w / DIM
    bw   = max(5, min(13, slot * 0.55))

    def y(v):  return HEAD + price_h - (v/hi)*price_h
    def x(d):  return PL + slot*(d-1) + slot/2

    last  = cd[-1]
    prevc = cd[-2]["c"] if len(cd) >= 2 else last["o"]
    chg   = last["c"] - prevc
    pct   = (chg/prevc*100) if prevc else 0.0
    up    = chg >= 0
    lc    = GREEN if last["c"] >= last["o"] else RED
    mtd   = sum(c["v"] for c in cd)
    mname = datetime.date(int(month[:4]), int(month[5:7]), 1).strftime("%b %Y").upper()

    s = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    s.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="{BG}" stroke="{FRAME}"/>')

    # ── header ──
    s.append(f'<text x="{PL+8}" y="34" font-family="{SANS}" font-size="13" font-weight="700" letter-spacing="1.2" fill="{TEXT}">{GH_USER.upper()} · COMMITS'
             f'<tspan fill="{SUB}" font-weight="500" letter-spacing="0.6">  1D · {mname}</tspan></text>')
    price_str = str(last["c"])
    s.append(f'<text x="{PL+8}" y="70" font-family="{MONO}" font-size="32" font-weight="800" fill="{GREEN if up else RED}" letter-spacing="-0.5">{price_str}</text>')
    pill_x = PL + 8 + len(price_str)*20 + 14
    pill_t = f'{"+" if up else ""}{chg} ({"+" if up else ""}{pct:.1f}%)'
    pill_w = len(pill_t)*7.4 + 20
    s.append(f'<rect x="{pill_x}" y="50" width="{pill_w:.0f}" height="24" rx="6" fill="{GREEN if up else RED}" opacity="0.14"/>')
    s.append(f'<text x="{pill_x+pill_w/2:.0f}" y="66" text-anchor="middle" font-family="{MONO}" font-size="12" font-weight="700" fill="{GREEN if up else RED}">{pill_t}</text>')
    # OHLC readout (right, two lines)
    rx = W - AXIS_W - 12
    s.append(f'<text x="{rx}" y="34" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="0.3">'
             f'<tspan fill="{SUB}">O</tspan> <tspan fill="{lc}">{last["o"]}</tspan>'
             f'  <tspan fill="{SUB}">H</tspan> <tspan fill="{lc}">{last["h"]}</tspan>'
             f'  <tspan fill="{SUB}">L</tspan> <tspan fill="{lc}">{last["l"]}</tspan>'
             f'  <tspan fill="{SUB}">C</tspan> <tspan fill="{lc}">{last["c"]}</tspan></text>')
    s.append(f'<text x="{rx}" y="54" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="0.3">'
             f'<tspan fill="{SUB}">MTD</tspan> <tspan fill="{TEXT}">{mtd}</tspan>'
             f'  <tspan fill="{SUB}">SESSION</tspan> <tspan fill="{TEXT}">{len(cd)}/{DIM}</tspan></text>')
    s.append(f'<line x1="{PL}" y1="{HEAD-6}" x2="{W-PL}" y2="{HEAD-6}" stroke="{FRAME}" stroke-width="1"/>')

    # ── watermark ──
    s.append(f'<text x="{PL+plot_w/2}" y="{HEAD+price_h/2+12}" text-anchor="middle" font-family="{SANS}" font-size="38" font-weight="800" letter-spacing="6" fill="{TEXT}" opacity="0.035">{GH_USER.upper()}</text>')

    # ── grid + axis ──
    for gv in (0.25, 0.5, 0.75, 1.0):
        gy = HEAD + price_h*(1-gv)
        s.append(f'<line x1="{PL}" y1="{gy:.1f}" x2="{PL+plot_w}" y2="{gy:.1f}" stroke="{GRID}" stroke-width="1"/>')
        s.append(f'<text x="{W-AXIS_W+10}" y="{gy+3.5:.1f}" font-family="{MONO}" font-size="10.5" fill="{SUB}">{hi*gv:.0f}</text>')
    s.append(f'<line x1="{W-AXIS_W}" y1="{HEAD-6}" x2="{W-AXIS_W}" y2="{vol_top+VOL_H}" stroke="{AXIS}" stroke-width="1"/>')

    # ── last price tag ──
    ly = y(last["c"])
    s.append(f'<line x1="{PL}" y1="{ly:.1f}" x2="{W-AXIS_W}" y2="{ly:.1f}" stroke="{lc}" stroke-width="1" stroke-dasharray="2 4" opacity="0.55"/>')
    s.append(f'<rect x="{W-AXIS_W+4}" y="{ly-10:.1f}" width="{AXIS_W-14}" height="20" rx="5" fill="{lc}"/>')
    s.append(f'<text x="{W-AXIS_W+4+(AXIS_W-14)/2}" y="{ly+3.8:.1f}" text-anchor="middle" font-family="{MONO}" font-size="11.5" font-weight="800" fill="{BG}">{last["c"]}</text>')

    # ── candles ──
    for c in cd:
        cx, col = x(c["day"]), (GREEN if c["c"] >= c["o"] else RED)
        top, bot = y(max(c["o"],c["c"])), y(min(c["o"],c["c"]))
        if bot - top < 1.4: bot = top + 1.4
        s.append(f'<line x1="{cx:.1f}" y1="{y(c["h"]):.1f}" x2="{cx:.1f}" y2="{y(c["l"]):.1f}" stroke="{col}" stroke-width="1"/>')
        s.append(f'<rect x="{cx-bw/2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{bot-top:.1f}" rx="1" fill="{col}"/>')

    # ── volume pane ──
    s.append(f'<text x="{PL+8}" y="{vol_top+11}" font-family="{MONO}" font-size="10" letter-spacing="0.5" fill="{SUB}">VOL <tspan fill="{lc}">{last["v"]}</tspan></text>')
    for c in cd:
        cx, col = x(c["day"]), (GREEN if c["c"] >= c["o"] else RED)
        vh = (c["v"]/vmax)*(VOL_H-16)
        s.append(f'<rect x="{cx-bw/2:.1f}" y="{vol_top+VOL_H-vh:.1f}" width="{bw:.1f}" height="{max(vh,1):.1f}" rx="1" fill="{col}" opacity="0.42"/>')

    # ── x axis ──
    for d in (1,5,10,15,20,25,30):
        s.append(f'<text x="{x(d):.1f}" y="{H-12}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{SUB}">{d:02d}</text>')

    s.append('</svg>')
    with open(path,"w") as f: f.write("\n".join(s))

def main():
    days = fetch_days() if GH_TOKEN else mock_days()
    cd, month = build(days)
    if not cd:
        cd = [{"day":1,"o":0,"h":0,"l":0,"c":0,"v":0}]
        month = datetime.date.today().strftime("%Y-%m")
    render(cd, month, OUT)
    print(f"rendered {len(cd)} candles · {month}")

if __name__ == "__main__":
    main()
