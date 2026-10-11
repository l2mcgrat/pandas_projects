"""Gaming & Performance Log icons: fighting-game analytics, PC and console play, athletics, memory and health."""

import math


def _burst(cx: float, cy: float, inner: float, outer: float, count: int, start: float = 0) -> str:
    lines = []
    for i in range(count):
        angle = math.radians(start + i * 360 / count)
        c, s = math.cos(angle), math.sin(angle)
        lines.append(f"M{cx + inner * c:.1f} {cy + inner * s:.1f}L{cx + outer * c:.1f} {cy + outer * s:.1f}")
    return "".join(lines)


def _star(cx: float, cy: float, outer: float, inner: float) -> str:
    return " ".join(f"{cx + (outer if i % 2 == 0 else inner) * math.cos(math.radians(-90 + i * 36)):.1f},"
                    f"{cy + (outer if i % 2 == 0 else inner) * math.sin(math.radians(-90 + i * 36)):.1f}" for i in range(10))


def _grid(x0: int, y0: int, columns: int, rows: int, size: int, gap: int) -> str:
    return "".join(f"M{x0 + c * (size + gap)} {y0 + r * (size + gap)}h{size}v{size}h-{size}z" for r in range(rows) for c in range(columns))


_HEART = "M48 43c-6-4-8-7-8-10a4 4 0 0 1 8-1.5A4 4 0 0 1 56 33c0 3-2 6-8 10z"

