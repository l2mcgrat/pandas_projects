"""Sports & Entertainment icons: anime, film, reality TV, video creators, the First to Four series and sports analytics."""

import math


def _star(cx: float, cy: float, outer: float, inner: float, points: int = 5) -> str:
    coords = []
    for i in range(points * 2):
        radius = outer if i % 2 == 0 else inner
        angle = math.radians(-90 + i * 180 / points)
        coords.append(f"{cx + radius * math.cos(angle):.1f},{cy + radius * math.sin(angle):.1f}")
    return " ".join(coords)


def _grid(x0: int, y0: int, columns: int, rows: int, size: int, gap: int, skip=()) -> str:
    return "".join(f"M{x0 + c * (size + gap)} {y0 + r * (size + gap)}h{size}v{size}h-{size}z"
                   for r in range(rows) for c in range(columns) if (c, r) not in skip)


_HEART = "M0 4c-3-2-4.5-3.5-4.5-5a2.25 2.25 0 0 1 4.5-.8 2.25 2.25 0 0 1 4.5.8c0 1.5-1.5 3-4.5 5z"

ICONS = {
    "Sports-and-Entertainment/Anime-and-Manga": {
        "draw": '<rect x="12" y="8" width="40" height="48" rx="2"/><path d="M12 28h40M30 8v20M12 42l40-4M26 40v16"/>'
                '<path class="a" d="M35 14h13M37 19h11M33 24h15"/>'
                f'<polygon class="b" points="{_star(40, 48, 5.5, 2.4, 6)}"/>',
        "parts": (("a", "0%{transform:translateX(4px);opacity:0}30%{opacity:1}100%{transform:translateX(-6px);opacity:0}", "41px 19px", "0.8s", "linear"),
                  ("b", "0%,100%{transform:scale(1) rotate(0deg)}50%{transform:scale(1.25) rotate(30deg)}", "40px 48px", "1.6s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Western-Productions": {
        "draw": '<rect x="10" y="28" width="44" height="26" rx="2"/><path d="M10 37h44M10 46h44"/>'
                '<g class="a"><path d="M10 28l42-8 1.5 6-42 8z"/><path d="M19 26.5l3.5 4.5M29 24.5l3.5 4.5M39 22.5l3.5 4.5"/></g>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}30%{transform:rotate(-14deg)}45%,52%{transform:rotate(0deg)}", "10px 28px", "1.4s", "ease-in"),),
    },
    "Sports-and-Entertainment/Big-Brother-and-Survivor": {
        "draw": '<path d="M28 56l2-30h4l2 30"/><path d="M24 22h16l-3 6H27z"/>'
                '<path class="a" d="M32 20c-6-4-4-10 0-14 0 4 6 5 4 10-1 3-2 4-4 4z"/>'
                '<rect x="40" y="8" width="12" height="7" rx="1.5"/><path d="M52 10l4-2v7l-4-2"/>'
                '<circle class="b" cx="44" cy="11.5" r="1.4" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%,100%{transform:scale(1,1) skewX(0deg)}25%{transform:scale(.92,1.12) skewX(4deg)}50%{transform:scale(1.05,.94) skewX(-3deg)}75%{transform:scale(.96,1.08) skewX(2deg)}",
                   "32px 20px", "0.9s", "ease-in-out"),
                  ("b", "0%,55%{opacity:1}56%,100%{opacity:.1}", "44px 11.5px", "1.2s", "steps(1,end)")),
    },
    "Sports-and-Entertainment/YouTube": {
        "draw": f'<path d="{_grid(8, 8, 2, 2, 22, 4)}"/><path d="M15 13v8l7-4z"/><path opacity=".35" d="M8 56h48"/>'
                '<path class="b" pathLength="1" stroke-dasharray="1" d="M8 56h48"/><circle class="a" cx="8" cy="56" r="3" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translateX(0px)}90%{transform:translateX(48px);opacity:1}100%{transform:translateX(48px);opacity:0}", "8px 56px", "3.2s", "linear"),
                  ("b", "0%{stroke-dashoffset:1}90%,100%{stroke-dashoffset:0}", "32px 56px", "3.2s", "linear")),
    },
    "Sports-and-Entertainment/Series-Hub": {
        "draw": '<rect x="8" y="24" width="48" height="30" rx="3"/><path d="M16 31v10h9M22 29v18"/>'
                '<path d="M38 31h8l-4.5 6c3.5 0 5.5 2 5.5 4.5S45 46 42 46s-4-1.5-4.5-2.5"/>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="32" cy="35" r="1.4"/><circle cx="32" cy="42" r="1.4"/></g>'
                f'<g class="a"><circle cx="32" cy="12" r="6"/><path d="M26 12h12M32 6v12"/></g>',
        "parts": (("a", "0%,100%{transform:translateY(0px) scale(1,1)}45%{transform:translateY(5.5px) scale(1.15,.85)}55%{transform:translateY(5px) scale(1.1,.9)}",
                   "32px 18px", "0.9s", "ease-in"),
                  ("b", "0%,49%,100%{opacity:1}50%,99%{opacity:.2}", "32px 38px", "1.8s", "steps(1,end)")),
    },
    "Sports-and-Entertainment/Sports-Analytics": {
        "draw": '<rect x="8" y="10" width="48" height="44" rx="2"/><path d="M24 10v18h16V10M12 10v8a20 20 0 0 0 40 0v-8"/><circle cx="32" cy="14" r="2"/>'
                '<g class="a" fill="currentColor" stroke="none"><circle cx="20" cy="40" r="1.8"/><circle cx="32" cy="46" r="1.8"/><circle cx="44" cy="40" r="1.8"/><circle cx="28" cy="24" r="1.8"/></g>'
                '<path class="b" d="M14 30l3 3m0-3-3 3M47 26l3 3m0-3-3 3"/>',
        "parts": (("a", "0%,100%{transform:scale(.6);opacity:.4}50%{transform:scale(1.1);opacity:1}", "32px 36px", "1.8s", "ease-in-out"),
                  ("b", "0%,30%,100%{opacity:.2}50%,70%{opacity:1}", "32px 29px", "1.8s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Anime-and-Manga/SeriesGraph-Top-50": {
        "draw": f'<path d="{_grid(12, 14, 5, 4, 6, 2, skip={(1, 1), (3, 2), (2, 3)})}"/>'
                f'<path fill="currentColor" fill-opacity=".45" stroke="none" d="{_grid(12, 14, 5, 4, 6, 2, skip={(c, r) for c in range(5) for r in range(4) if (c + r) % 3})}"/>'
                '<path d="M10 52h44"/><rect class="a" x="10" y="12" width="10" height="34" rx="1.5"/>',
        "parts": (("a", "0%{transform:translateX(0px)}20%{transform:translateX(8px)}40%{transform:translateX(16px)}60%{transform:translateX(24px)}80%,100%{transform:translateX(32px)}",
                   "15px 29px", "2.5s", "steps(1,end)"),),
    },
    "Sports-and-Entertainment/Anime-and-Manga/Anime-Studios": {
        "draw": '<path d="M10 56V32h44v24"/><path d="M16 38h6v6h-6zM29 38h6v6h-6zM42 38h6v6h-6zM28 56v-6h8v6"/>'
                '<g class="a"><circle cx="32" cy="17" r="10"/><circle cx="32" cy="17" r="2"/><circle cx="32" cy="11" r="2.4"/>'
                '<circle cx="37.2" cy="20" r="2.4"/><circle cx="26.8" cy="20" r="2.4"/></g><path d="M32 27v5"/>',
        "parts": (("a", "0%{transform:rotate(-60deg)}100%{transform:rotate(60deg)}", "32px 17px", "1.5s", "linear"),),
    },
    "Sports-and-Entertainment/Anime-and-Manga/Legendary-Authors": {
        "draw": '<path d="M18 46h16v10H18zM20 46v-4h12v4"/>'
                '<g class="a"><path d="M30 40C38 28 46 16 56 8c-4 12-12 22-22 30z"/><path d="M33 37l18-24"/></g>'
                '<path class="b" pathLength="1" stroke-dasharray="1" d="M38 54c3-2 5 2 8 0s5 2 8 0"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg) translate(0px,0px)}25%{transform:rotate(-4deg) translate(2px,-1px)}50%{transform:rotate(3deg) translate(4px,0px)}"
                        "75%{transform:rotate(-2deg) translate(2px,1px)}", "30px 40px", "1.6s", "ease-in-out"),
                  ("b", "0%,10%{stroke-dashoffset:1}75%,100%{stroke-dashoffset:0}", "46px 54px", "1.6s", "linear")),
    },
    "Sports-and-Entertainment/Anime-and-Manga/Production-Process": {
        "draw": '<rect x="12" y="22" width="36" height="30" rx="1"/><path d="M22 18h16"/><circle cx="26" cy="18" r="1.5"/><circle cx="34" cy="18" r="1.5"/>'
                '<g class="a"><rect x="14" y="20" width="36" height="30" rx="1"/><circle cx="30" cy="36" r="6"/><path d="M24 44c4-2 8-2 12 0"/></g>',
        "parts": (("a", "0%,100%{transform:scaleY(1)}40%,55%{transform:scaleY(-.2)}", "32px 20px", "2.2s", "ease-in-out"),),
    },
    "Sports-and-Entertainment/Anime-and-Manga/Sakuga-and-Artstyles": {
        "draw": '<path opacity=".45" stroke-dasharray="2 3" d="M12 46C16 30 30 22 52 24"/>'
                '<circle opacity=".25" cx="24" cy="30" r="4"/><circle opacity=".4" cx="40" cy="22" r="4"/>'
                '<path class="b" d="M8 54h48"/><circle class="a" cx="12" cy="46" r="4.5"/>',
        "parts": (("a", "0%{transform:translate(0px,0px) scale(1,1)}30%{transform:translate(12px,-16px) scale(1.25,.8)}60%{transform:translate(28px,-24px) scale(.85,1.15)}"
                        "85%,100%{transform:translate(40px,-22px) scale(1,1)}", "12px 46px", "1.6s", "cubic-bezier(.2,.8,.3,1)"),
                  ("b", "0%,100%{transform:scaleX(1)}30%{transform:scaleX(.9)}", "32px 54px", "1.6s", "ease-out")),
    },
    "Sports-and-Entertainment/Anime-and-Manga/Upcoming-Greatness": {
        "draw": f'<polygon class="a" points="{_star(42, 20, 9, 4)}"/>'
                '<path class="b" d="M30 32 14 48M34 36l-12 12M26 30 12 44"/><path d="M8 56h48" opacity=".4"/>',
        "parts": (("a", "0%{transform:translate(-8px,8px) scale(.7);opacity:.3}60%{transform:translate(0px,0px) scale(1.1);opacity:1}100%{transform:translate(0px,0px) scale(1);opacity:1}",
                   "42px 20px", "2.2s", "ease-out"),
                  ("b", "0%{opacity:0}40%{opacity:.9}100%{opacity:0}", "22px 40px", "2.2s", "ease-out")),
    },
    "Sports-and-Entertainment/Western-Productions/SeriesGraph-Top-50": {
        "draw": '<path d="M8 50h48M8 10v40"/><path opacity=".4" stroke-dasharray="2 3" d="M25 14v36M42 14v36"/>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="M10 42l4-6 5 3 4-8M27 34l4-5 5 2 4-7M44 26l4-5 5 1"/>'
                '<path class="b" d="M46 10l2-4 2 3 2-3 2 4z"/>',
        "parts": (("a", "0%,4%{stroke-dashoffset:1}66%,100%{stroke-dashoffset:0}", "32px 34px", "3s", "ease-in-out"),
                  ("b", "0%,100%{transform:translateY(0px) rotate(0deg)}50%{transform:translateY(-2px) rotate(-8deg)}", "50px 8px", "1.5s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Western-Productions/Adult-Animation": {
        "draw": '<rect x="8" y="18" width="48" height="32" rx="4"/><rect x="13" y="23" width="38" height="22" rx="2"/>'
                '<g class="b"><path d="M24 18l-6-10M40 18l6-10"/></g><path d="M16 50l-3 6M48 50l3 6"/>'
                f'<polygon class="a" points="{_star(32, 34, 8, 4, 8)}"/>',
        "parts": (("a", "0%,100%{transform:scale(1) rotate(0deg)}20%{transform:scale(1.2) rotate(-8deg)}40%{transform:scale(.9) rotate(6deg)}60%{transform:scale(1.1) rotate(-3deg)}",
                   "32px 34px", "1.2s", "ease-in-out"),
                  ("b", "0%,100%{transform:rotate(0deg)}50%{transform:rotate(5deg)}", "32px 18px", "1.2s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Western-Productions/Comedians": {
        "draw": '<path opacity=".3" d="M14 4l8 48h20l8-48"/><g class="a"><ellipse cx="32" cy="16" rx="5" ry="7"/><path d="M32 23v27"/></g>'
                '<path d="M22 54h20M32 50v4"/><path class="b" d="M14 16l-4-2M14 22H9M50 16l4-2M50 22h5"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}30%{transform:rotate(-8deg)}60%{transform:rotate(5deg)}", "32px 50px", "1.8s", "ease-in-out"),
                  ("b", "0%,100%{opacity:0}30%,45%{opacity:1}60%{opacity:.3}75%{opacity:1}", "32px 19px", "1.8s", "linear")),
    },
    "Sports-and-Entertainment/Western-Productions/Production-Process": {
        "draw": '<rect x="12" y="26" width="28" height="16" rx="2"/><path d="M40 30l10-4v16l-10-4z"/><path d="M26 42 19 56M26 42v14M26 42l7 14"/>'
                '<g class="a"><circle cx="19" cy="18" r="6"/><path d="M19 18v-6M19 18l5.2 3M19 18l-5.2 3"/></g>'
                '<g class="b"><circle cx="33" cy="18" r="6"/><path d="M33 18v-6M33 18l5.2 3M33 18l-5.2 3"/></g>',
        "parts": (("a", "0%{transform:rotate(0deg)}100%{transform:rotate(240deg)}", "19px 18px", "1.6s", "linear"),
                  ("b", "0%{transform:rotate(60deg)}100%{transform:rotate(300deg)}", "33px 18px", "1.6s", "linear")),
    },
    "Sports-and-Entertainment/Western-Productions/History-of-Film": {
        "draw": '<path d="M6 20h52M6 44h52"/><path class="b" stroke-dasharray="2 3" d="M6 24h52M6 40h52"/>'
                '<g class="a"><path d="M12 28h10v8H12zM26 28h10v8H26zM40 28h10v8H40z"/></g>',
        "parts": (("a", "0%{transform:translateX(-7px)}100%{transform:translateX(7px)}", "32px 32px", "1s", "linear"),
                  ("b", "0%{stroke-dashoffset:5}100%{stroke-dashoffset:0}", "32px 32px", "0.5s", "linear")),
    },
    "Sports-and-Entertainment/Western-Productions/Controversies": {
        "draw": '<g class="a"><rect x="8" y="14" width="40" height="38" rx="2"/><path d="M14 22h28" stroke-width="3"/><path d="M14 30h12M14 35h12M14 40h12M14 45h12M30 30h12v15H30z"/></g>'
                '<path class="b" d="M54 6l-6 12h6l-6 12"/>',
        "parts": (("a", "0%,100%{transform:translateX(0px) rotate(0deg)}20%{transform:translateX(-1.5px) rotate(-2deg)}40%{transform:translateX(1.5px) rotate(2deg)}60%{transform:translateX(-1px) rotate(-1deg)}",
                   "28px 33px", "0.8s", "ease-in-out"),
                  ("b", "0%,100%{opacity:.2}10%,20%{opacity:1}30%{opacity:.2}40%{opacity:.9}", "51px 18px", "1.6s", "linear")),
    },
    "Sports-and-Entertainment/Big-Brother-and-Survivor/All-Time-Greats": {
        "draw": '<g class="b"><path d="M22 52c-10-6-12-22-4-32M18 46l-5 1M15 39l-5-1M15 32l-4-3M18 25l-3-4"/>'
                '<path d="M42 52c10-6 12-22 4-32M46 46l5 1M49 39l5-1M49 32l4-3M46 25l3-4"/></g>'
                f'<polygon class="a" points="{_star(32, 32, 9, 3.8)}"/>',
        "parts": (("a", "0%,100%{transform:scale(1) rotate(0deg)}50%{transform:scale(1.15) rotate(36deg)}", "32px 32px", "2s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(1)}50%{transform:scale(1.04,.97)}", "32px 52px", "2s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Big-Brother-and-Survivor/Starter-Seasons": {
        "draw": '<rect class="b" x="8" y="12" width="48" height="34" rx="3"/><path d="M24 46l-4 8h24l-4-8"/>'
                '<path d="M28 21c-5-3-10 0-8 3.5s9 2.5 7.5 7.5-8 3.5-9.5.5"/><path class="a" d="M36 22l5-3v18M36 37h10"/>',
        "parts": (("a", "0%,100%{transform:translateY(0px) scale(1)}35%{transform:translateY(-3px) scale(1.08)}55%{transform:translateY(0px) scale(.97)}",
                   "41px 37px", "1.6s", "ease-out"),
                  ("b", "0%,100%{opacity:.75}50%{opacity:1}", "32px 29px", "1.6s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Big-Brother-and-Survivor/Roadmaps-to-Victory": {
        "draw": '<path d="M8 14l14-4 14 4 14-4v40l-14 4-14-4-14 4z"/><path d="M22 10v40M36 14v40" opacity=".5"/>'
                '<path class="a" stroke-dasharray="2.5 3.5" d="M14 44c6-6 4-14 12-16s10 6 16-4"/><path class="b" d="M40 18l6 6M46 18l-6 6"/>',
        "parts": (("a", "0%{stroke-dashoffset:6}100%{stroke-dashoffset:0}", "28px 34px", "0.7s", "linear"),
                  ("b", "0%,100%{transform:scale(1) rotate(0deg)}50%{transform:scale(1.3) rotate(90deg)}", "43px 21px", "1.4s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Big-Brother-and-Survivor/Greatest-Moments": {
        "draw": '<g class="a"><path d="M44.5 21A16 16 0 1 0 48 32"/><path d="M44.5 21l.5-6M44.5 21l-6-.5"/></g>'
                '<path class="b" d="M28 24v16l13-8z"/>',
        "parts": (("a", "0%{transform:rotate(360deg)}100%{transform:rotate(0deg)}", "32px 32px", "2.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(1)}50%{transform:scale(1.18)}70%{transform:scale(.95)}", "33px 32px", "1.2s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Big-Brother-and-Survivor/Predictions-and-Analytics": {
        "draw": '<circle cx="32" cy="28" r="17"/><path d="M20 50h24l-4-6H24zM16 56h32"/>'
                '<path class="b" d="M24 34v-6M30 34v-10M36 34v-4M42 34v-8"/>'
                '<g class="a"><path d="M23 18l1 2 2 1-2 1-1 2-1-2-2-1 2-1z"/></g>',
        "parts": (("a", "0%{transform:rotate(0deg) scale(1)}100%{transform:rotate(360deg) scale(1)}", "32px 28px", "3.2s", "linear"),
                  ("b", "0%,100%{transform:scaleY(1);opacity:.7}50%{transform:scaleY(1.25);opacity:1}", "33px 34px", "1.6s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Big-Brother-and-Survivor/Controversies": {
        "draw": '<path class="a" d="M8 12h22v14H18l-5 5v-5H8z"/><path class="b" d="M34 30h22v14h-5v5l-5-5H34z"/>'
                '<path class="c" d="M31 22l4 4-4 2 4 4"/>',
        "parts": (("a", "0%,100%{transform:translateX(0px)}25%{transform:translateX(-1.5px)}50%{transform:translateX(1.5px)}75%{transform:translateX(-.8px)}", "19px 19px", "0.5s", "linear"),
                  ("b", "0%,100%{transform:translateX(0px)}25%{transform:translateX(1.5px)}50%{transform:translateX(-1.5px)}75%{transform:translateX(.8px)}", "45px 37px", "0.5s", "linear"),
                  ("c", "0%,100%{opacity:.3;transform:scale(.9)}50%{opacity:1;transform:scale(1.15)}", "33px 27px", "1s", "ease-in-out")),
    },
    "Sports-and-Entertainment/YouTube/Educational": {
        "draw": '<rect x="8" y="10" width="48" height="32" rx="2"/><path d="M24 48h16M32 42v6"/>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="M14 30c4-12 8-12 12 0s8 12 12 0 6-8 8-6"/>'
                '<path class="b" d="M50 52 40 30"/>',
        "parts": (("a", "0%,6%{stroke-dashoffset:1}64%,100%{stroke-dashoffset:0}", "30px 26px", "2.8s", "ease-out"),
                  ("b", "0%,100%{transform:rotate(0deg)}60%{transform:rotate(0deg)}70%{transform:rotate(-6deg)}80%{transform:rotate(0deg)}", "50px 52px", "2.8s", "ease-in-out")),
    },
    "Sports-and-Entertainment/YouTube/Parasocial": {
        "draw": '<circle cx="12" cy="26" r="4.5"/><path d="M4 42c1-6 4-9 8-9s7 3 8 9"/><rect class="b" x="38" y="18" width="20" height="16" rx="2"/>'
                '<path d="M44 40h8M48 34v6"/><path opacity=".5" stroke-dasharray="2 3" d="M20 46h30m-3-3 3 3-3 3"/>'
                f'<g class="a"><path transform="translate(24 28)" d="{_HEART}"/></g>',
        "parts": (("a", "0%{transform:translateX(0px) scale(.6);opacity:0}20%{opacity:1}80%{transform:translateX(20px) scale(1);opacity:1}100%{transform:translateX(24px) scale(.8);opacity:0}",
                   "24px 28px", "2.4s", "ease-in-out"),
                  ("b", "0%,70%,100%{opacity:.6}85%{opacity:1}", "48px 26px", "2.4s", "ease-in-out")),
    },
    "Sports-and-Entertainment/YouTube/Documentary": {
        "draw": '<g class="a"><rect x="10" y="24" width="30" height="20" rx="3"/><path d="M40 28l12-6v24l-12-6z"/><path d="M14 24v-6h12v6"/></g>'
                '<circle class="b" cx="16" cy="30" r="1.8" fill="currentColor" stroke="none"/><path d="M14 52h28" opacity=".4"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg) translate(0px,0px)}30%{transform:rotate(1.5deg) translate(.6px,-.6px)}65%{transform:rotate(-2deg) translate(-.5px,.4px)}",
                   "26px 34px", "2s", "ease-in-out"),
                  ("b", "0%,49%{opacity:1}50%,100%{opacity:.1}", "16px 30px", "1s", "steps(1,end)")),
    },
    "Sports-and-Entertainment/YouTube/Data-Analytics": {
        "draw": '<path d="M8 54h48M8 18v36"/><path class="b" pathLength="1" stroke-dasharray="1" d="M10 50c10-2 16-8 22-16s12-10 22-12"/>'
                '<path d="M34 14c6-6 14-6 20 0-6 6-14 6-20 0z"/><circle class="a" cx="44" cy="14" r="2.2" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%,100%{transform:translate(0px,0px)}30%{transform:translate(-2.5px,0px)}60%{transform:translate(2.5px,.5px)}", "44px 14px", "2.4s", "ease-in-out"),
                  ("b", "0%{stroke-dashoffset:1}70%,100%{stroke-dashoffset:0}", "32px 36px", "2.4s", "ease-out")),
    },
    "Sports-and-Entertainment/YouTube/History": {
        "draw": '<rect x="8" y="18" width="48" height="28" rx="3"/><rect x="18" y="24" width="28" height="10" rx="2"/><path d="M14 40h36M24 46l2-4h12l2 4"/>'
                '<g class="a"><circle cx="24" cy="29" r="3.5"/><path d="M24 29v-3.5M24 29l3 1.8M24 29l-3 1.8"/></g>'
                '<g class="b"><circle cx="40" cy="29" r="3.5"/><path d="M40 29v-3.5M40 29l3 1.8M40 29l-3 1.8"/></g>',
        "parts": (("a", "0%{transform:rotate(-30deg)}100%{transform:rotate(90deg)}", "24px 29px", "1.2s", "linear"),
                  ("b", "0%{transform:rotate(10deg)}100%{transform:rotate(130deg)}", "40px 29px", "1.2s", "linear")),
    },
    "Sports-and-Entertainment/YouTube/Personal": {
        "draw": '<rect x="20" y="8" width="24" height="46" rx="4"/><circle cx="32" cy="12" r="1" fill="currentColor" stroke="none"/>'
                '<circle class="b" cx="32" cy="46" r="3"/>'
                f'<g class="a"><path transform="translate(32 30)" d="{_HEART}"/></g>',
        "parts": (("a", "0%{transform:translateY(4px) scale(.7);opacity:0}30%{opacity:1}100%{transform:translateY(-12px) scale(1.1);opacity:0}", "32px 30px", "1.8s", "ease-out"),
                  ("b", "0%,100%{transform:scale(1)}50%{transform:scale(.8)}", "32px 46px", "1.8s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Series-Hub/Videos": {
        "draw": '<rect x="8" y="10" width="48" height="34" rx="3"/><path d="M12 40h40"/><path opacity=".35" d="M8 52h48"/>'
                '<path class="b" pathLength="1" stroke-dasharray="1" d="M8 52h48"/>'
                '<g class="a"><circle cx="32" cy="21" r="5"/><path d="M27 21h10M32 16v10"/></g>',
        "parts": (("a", "0%,100%{transform:translateY(0px) scale(1,1)}45%{transform:translateY(13px) scale(1,1)}52%{transform:translateY(14px) scale(1.15,.85)}60%{transform:translateY(12px) scale(1,1)}",
                   "32px 26px", "1.1s", "ease-in"),
                  ("b", "0%{stroke-dashoffset:1}96%,100%{stroke-dashoffset:0}", "32px 52px", "4.4s", "linear")),
    },
    "Sports-and-Entertainment/Series-Hub/Rules": {
        "draw": '<rect x="10" y="8" width="30" height="40" rx="2"/><path d="M16 8v40M21 16h14M21 22h14M21 28h10"/>'
                '<g class="a"><circle cx="44" cy="46" r="7"/><path d="M37 42h-8v-6h11"/><circle cx="44" cy="46" r="2"/></g>'
                '<path class="b" d="M53 37a10 10 0 0 1 3 7M55 33a14 14 0 0 1 3 10"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}20%{transform:rotate(-6deg)}40%{transform:rotate(5deg)}60%{transform:rotate(-3deg)}", "40px 44px", "1s", "ease-in-out"),
                  ("b", "0%{opacity:0;transform:translate(-2px,1px)}30%{opacity:1}100%{opacity:0;transform:translate(2px,-1px)}", "55px 40px", "1s", "ease-out")),
    },
    "Sports-and-Entertainment/Series-Hub/Analytics": {
        "draw": '<path d="M10 16h44v6H10zM10 29h44v6H10zM10 42h44v6H10z"/>'
                '<path class="a" fill="currentColor" fill-opacity=".45" stroke="none" d="M10 16h26v6H10zM10 29h18v6H10zM10 42h32v6H10z"/>'
                '<path d="M8 10v42" opacity=".5"/>',
        "parts": (("a", "0%,100%{transform:scaleX(1)}35%{transform:scaleX(.88)}70%{transform:scaleX(1.08)}", "10px 32px", "2.2s", "ease-in-out"),),
    },
    "Sports-and-Entertainment/Series-Hub/History": {
        "draw": '<rect x="10" y="8" width="38" height="48" rx="2"/><path d="M10 16h38" opacity=".5"/>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="M16 22v12M21 22v12M26 22v12M31 22v12M13 32l21-8"/>'
                '<path opacity=".5" d="M16 40v10M21 40v10M26 40v10"/><g class="b"><path d="M50 46 58 20l2 1-8 26z"/><path d="M50 46l-1 4 3-3"/></g>',
        "parts": (("a", "0%,8%{stroke-dashoffset:1}74%,100%{stroke-dashoffset:0}", "24px 28px", "2.6s", "ease-in-out"),
                  ("b", "0%,100%{transform:translate(0px,0px)}50%{transform:translate(-2px,-3px)}", "54px 34px", "0.65s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Series-Hub/Records": {
        "draw": '<path d="M20 10h24v12a12 12 0 0 1-24 0z"/><path d="M20 14h-6a6 6 0 0 0 6 8M44 14h6a6 6 0 0 1-6 8M32 34v8M24 42h16v6H24zM20 52h24"/>'
                '<path class="a" d="M27 13l-3 12"/>'
                f'<polygon class="b" points="{_star(52, 40, 4, 1.7)}"/>',
        "parts": (("a", "0%{transform:translateX(-4px);opacity:0}30%{opacity:1}60%{transform:translateX(12px);opacity:0}100%{transform:translateX(12px);opacity:0}", "25px 19px", "2s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(.6) rotate(0deg);opacity:.4}50%{transform:scale(1.2) rotate(72deg);opacity:1}", "52px 40px", "2s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Series-Hub/Creator-Petition": {
        "draw": '<g class="a"><rect x="14" y="14" width="36" height="26" rx="1"/><path d="M19 21h18M19 26h22M19 31h14"/></g>'
                '<path d="M8 30v24h48V30"/><path d="M8 30l24 16 24-16"/>'
                f'<g class="b"><path transform="translate(32 50) scale(1.2)" d="{_HEART}"/></g>',
        "parts": (("a", "0%,100%{transform:translateY(8px)}50%{transform:translateY(-4px)}", "32px 27px", "2.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(1)}25%{transform:scale(1.3)}40%{transform:scale(1)}", "32px 50px", "1.2s", "ease-out")),
    },
    "Sports-and-Entertainment/Sports-Analytics/Player-Rankings": {
        "draw": '<path d="M8 56V42h16v14M24 56V32h16v24M40 56V46h16v10"/><path d="M30 38h4v8M15 48h3M45 51h4"/>'
                '<circle class="a" cx="32" cy="24" r="4.5"/>',
        "parts": (("a", "0%,100%{transform:translateY(0px) scale(1,1)}40%{transform:translateY(-7px) scale(1,1)}80%{transform:translateY(0px) scale(1.12,.88)}", "32px 28.5px", "1.1s", "ease-in-out"),),
    },
    "Sports-and-Entertainment/Sports-Analytics/Metric-Overview": {
        "draw": '<path d="M32 10l19 11v22L32 54 13 43V21z"/><path opacity=".45" d="M32 10v44M13 21l38 22M51 21 13 43"/>'
                '<path class="a" fill="currentColor" fill-opacity=".25" d="M32 18l12 8v14l-12 6-9-5V25z"/>',
        "parts": (("a", "0%,100%{transform:scale(1,1)}50%{transform:scale(.8,1.12)}", "32px 32px", "2.4s", "ease-in-out"),),
    },
    "Sports-and-Entertainment/Sports-Analytics/Statistics": {
        "draw": '<path d="M20 8h8a4 4 0 0 0 8 0h8l10 8-6 8-4-3v35H20V21l-4 3-6-8z"/>'
                '<path class="a" d="M26 34v14M32 30v18M38 38v10"/>',
        "parts": (("a", "0%,100%{transform:scaleY(1)}30%{transform:scaleY(.5)}65%{transform:scaleY(1.12)}", "32px 48px", "1.8s", "ease-in-out"),),
    },
    "Sports-and-Entertainment/Sports-Analytics/Predictions-and-Results": {
        "draw": '<path d="M8 14h10v8h8M8 30h10v-8M8 38h10v8h8M8 54h10v-8M26 22v24M26 34h20"/>'
                f'<polygon class="b" points="{_star(52, 34, 5, 2.2)}"/><circle class="a" cx="8" cy="14" r="2.5" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translate(0px,0px)}25%{transform:translate(10px,8px)}50%{transform:translate(18px,8px)}75%{transform:translate(18px,20px)}"
                        "92%,100%{transform:translate(38px,20px)}", "8px 14px", "3s", "ease-in-out"),
                  ("b", "0%,85%{transform:scale(.8);opacity:.4}93%{transform:scale(1.3);opacity:1}100%{transform:scale(.8);opacity:.4}", "52px 34px", "3s", "ease-out")),
    },
    "Sports-and-Entertainment/Sports-Analytics/Conditioning": {
        "draw": '<g class="a"><path d="M8 44c0-6 4-10 8-10l6-6 8 8h10c6 0 12 3 14 8v4H8z"/><path d="M8 48h46M26 36l-3 3M30 38l-3 3"/></g>'
                '<path class="b" d="M4 30h10M2 36h8M6 24h8"/>',
        "parts": (("a", "0%,100%{transform:translateY(0px) rotate(0deg)}40%{transform:translateY(-6px) rotate(-5deg)}70%{transform:translateY(0px) rotate(2deg)}", "30px 46px", "0.9s", "ease-in-out"),
                  ("b", "0%,100%{transform:translateX(0px);opacity:.3}50%{transform:translateX(-3px);opacity:1}", "8px 30px", "0.9s", "ease-in-out")),
    },
    "Sports-and-Entertainment/Sports-Analytics/Shenanigans": {
        "draw": '<g class="b"><circle cx="32" cy="22" r="10"/><path class="a" d="M24 22h16M32 12v20M27 14.5c3.5 4 3.5 11 0 15M37 14.5c-3.5 4-3.5 11 0 15"/></g>'
                '<path d="M32 32v14M27 54c0-5 2-8 5-8s5 3 5 8"/>',
        "parts": (("a", "0%{transform:rotate(15deg)}100%{transform:rotate(-165deg)}", "32px 22px", "0.8s", "linear"),
                  ("b", "0%,100%{transform:translateX(0px)}25%{transform:translateX(-1px)}75%{transform:translateX(1px)}", "32px 32px", "0.8s", "ease-in-out")),
    },
}