ICONS = {
    "Gaming-and-Performance-Log/Smash-Bros": {
        "draw": '<g class="a"><path d="M10 26h22a6 6 0 0 1 6 6v6a8 8 0 0 1-8 8H18a8 8 0 0 1-8-8z"/><path d="M17 26v7M24 26v7M31 26v7M10 36h12"/></g>'
                f'<path class="b" d="{_burst(50, 36, 3, 9, 8)}"/>',
        "parts": (("a", "0%,100%{transform:translateX(0px)}35%{transform:translateX(-4px)}50%{transform:translateX(5px)}62%{transform:translateX(3px)}", "24px 36px", "1.2s", "ease-in-out"),
                  ("b", "0%,45%,100%{transform:scale(.4);opacity:0}52%{transform:scale(1.2);opacity:1}70%{transform:scale(1);opacity:.4}", "50px 36px", "1.2s", "ease-out")),
    },
    "Gaming-and-Performance-Log/Steam": {
        "draw": '<path d="M6 54h52"/><path d="M12 54V24h6v30M20 54V20h6v34M36 54V26h6v28M44 54V18h6v36"/><path d="M14 30h2M22 26h2M38 32h2M46 24h2"/>'
                '<g class="a"><path d="M28 54V22h6v32"/><path d="M30 28h2"/></g>',
        "parts": (("a", "0%,100%{transform:translateY(0px)}40%,60%{transform:translateY(-8px)}", "31px 38px", "2s", "ease-in-out"),),
    },
    "Gaming-and-Performance-Log/Nintendo": {
        "draw": '<rect x="8" y="18" width="48" height="28" rx="9"/><rect x="22" y="22" width="20" height="18" rx="1.5"/>'
                '<path class="a" d="M13 32h7M16.5 28.5v7"/><circle cx="47" cy="29" r="2"/><circle cx="51" cy="34" r="2"/>'
                '<rect class="b" x="30" y="34" width="4" height="4" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%,100%{transform:scale(1)}20%{transform:scale(.8)}35%{transform:scale(1)}", "16.5px 32px", "1s", "ease-out"),
                  ("b", "0%,100%{transform:translateY(0px)}20%{transform:translateY(-8px)}40%{transform:translateY(0px)}", "32px 36px", "1s", "ease-out")),
    },
    "Gaming-and-Performance-Log/Athletics": {
        "draw": '<path d="M22 20h20a12 12 0 0 1 0 24H22a12 12 0 0 1 0-24z"/>'
                '<path opacity=".45" stroke-dasharray="2 3" d="M22 26h20a6 6 0 0 1 0 12H22a6 6 0 0 1 0-12z"/><path opacity=".6" d="M32 14v8"/>'
                '<circle class="a" cx="32" cy="20" r="2.6" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translate(0px,0px)}9%{transform:translate(10px,0px)}17%{transform:translate(18.5px,3.5px)}25%{transform:translate(22px,12px)}"
                        "33%{transform:translate(18.5px,20.5px)}41%{transform:translate(10px,24px)}59%{transform:translate(-10px,24px)}67%{transform:translate(-18.5px,20.5px)}"
                        "75%{transform:translate(-22px,12px)}83%{transform:translate(-18.5px,3.5px)}91%{transform:translate(-10px,0px)}100%{transform:translate(0px,0px)}",
                   "32px 20px", "3.6s", "linear"),),
    },
    "Gaming-and-Performance-Log/Memory": {
        "draw": '<rect x="12" y="14" width="30" height="22" rx="2" transform="rotate(-8 27 25)"/>'
                '<g class="a"><rect x="20" y="24" width="32" height="24" rx="2"/><path d="M33 31c0-3 6-3 6 0s-3 3-3 5M36 41v.5"/></g>'
                '<path class="b" d="M52 10l1.2 2.8 2.8 1.2-2.8 1.2L52 18l-1.2-2.8-2.8-1.2 2.8-1.2z"/>',
        "parts": (("a", "0%,40%,100%{transform:scaleX(1)}55%{transform:scaleX(0)}70%{transform:scaleX(-1)}85%{transform:scaleX(0)}", "36px 36px", "3s", "ease-in-out"),
                  ("b", "0%,100%{opacity:.3;transform:scale(.8)}50%{opacity:1;transform:scale(1.2)}", "52px 14px", "1.5s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Health": {
        "draw": '<path class="b" d="M32 54C18 44 8 34 8 22a12 12 0 0 1 24-4 12 12 0 0 1 24 4c0 12-10 22-24 32z"/>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="M12 32h10l3-6 4 12 4-16 4 10h15"/>',
        "parts": (("a", "0%{stroke-dashoffset:1}55%,85%{stroke-dashoffset:0}100%{stroke-dashoffset:-1}", "32px 30px", "1.8s", "linear"),
                  ("b", "0%,100%{transform:scale(1)}12%{transform:scale(1.06)}24%{transform:scale(.99)}36%{transform:scale(1.04)}", "32px 34px", "1.8s", "ease-out")),
    },
    "Gaming-and-Performance-Log/Smash-Bros/New-Smash-Mains": {
        "draw": f'<path d="{_grid(10, 14, 3, 2, 12, 4)}"/><path d="M48 33v6M45 36h6"/>'
                '<rect class="b" x="42" y="30" width="12" height="12" rx="1"/><path class="a" d="M24 44v12l3.5-3.5 3 5.5 2.5-1.2-3-5.5H35z"/>',
        "parts": (("a", "0%,15%{transform:translate(0px,0px)}50%,80%{transform:translate(24px,-6px)}100%{transform:translate(0px,0px)}", "28px 50px", "2.6s", "ease-in-out"),
                  ("b", "0%,45%{transform:scale(1);opacity:0}60%{transform:scale(1.2);opacity:1}80%{transform:scale(1);opacity:1}100%{opacity:0}", "48px 36px", "2.6s", "ease-out")),
    },
    "Gaming-and-Performance-Log/Smash-Bros/Next-Smash-Mains": {
        "draw": '<circle cx="10" cy="32" r="5"/><circle cx="24" cy="32" r="5"/>'
                '<g class="b"><circle cx="38" cy="32" r="6.5"/><path d="M36 30c0-2.5 4-2.5 4 0s-2 2-2 4"/><circle cx="38" cy="37" r="0.6"/></g>'
                '<path class="a" d="M47 26l5 6-5 6M53 26l5 6-5 6"/>',
        "parts": (("a", "0%{transform:translateX(-3px);opacity:.3}60%{transform:translateX(1px);opacity:1}100%{transform:translateX(-3px);opacity:.3}", "52px 32px", "1s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(1)}50%{transform:scale(1.14)}", "38px 32px", "1s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Smash-Bros/Mechanics-History": {
        "draw": '<path d="M8 28h48v10H8z"/><path d="M20 28v10M36 28v10"/>'
                '<path class="b" fill="currentColor" fill-opacity=".35" stroke="none" d="M20 28h16v10H20z"/>'
                '<path opacity=".5" d="M8 48h48M8 46v4M24 46v4M40 46v4M56 46v4"/>'
                '<g class="a"><path d="M8 22v22"/><path d="M5 18h6l-3 4z"/></g>',
        "parts": (("a", "0%,5%{transform:translateX(0px)}95%,100%{transform:translateX(48px)}", "8px 30px", "2.4s", "linear"),
                  ("b", "0%,30%,70%,100%{opacity:.4}40%,60%{opacity:1}", "28px 33px", "2.4s", "linear")),
    },
    "Gaming-and-Performance-Log/Smash-Bros/Player-Statistics": {
        "draw": '<path d="M8 8v48h48"/>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="16" cy="46" r="1.8"/><circle cx="22" cy="40" r="1.8"/><circle cx="28" cy="42" r="1.8"/>'
                '<circle cx="34" cy="30" r="1.8"/><circle cx="40" cy="32" r="1.8"/><circle cx="46" cy="22" r="1.8"/><circle cx="50" cy="18" r="1.8"/></g>'
                '<path class="a" d="M12 48 54 16"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}50%{transform:rotate(-5deg)}75%{transform:rotate(2deg)}", "33px 32px", "2.2s", "ease-in-out"),
                  ("b", "0%,100%{opacity:.55;transform:scale(1)}50%{opacity:1;transform:scale(1.05)}", "33px 32px", "2.2s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Smash-Bros/Character-Origins": {
        "draw": '<g class="a"><path d="M18 8h28v34H18z"/><rect x="22" y="12" width="20" height="14" rx="1"/><path d="M24 42v5M29 42v5M35 42v5M40 42v5"/>'
                f'<polygon class="b" points="{_star(32, 19, 5, 2.1)}"/></g><path d="M12 48h40v8H12z"/>',
        "parts": (("a", "0%,100%{transform:translateY(-5px)}45%,65%{transform:translateY(3px)}", "32px 28px", "2.4s", "ease-in-out"),
                  ("b", "0%,50%{opacity:.3;transform:rotate(0deg)}65%{opacity:1;transform:rotate(72deg)}100%{opacity:.3;transform:rotate(72deg)}", "32px 19px", "2.4s", "ease-out")),
    },
    "Gaming-and-Performance-Log/Smash-Bros/Highlights": {
        "draw": '<path opacity=".4" d="M10 56h44"/><path class="a" d="M32 56V40"/>'
                f'<g class="b"><path d="{_burst(32, 20, 3, 12, 10)}"/><circle cx="32" cy="20" r="1.4" fill="currentColor" stroke="none"/></g>'
                '<circle cx="14" cy="14" r="1.2" fill="currentColor" stroke="none"/><circle cx="50" cy="30" r="1" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translateY(0px) scaleY(1);opacity:1}35%{transform:translateY(-14px) scaleY(.6);opacity:1}45%,100%{transform:translateY(-18px) scaleY(.2);opacity:0}",
                   "32px 48px", "2s", "ease-out"),
                  ("b", "0%,38%{transform:scale(.2);opacity:0}50%{transform:scale(1);opacity:1}85%{transform:scale(1.2);opacity:0}100%{transform:scale(.2);opacity:0}",
                   "32px 20px", "2s", "ease-out")),
    },
    "Gaming-and-Performance-Log/Steam/Favourites": {
        "draw": '<rect x="16" y="8" width="32" height="48" rx="3"/><path d="M22 8v48"/><path opacity=".6" d="M27 46h16"/>'
                f'<g class="a"><path transform="translate(-13 -6)" d="{_HEART}"/></g>',
        "parts": (("a", "0%,100%{transform:scale(1)}20%{transform:scale(1.2)}35%{transform:scale(1)}50%{transform:scale(1.12)}", "35px 30px", "1.3s", "ease-in-out"),),
    },
    "Gaming-and-Performance-Log/Steam/Achievements-History": {
        "draw": f'<g class="a"><path d="M32 8l16 9v18l-16 9-16-9V17z"/><polygon points="{_star(32, 26, 7, 3)}"/></g>'
                '<path d="M24 40l-4 14 6-3 4 5 1-12M40 40l4 14-6-3-4 5-1-12"/>',
        "parts": (("a", "0%,100%{transform:scaleX(1)}30%{transform:scaleX(.1)}60%{transform:scaleX(1.05)}", "32px 26px", "2s", "ease-in-out"),),
    },
    "Gaming-and-Performance-Log/Steam/Combat-Platformers": {
        "draw": '<path d="M6 54h16M26 44h14M44 34h14"/><g class="a"><path d="M18 40 38 18"/><path d="M14 34l9 9M18 40l-5 5"/></g>'
                '<path class="b" d="M26 10a28 28 0 0 1 24 24"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}35%{transform:rotate(-30deg)}50%{transform:rotate(35deg)}62%{transform:rotate(28deg)}", "16px 42px", "1.3s", "ease-in-out"),
                  ("b", "0%,42%,100%{opacity:0}50%{opacity:1}62%{opacity:0}", "38px 22px", "1.3s", "linear")),
    },
    "Gaming-and-Performance-Log/Steam/Strategy": {
        "draw": '<path d="M6 56h52"/><path opacity=".5" stroke-dasharray="2 2" d="M32 50h20v4H32z"/>'
                '<g class="a"><path d="M22 54h20v-4H22zM24 50l2-18h12l2 18M23 32h18v-9h-4v4h-3v-4h-4v4h-3v-4h-4z"/></g>',
        "parts": (("a", "0%,100%{transform:translate(0px,0px)}25%{transform:translate(0px,-6px)}55%{transform:translate(10px,-6px)}75%,90%{transform:translate(10px,0px)}",
                   "32px 40px", "2.8s", "ease-in-out"),),
    },
    "Gaming-and-Performance-Log/Steam/History": {
        "draw": '<path d="M14 10h30l6 6v38H14z"/><g class="a"><path d="M22 10v12h18V10"/><path d="M34 13v6"/></g>'
                '<rect x="20" y="32" width="24" height="18" rx="1"/><path class="b" d="M24 38h16M24 43h12"/>',
        "parts": (("a", "0%,100%{transform:translateX(0px)}50%{transform:translateX(-5px)}", "31px 16px", "1.6s", "ease-in-out"),
                  ("b", "0%,100%{opacity:.4;transform:translateX(0px)}50%{opacity:1;transform:translateX(1px)}", "32px 40px", "1.6s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Steam/Shopping-Cart": {
        "draw": '<g class="b"><path d="M8 14h6l6 26h28l4-18H18"/><circle cx="24" cy="46" r="3"/><circle cx="44" cy="46" r="3"/></g>'
                '<rect class="a" x="27" y="27" width="12" height="10" rx="1"/>',
        "parts": (("a", "0%{transform:translateY(-18px) rotate(-12deg);opacity:0}30%{opacity:1}55%{transform:translateY(0px) rotate(0deg)}65%{transform:translateY(-2px) rotate(3deg)}"
                        "75%,100%{transform:translateY(0px) rotate(0deg)}", "33px 32px", "2.2s", "ease-in"),
                  ("b", "0%,50%,70%,100%{transform:translateY(0px)}58%{transform:translateY(1.5px)}", "30px 30px", "2.2s", "ease-out")),
    },
    "Gaming-and-Performance-Log/Nintendo/All-Time-Greats": {
        "draw": '<path d="M10 56h44M14 54V34h10v20zM27 54V28h10v26zM40 54V34h10v20z"/><path opacity=".6" d="M16 38h6M29 32h6M42 38h6"/>'
                '<path class="a" d="M22 20l3-10 7 6 7-6 3 10z"/>'
                f'<path class="b" d="{_burst(32, 16, 11, 13, 6, -90)}"/>',
        "parts": (("a", "0%,100%{transform:translateY(0px) rotate(0deg)}50%{transform:translateY(-3px) rotate(-4deg)}", "32px 15px", "2s", "ease-in-out"),
                  ("b", "0%,30%,100%{opacity:0}55%{opacity:1}", "32px 16px", "2s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Nintendo/Mario-Sports": {
        "draw": '<g transform="rotate(-35 24 24)"><ellipse cx="24" cy="24" rx="11" ry="14"/><path opacity=".5" d="M14 18h20M13 24h22M14 30h20M19 11v26M24 10v28M29 11v26"/></g>'
                '<path stroke-width="3" d="M32 35.5 41.2 48.6"/><path opacity=".5" d="M40 57h18"/>'
                '<g class="a"><circle cx="49" cy="16" r="4"/><path d="M45.5 14.5c2 1 5 1 7 0"/></g>',
        "parts": (("a", "0%,100%{transform:translate(0px,0px) scale(1,1)}40%{transform:translate(0px,33px) scale(1.1,.85)}50%{transform:translate(0px,30px) scale(1,1)}",
                   "49px 20px", "1.4s", "ease-in"),),
    },
    "Gaming-and-Performance-Log/Nintendo/Console-Comparison": {
        "draw": '<rect x="6" y="14" width="22" height="14" rx="3"/><path d="M11 21h5M13.5 18.5v5"/>'
                '<rect x="36" y="12" width="22" height="18" rx="5"/><path d="M41 16h12v10H41z"/><path d="M30 21h4"/>'
                '<path class="a" stroke-width="6" d="M17 54V36"/><path class="b" stroke-width="6" d="M47 54V36"/>',
        "parts": (("a", "0%,100%{transform:scaleY(1)}50%{transform:scaleY(.6)}", "17px 54px", "1.8s", "ease-in-out"),
                  ("b", "0%,100%{transform:scaleY(.6)}50%{transform:scaleY(1)}", "47px 54px", "1.8s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Nintendo/Controversy": {
        "draw": '<g class="a"><path d="M32 8 57 52H7z"/><path class="b" d="M32 22v16M32 44v1"/></g>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}15%{transform:rotate(-5deg)}30%{transform:rotate(4deg)}45%{transform:rotate(-2deg)}60%{transform:rotate(0deg)}", "32px 52px", "1.6s", "ease-out"),
                  ("b", "0%,60%,100%{opacity:1}75%{opacity:.3}", "32px 33px", "1.6s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Nintendo/History": {
        "draw": '<g class="b"><path d="M18 8h28M18 56h28M20 8c0 14 12 16 12 24s-12 10-12 24M44 8c0 14-12 16-12 24s12 10 12 24"/>'
                '<path fill="currentColor" stroke="none" d="M26 14h12v4H26zM29 18h6v4h-6zM24 50h16v4H24zM28 46h8v4h-8z"/>'
                '<g class="a" fill="currentColor" stroke="none"><rect x="30.5" y="30" width="3" height="3"/><rect x="30.5" y="36" width="3" height="3"/></g></g>',
        "parts": (("a", "0%{transform:translateY(0px);opacity:1}80%{transform:translateY(10px);opacity:0}100%{transform:translateY(10px);opacity:0}", "32px 34px", "2.5s", "linear"),
                  ("b", "0%,80%{transform:rotate(0deg)}100%{transform:rotate(180deg)}", "32px 32px", "2.5s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Nintendo/Upcoming-Greats": {
        "draw": '<path d="M14 30h36v24H14zM32 30v24"/>'
                '<g class="a"><path d="M12 22h40v8H12z"/><path d="M32 22v8M32 22c-4-8-12-8-10-2 1 2 6 2 10 2zM32 22c4-8 12-8 10-2-1 2-6 2-10 2z"/></g>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="18" cy="12" r="1.3"/><circle cx="46" cy="10" r="1.6"/><circle cx="54" cy="20" r="1.1"/></g>',
        "parts": (("a", "0%,100%{transform:translateY(0px) rotate(0deg)}35%{transform:translateY(-7px) rotate(-8deg)}55%{transform:translateY(-5px) rotate(5deg)}75%{transform:translateY(0px) rotate(0deg)}",
                   "32px 26px", "2s", "ease-in-out"),
                  ("b", "0%,30%,100%{opacity:0;transform:translateY(0px)}55%{opacity:1;transform:translateY(-3px)}", "36px 14px", "2s", "ease-out")),
    },
    "Gaming-and-Performance-Log/Athletics/Running": {
        "draw": '<g class="a"><circle cx="38" cy="12" r="4"/><path d="M36 18l-6 14M34 22l8 4M34 22l-8 2M30 32l8 8-2 10M30 32l-8 6-6-2"/></g>'
                '<path class="b" d="M8 24h10M6 32h12M10 40h8"/>',
        "parts": (("a", "0%,100%{transform:translateY(0px) rotate(0deg)}25%{transform:translateY(-2px) rotate(2deg)}50%{transform:translateY(0px) rotate(0deg)}75%{transform:translateY(-2px) rotate(-1deg)}",
                   "32px 32px", "0.7s", "linear"),
                  ("b", "0%{transform:translateX(4px);opacity:0}40%{opacity:1}100%{transform:translateX(-4px);opacity:0}", "12px 32px", "0.7s", "linear")),
    },
    "Gaming-and-Performance-Log/Athletics/Swimming": {
        "draw": '<circle cx="22" cy="28" r="4.5"/><path class="a" d="M26 30c4-10 14-12 20-4"/>'
                '<path class="b" d="M8 40q5-4 10 0t10 0 10 0 10 0 10 0"/><path opacity=".5" d="M10 48q5-3 10 0t10 0 10 0 10 0"/>',
        "parts": (("a", "0%{transform:rotate(-20deg)}50%{transform:rotate(25deg)}100%{transform:rotate(-20deg)}", "26px 30px", "1.2s", "ease-in-out"),
                  ("b", "0%,100%{transform:translateX(0px)}50%{transform:translateX(-4px)}", "33px 40px", "1.2s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Athletics/Weightlifting": {
        "draw": '<path opacity=".5" d="M8 56h48"/><g class="a"><path d="M8 30h48"/><path stroke-width="3" d="M12 22v16M17 20v20M47 20v20M52 22v16"/></g>'
                '<path class="b" d="M26 46l-3 3M38 46l3 3M32 47v4"/>',
        "parts": (("a", "0%,100%{transform:translateY(12px)}40%,60%{transform:translateY(-4px)}", "32px 30px", "2s", "ease-in-out"),
                  ("b", "0%,30%,70%,100%{opacity:0}45%,55%{opacity:1}", "32px 48px", "2s", "linear")),
    },
    "Gaming-and-Performance-Log/Athletics/Training-Schedule": {
        "draw": '<rect x="8" y="16" width="48" height="32" rx="2"/><path d="M8 24h48M18 12v8M46 12v8"/>'
                '<path opacity=".5" d="M14.9 24v24M21.7 24v24M28.6 24v24M35.4 24v24M42.3 24v24M49.1 24v24"/>'
                '<path class="a" d="M9.5 35l2 2 3-4"/>',
        "parts": (("a", "0%{transform:translateX(0px)}14%{transform:translateX(6.86px)}28%{transform:translateX(13.71px)}42%{transform:translateX(20.57px)}"
                        "57%{transform:translateX(27.43px)}71%{transform:translateX(34.29px)}85%,100%{transform:translateX(41.14px)}", "12px 35px", "3.5s", "steps(1,end)"),),
    },
    "Gaming-and-Performance-Log/Athletics/History": {
        "draw": '<path d="M24 12h16M26 12c-8 6-8 20 0 26h12c8-6 8-20 0-26M28 38v6h8v-6M24 50h16v-6H24z"/><path d="M22 18h-4a4 4 0 0 0 4 8M42 18h4a4 4 0 0 1-4 8"/>'
                '<path class="a" d="M28 18l-2 10"/><path class="b" d="M18 54c4-1 6-3 6-6M46 54c-4-1-6-3-6-6"/>',
        "parts": (("a", "0%{transform:translateX(-2px);opacity:0}40%{opacity:1}70%{transform:translateX(10px);opacity:0}100%{transform:translateX(10px);opacity:0}", "27px 23px", "2.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:scaleX(1)}50%{transform:scaleX(1.12)}", "32px 52px", "2.4s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Athletics/Future-Events": {
        "draw": '<circle opacity=".3" cx="32" cy="32" r="18"/><circle class="a" cx="32" cy="32" r="18" pathLength="1" stroke-dasharray="1" transform="rotate(-90 32 32)"/>'
                '<path d="M30 40V22"/><path class="b" d="M30 22h10l-2.5 3 2.5 3H30"/>',
        "parts": (("a", "0%{stroke-dashoffset:0}100%{stroke-dashoffset:1}", "32px 32px", "4s", "linear"),
                  ("b", "0%,100%{transform:skewY(0deg) scaleX(1)}50%{transform:skewY(6deg) scaleX(.85)}", "30px 25px", "1.3s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Memory/Names-and-Places": {
        "draw": '<g class="a"><path d="M22 54c-8-10-12-16-12-22a12 12 0 0 1 24 0c0 6-4 12-12 22z"/><circle cx="22" cy="32" r="4"/></g>'
                '<g class="b"><path d="M36 14h20v14H36l-4-7z"/><path d="M40 19h10M40 23h7"/></g>',
        "parts": (("a", "0%,100%{transform:translateY(0px)}20%{transform:translateY(-8px)}35%{transform:translateY(0px)}45%{transform:translateY(-2px)}55%{transform:translateY(0px)}",
                   "22px 54px", "2s", "ease-out"),
                  ("b", "0%,100%{transform:rotate(0deg)}30%{transform:rotate(6deg)}60%{transform:rotate(-4deg)}", "32px 21px", "2s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Memory/Scientific-Concepts": {
        "draw": '<path d="M18 40a14 14 0 0 1-4-26 14 14 0 0 1 24-6 12 12 0 0 1 14 18 10 10 0 0 1-12 14z"/><circle cx="16" cy="48" r="3"/><circle cx="10" cy="55" r="2"/>'
                '<g class="a"><circle cx="32" cy="24" r="3.5"/><circle cx="24" cy="30" r="2.5"/><circle cx="41" cy="28" r="2.5"/><circle cx="33" cy="15" r="2.5"/>'
                '<path d="M29 26l-3 2M35 25l4 2M32 21l.5-3.5"/></g>',
        "parts": (("a", "0%{transform:rotate(0deg) translate(0px,0px)}50%{transform:rotate(180deg) translate(0px,-1px)}100%{transform:rotate(360deg) translate(0px,0px)}",
                   "32px 25px", "4s", "linear"),),
    },
    "Gaming-and-Performance-Log/Memory/Techniques": {
        "draw": '<path d="M10 28 32 10l22 18v26H10z"/><path d="M32 28v26M10 41h44M10 28h44"/><path opacity=".6" d="M28 54v-6h-6v6"/>'
                '<circle class="a" cx="21" cy="34.5" r="2.5" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%,20%{transform:translate(0px,0px)}25%,45%{transform:translate(22px,0px)}50%,70%{transform:translate(22px,13px)}75%,95%{transform:translate(0px,13px)}"
                        "100%{transform:translate(0px,0px)}", "21px 34.5px", "4s", "ease-in-out"),),
    },
    "Gaming-and-Performance-Log/Memory/Meditation-Study": {
        "draw": '<path class="b" d="M44 14A20 20 0 1 0 52 30"/><circle class="a" cx="32" cy="32" r="8"/>',
        "parts": (("a", "0%,100%{transform:scale(.7);opacity:.6}50%{transform:scale(1.1);opacity:1}", "32px 32px", "5s", "ease-in-out"),
                  ("b", "0%,100%{transform:rotate(-8deg)}50%{transform:rotate(8deg)}", "32px 32px", "5s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Memory/Quiz-Analytics": {
        "draw": '<rect x="10" y="8" width="30" height="46" rx="2"/><circle cx="17" cy="18" r="3"/><circle cx="17" cy="28" r="3"/><circle cx="17" cy="38" r="3"/>'
                '<path d="M23 18h11M23 28h11M23 38h11"/><circle class="a" cx="17" cy="18" r="1.4" fill="currentColor" stroke="none"/>'
                '<path opacity=".35" stroke-width="5" d="M48 54V24"/><path class="b" stroke-width="5" d="M48 54V24"/>',
        "parts": (("a", "0%,25%{transform:translateY(0px)}35%,60%{transform:translateY(10px)}70%,100%{transform:translateY(20px)}", "17px 18px", "2.4s", "ease-in-out"),
                  ("b", "0%{transform:scaleY(.2)}70%,100%{transform:scaleY(1)}", "48px 54px", "2.4s", "ease-out")),
    },
    "Gaming-and-Performance-Log/Memory/Information-Theory": {
        "draw": '<path opacity=".5" d="M6 20h52M6 44h52"/>'
                '<g class="a"><path d="M10 26v12M26 26v12M34 26v12M50 26v12"/><ellipse cx="18" cy="32" rx="3" ry="6"/><ellipse cx="42" cy="32" rx="3" ry="6"/></g>'
                '<path class="b" d="M10 52l3-3 3 3 3-3 3 3 3-3 3 3"/>',
        "parts": (("a", "0%{transform:translateX(4px);opacity:.4}50%{opacity:1}100%{transform:translateX(-4px);opacity:.4}", "30px 32px", "1.2s", "linear"),
                  ("b", "0%,100%{opacity:.2}35%{opacity:.8}65%{opacity:.35}", "19px 50px", "0.9s", "linear")),
    },
    "Gaming-and-Performance-Log/Health/Sleep": {
        "draw": '<path class="b" d="M40 14a16 16 0 1 0 14 24 13 13 0 0 1-14-24z"/><path class="a" d="M12 18h7l-7 7h7M22 8h5l-5 5h5"/>',
        "parts": (("a", "0%{transform:translate(0px,4px) scale(.8);opacity:0}40%{opacity:1}100%{transform:translate(-3px,-4px) scale(1.1);opacity:0}", "18px 18px", "2.4s", "ease-out"),
                  ("b", "0%,100%{transform:rotate(0deg)}50%{transform:rotate(-6deg)}", "40px 32px", "4s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Health/Diet": {
        "draw": '<g class="b"><path d="M32 20c-6-4-16-2-16 10 0 12 8 22 16 18 8 4 16-6 16-18 0-12-10-14-16-10z"/><path d="M32 20c0-4 2-7 4-8"/></g>'
                '<path class="a" d="M35 15c4-4 10-4 12-2-2 4-8 5-12 2z"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}50%{transform:rotate(-12deg)}75%{transform:rotate(3deg)}", "35px 15px", "1.8s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(1,1)}50%{transform:scale(1.04,.97)}", "32px 48px", "1.8s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Health/Mentality": {
        "draw": '<path d="M38 54V44h6l2-8 4-2-4-6c0-10-8-18-18-18S12 18 12 30c0 7 4 12 8 15v9"/>'
                f'<circle class="b" cx="29" cy="29" r="4.5"/><path class="a" d="{_burst(29, 29, 7, 10, 8)}"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg) scale(1)}50%{transform:rotate(22.5deg) scale(1.08)}", "29px 29px", "3s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(.95)}50%{transform:scale(1.18)}", "29px 29px", "3s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Health/Information-Consumption": {
        "draw": '<path d="M10 12h44L38 32v14l-12 6V32z"/>'
                '<g class="a"><rect x="18" y="2" width="6" height="6" rx="1"/><rect x="30" y="1" width="6" height="6" rx="1"/><rect x="42" y="3" width="5" height="5" rx="1"/></g>'
                '<circle class="b" cx="32" cy="56" r="2" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translateY(-2px);opacity:0}25%{opacity:1}80%{transform:translateY(14px) scale(.7);opacity:0}100%{opacity:0}", "32px 8px", "2s", "ease-in"),
                  ("b", "0%,70%{transform:translateY(-4px);opacity:0}85%{opacity:1}100%{transform:translateY(2px);opacity:0}", "32px 56px", "2s", "ease-in")),
    },
    "Gaming-and-Performance-Log/Health/Analytics": {
        "draw": '<rect x="20" y="18" width="24" height="28" rx="5"/><path d="M24 18l2-10h12l2 10M24 46l2 10h12l2-10M44 28h2v6h-2"/>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="M23 33h5l2-4 3 8 2-6 2 2h4"/>'
                '<circle class="b" cx="32" cy="24" r="1.3" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{stroke-dashoffset:1}50%,75%{stroke-dashoffset:0}100%{stroke-dashoffset:-1}", "32px 33px", "1.6s", "linear"),
                  ("b", "0%,100%{opacity:1}40%{opacity:.2}", "32px 24px", "0.8s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log/Health/Struggles-and-Setbacks": {
        "draw": '<g class="b"><circle cx="44" cy="18" r="6"/><path d="M44 8V6M52 12l1.5-1.5M54 20h2"/></g>'
                '<path d="M16 38a8 8 0 0 1 2-15.7A11 11 0 0 1 39 20a8 8 0 0 1 3 16z"/><path class="a" d="M20 44l-2 5M28 44l-2 5M36 44l-2 5"/>',
        "parts": (("a", "0%{transform:translateY(-3px);opacity:0}30%{opacity:1}100%{transform:translateY(6px);opacity:0}", "28px 46px", "0.9s", "linear"),
                  ("b", "0%,100%{transform:translate(0px,2px)}50%{transform:translate(2px,-2px)}", "44px 18px", "3s", "ease-in-out")),
    },
}
