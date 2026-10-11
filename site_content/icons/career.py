"""Career & Education icons: jobs, coursework, Waterloo memories, projects, plans and abstract career-path emblems."""

import math


def _burst(cx: float, cy: float, inner: float, outer: float, count: int = 12, start: float = 0) -> str:
    lines = []
    for i in range(count):
        angle = math.radians(start + i * 360 / count)
        c, s = math.cos(angle), math.sin(angle)
        lines.append(f"M{cx + inner * c:.1f} {cy + inner * s:.1f}L{cx + outer * c:.1f} {cy + outer * s:.1f}")
    return "".join(lines)


_HEART = "M48 43c-6-4-8-7-8-10a4 4 0 0 1 8-1.5A4 4 0 0 1 56 33c0 3-2 6-8 10z"

ICONS = {
    "Career-and-Education": {
        "draw": '<g class="a"><path d="M32 12 58 24 32 36 6 24z"/><path d="M16 29v10c0 4 7 7 16 7s16-3 16-7V29"/>'
                '<g class="b"><path d="M52 26v12"/><circle cx="52" cy="40" r="2" fill="currentColor" stroke="none"/></g></g>',
        "parts": (("a", "0%,100%{transform:translateY(0px) rotate(0deg)}35%{transform:translateY(-6px) rotate(-6deg)}60%{transform:translateY(0px) rotate(2deg)}",
                   "32px 30px", "1.8s", "ease-in-out"),
                  ("b", "0%,100%{transform:rotate(0deg)}30%{transform:rotate(16deg)}60%{transform:rotate(-10deg)}", "52px 26px", "1.8s", "ease-in-out")),
    },
    "Career-and-Education/Job-Experiences": {
        "draw": '<path d="M8 40h48"/><circle cx="16" cy="40" r="2.5"/><circle cx="32" cy="40" r="2.5"/><circle cx="48" cy="40" r="2.5"/>'
                '<path d="M16 37.5V29M32 42.5V47M48 37.5V29"/><rect x="10" y="19" width="12" height="10" rx="2"/>'
                '<rect x="26" y="47" width="12" height="9" rx="2"/><rect x="42" y="19" width="12" height="10" rx="2"/>'
                '<circle class="a" cx="16" cy="40" r="5"/>',
        "parts": (("a", "0%,20%{transform:translateX(0px)}33%,53%{transform:translateX(16px)}66%,86%{transform:translateX(32px)}100%{transform:translateX(0px)}",
                   "16px 40px", "3.6s", "ease-in-out"),),
    },
    "Career-and-Education/Educational-Favourites": {
        "draw": '<path d="M32 22c-6-4-14-5-22-4v32c8-1 16 0 22 4 6-4 14-5 22-4V18c-8-1-16 0-22 4zM32 22v32"/>'
                '<path class="b" d="M32 22c4-3 9-4 14-4v28c-5 0-10 1-14 4"/>'
                '<path class="a" d="M32 15c-4-2.5-6-4.5-6-6.5a3 3 0 0 1 6-1 3 3 0 0 1 6 1c0 2-2 4-6 6.5z"/>',
        "parts": (("a", "0%,100%{transform:translateY(0px) scale(1)}50%{transform:translateY(-2px) scale(1.18)}", "32px 10px", "1.6s", "ease-in-out"),
                  ("b", "0%,15%,100%{transform:scaleX(1)}55%,70%{transform:scaleX(-1)}", "32px 34px", "3.2s", "ease-in-out")),
    },
    "Career-and-Education/Waterloo-Highlights": {
        "draw": '<rect x="10" y="12" width="28" height="34" rx="1.5" transform="rotate(-10 24 46)"/>'
                '<g class="a"><rect x="22" y="14" width="28" height="34" rx="1.5"/><rect x="25" y="17" width="22" height="20"/>'
                '<path d="M25 33l7-8 5 5 4-3 6 6"/><circle cx="41" cy="22" r="2"/></g>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}45%,60%{transform:rotate(12deg)}", "30px 48px", "2.4s", "ease-in-out"),),
    },
    "Career-and-Education/Projects": {
        "draw": '<polygon points="34,15.5 45.4,23.7 42,28.5 30.6,20.3" class="a"/><path d="M46 50 30 27"/>'
                '<circle cx="27" cy="22" r="5.5"/><path d="M27 22l-3-6M27 22l6-2"/>'
                '<path class="b" d="M48 14l3-3M50 20h4M44 10V6"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}30%{transform:rotate(-14deg)}45%{transform:rotate(4deg)}55%{transform:rotate(0deg)}",
                   "18px 50px", "1.4s", "ease-in-out"),
                  ("b", "0%,26%,50%,100%{opacity:0}32%,42%{opacity:1}", "50px 13px", "1.4s", "linear")),
    },
    "Career-and-Education/Future-Planning": {
        "draw": '<g class="a"><polygon points="12.5,37.4 41.7,18.1 46.3,25.9 15.5,42.6"/><path d="M14 40l-4 2.5"/></g>'
                '<path d="M29 33 20 56M29 33v23M29 33l9 23"/>'
                '<path class="b" d="M52 5l1.5 3.5L57 10l-3.5 1.5L52 15l-1.5-3.5L47 10l3.5-1.5z"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}40%{transform:rotate(-6deg)}70%{transform:rotate(3deg)}", "29px 31px", "3s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(.7);opacity:.5}50%{transform:scale(1.2);opacity:1}", "52px 10px", "1.5s", "ease-in-out")),
    },
    "Career-and-Education/Career-Paths": {
        "draw": '<path d="M32 56V38"/><circle cx="32" cy="56" r="1.5" fill="currentColor" stroke="none"/>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="M32 38c0-8-14-10-16-24M32 38V12M32 38c0-8 14-10 16-24"/>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="16" cy="11" r="3"/><circle cx="32" cy="9" r="3"/><circle cx="48" cy="11" r="3"/></g>',
        "parts": (("a", "0%{stroke-dashoffset:1}50%,85%{stroke-dashoffset:0}100%{stroke-dashoffset:1}", "32px 30px", "3s", "ease-out"),
                  ("b", "0%,45%{opacity:0}60%{opacity:1}88%{opacity:1}100%{opacity:0}", "32px 11px", "3s", "linear")),
    },
    "Career-and-Education/Job-Experiences/Quantum-Molecular-Dynamics-Simulations": {
        "draw": '<path d="M6 22h52M6 42h52"/><path opacity=".45" d="M10 22l4 4h8l4-4M34 22l4 4h8l4-4M10 42l4-4h8l4 4M34 42l4-4h8l4 4"/>'
                '<g class="a"><circle cx="32" cy="31" r="4.5"/><g class="b"><path d="M29 34 26.5 36.5M35 34l2.5 2.5"/>'
                '<circle cx="25" cy="38" r="2.3"/><circle cx="39" cy="38" r="2.3"/></g></g>',
        "parts": (("a", "0%{transform:translateX(-10px) rotate(0deg)}50%{transform:translateX(10px) rotate(180deg)}100%{transform:translateX(-10px) rotate(360deg)}",
                   "32px 33px", "3s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(1)}50%{transform:scale(1.12,.9)}", "32px 32px", "0.6s", "ease-in-out")),
    },
    "Career-and-Education/Job-Experiences/Process-Engineering": {
        "draw": '<rect x="6" y="24" width="12" height="16" rx="2"/><path d="M32 22l10 10-10 10-10-10z"/><rect x="46" y="24" width="12" height="16" rx="2"/>'
                '<path d="M18 32h4M42 32h4"/><path class="b" stroke-dasharray="3 3.5" d="M52 40v10H12V40"/><path d="M9 43l3-3 3 3"/>'
                '<circle class="a" cx="12" cy="32" r="2.5" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translateX(0px);opacity:0}10%{opacity:1}90%{opacity:1}100%{transform:translateX(40px);opacity:0}", "12px 32px", "2.4s", "linear"),
                  ("b", "0%{stroke-dashoffset:0}100%{stroke-dashoffset:-6.5}", "32px 45px", "0.6s", "linear")),
    },
    "Career-and-Education/Job-Experiences/Business-Intelligence": {
        "draw": '<rect x="8" y="10" width="48" height="32" rx="3"/><path d="M26 42l-3 10h18l-3-10M20 52h24"/>'
                '<circle opacity=".35" cx="20" cy="26" r="7"/><circle class="b" cx="20" cy="26" r="7" stroke-dasharray="14 30"/>'
                '<path class="a" d="M33 36v-8M38 36V20M43 36V25M48 36V17"/>',
        "parts": (("a", "0%,100%{transform:scaleY(1)}30%{transform:scaleY(.6)}60%{transform:scaleY(1.1)}", "40px 36px", "2s", "ease-in-out"),
                  ("b", "0%{transform:rotate(-90deg)}100%{transform:rotate(270deg)}", "20px 26px", "2s", "linear")),
    },
    "Career-and-Education/Job-Experiences/Corporate-Research-and-Development": {
        "draw": '<path d="M15 14h34M18 14v34a6 6 0 0 0 6 6h16a6 6 0 0 0 6-6V14"/><path d="M18 36h28"/>'
                '<g class="a"><circle cx="25" cy="31" r="4"/><circle cx="32" cy="28" r="5"/><circle cx="39" cy="31" r="4"/>'
                '<circle cx="28" cy="22" r="3"/><circle cx="36" cy="21" r="3.5"/></g>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="26" cy="47" r="1.3"/><circle cx="36" cy="44" r="1"/></g>',
        "parts": (("a", "0%,100%{transform:scale(1,.55)}50%{transform:scale(1.03,1.05)}", "32px 36px", "2.4s", "ease-in-out"),
                  ("b", "0%{transform:translateY(4px);opacity:0}30%{opacity:1}100%{transform:translateY(-8px);opacity:0}", "31px 45px", "1.2s", "ease-out")),
    },
    "Career-and-Education/Job-Experiences/Materials-Engineer": {
        "draw": '<path d="M18 4v6M46 4v6M18 54v6M46 54v6" opacity=".5"/><path d="M20 26h3M20 40h3"/>'
                '<path class="a" d="M24 10h16v8l-4 4v20l4 4v8H24v-8l4-4V22l-4-4z"/>',
        "parts": (("a", "0%,100%{transform:scaleY(1)}55%{transform:scaleY(1.08)}65%{transform:scaleY(1.06)}", "32px 32px", "1.8s", "ease-in-out"),),
    },
    "Career-and-Education/Job-Experiences/Lifeguarding-Days": {
        "draw": '<g class="a"><circle cx="32" cy="28" r="12"/><circle cx="32" cy="28" r="6"/>'
                '<path d="M36.2 23.8l4.3-4.3M27.8 23.8l-4.3-4.3M27.8 32.2l-4.3 4.3M36.2 32.2l4.3 4.3"/></g>'
                '<path class="b" d="M6 48q5-4 10 0t10 0 10 0 10 0 10 0"/><path opacity=".5" d="M10 55q5-3 10 0t10 0 10 0 10 0"/>',
        "parts": (("a", "0%,100%{transform:translateY(0px) rotate(0deg)}50%{transform:translateY(3px) rotate(8deg)}", "32px 28px", "2.2s", "ease-in-out"),
                  ("b", "0%,100%{transform:translateX(-2px)}50%{transform:translateX(3px)}", "31px 48px", "2.2s", "ease-in-out")),
    },
    "Career-and-Education/Educational-Favourites/Statistical-Thermodynamics": {
        "draw": '<path d="M8 10v42h36"/><path class="a" d="M10 50c4 0 6-28 12-28s10 18 24 26"/>'
                '<path d="M50 12a3 3 0 0 1 6 0v26a5 5 0 1 1-6 0z"/><path class="b" d="M53 42V28"/>',
        "parts": (("a", "0%,100%{transform:scale(1,1)}50%{transform:scale(1.2,.8)}", "10px 50px", "2.6s", "ease-in-out"),
                  ("b", "0%,100%{transform:scaleY(.6)}50%{transform:scaleY(1.3)}", "53px 42px", "2.6s", "ease-in-out")),
    },
    "Career-and-Education/Educational-Favourites/Continuum-Mechanics": {
        "draw": '<circle cx="32" cy="32" r="7"/>'
                '<g class="a" stroke-dasharray="4 4"><path d="M6 24c12 0 16-6 26-6s14 6 26 6M6 40c12 0 16 6 26 6s14-6 26-6"/>'
                '<path d="M6 13c14 0 18-3 26-3s12 3 26 3M6 51c14 0 18 3 26 3s12-3 26-3"/></g>'
                '<path class="b" d="M42 32c2-2 5-1 5 1s-3 3-4 1"/>',
        "parts": (("a", "0%{stroke-dashoffset:8}100%{stroke-dashoffset:0}", "32px 32px", "0.8s", "linear"),
                  ("b", "0%{transform:rotate(0deg)}100%{transform:rotate(-180deg)}", "44px 33px", "1.6s", "linear")),
    },
    "Career-and-Education/Educational-Favourites/Vector-Calculus": {
        "draw": '<circle class="b" cx="32" cy="32" r="18" stroke-dasharray="6 5"/><path d="M29 11l4 3-4 3"/>'
                '<path transform="rotate(120 32 32)" d="M29 11l4 3-4 3"/><path transform="rotate(240 32 32)" d="M29 11l4 3-4 3"/>'
                '<g class="a"><path d="M32 24v16M24 32h16"/><circle cx="32" cy="32" r="2"/></g>',
        "parts": (("a", "0%{transform:rotate(0deg)}100%{transform:rotate(180deg)}", "32px 32px", "2s", "linear"),
                  ("b", "0%{stroke-dashoffset:0}100%{stroke-dashoffset:-11}", "32px 32px", "1.1s", "linear")),
    },
    "Career-and-Education/Educational-Favourites/Nanofabrication": {
        "draw": '<path d="M24 6h16l-3 6H27z"/><path class="a" stroke-dasharray="3 4" d="M28 14v24M32 14v24M36 14v24"/>'
                '<path d="M14 30h12M38 30h12" stroke-width="3"/><rect x="12" y="44" width="40" height="7"/><rect x="12" y="40" width="40" height="4"/>'
                '<rect class="b" x="28" y="40" width="8" height="4" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{stroke-dashoffset:0}100%{stroke-dashoffset:-7}", "32px 26px", "0.7s", "linear"),
                  ("b", "0%,40%{opacity:0}75%,100%{opacity:1}", "32px 42px", "2.4s", "ease-in")),
    },
    "Career-and-Education/Educational-Favourites/Integrated-Circuits": {
        "draw": '<rect x="22" y="12" width="20" height="40" rx="2"/><path d="M29 12a3 3 0 0 0 6 0"/>'
                '<path d="M22 18h-5M22 26h-5M22 34h-5M22 42h-5M42 18h5M42 26h5M42 34h5M42 42h5"/>'
                '<path opacity=".35" d="M17 18h10v10h10v14h10"/>'
                '<path class="a" pathLength="1" stroke-dasharray="0.18 0.82" d="M17 18h10v10h10v14h10"/>'
                '<circle class="b" cx="26" cy="17" r="1.4" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{stroke-dashoffset:1}100%{stroke-dashoffset:0}", "32px 30px", "1.6s", "linear"),
                  ("b", "0%,100%{opacity:.3}45%,55%{opacity:1}", "26px 17px", "1.6s", "ease-in-out")),
    },
    "Career-and-Education/Educational-Favourites/Semiconductor-Physics": {
        "draw": '<path d="M8 18h48M8 46h48"/><path opacity=".3" d="M8 32h48" stroke-dasharray="2 4"/>'
                '<circle class="b" cx="32" cy="46" r="3"/><circle class="a" cx="32" cy="46" r="3" fill="currentColor" stroke="none"/>'
                '<path class="c" d="M10 32q2-3 4 0t4 0 4 0 4 0m-3-3 3 3-3 3"/>',
        "parts": (("a", "0%,20%{transform:translateY(0px)}45%,80%{transform:translateY(-28px)}100%{transform:translateY(0px)}", "32px 46px", "2.6s", "ease-in-out"),
                  ("b", "0%,20%{opacity:0}45%,80%{opacity:1}100%{opacity:0}", "32px 46px", "2.6s", "ease-in-out"),
                  ("c", "0%,100%{opacity:0;transform:translateX(-4px)}15%,30%{opacity:1;transform:translateX(4px)}", "18px 32px", "2.6s", "ease-out")),
    },
    "Career-and-Education/Waterloo-Highlights/Varsity-Cheerleading": {
        "draw": f'<g class="a"><path d="{_burst(20, 22, 3, 10)}"/><path d="M22 30l6 22"/></g>'
                f'<g class="b"><path d="{_burst(44, 22, 3, 10, start=15)}"/><path d="M42 30l-6 22"/></g>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}20%{transform:rotate(-12deg)}40%{transform:rotate(6deg)}60%{transform:rotate(-8deg)}80%{transform:rotate(3deg)}",
                   "28px 52px", "1s", "ease-in-out"),
                  ("b", "0%,100%{transform:rotate(0deg)}20%{transform:rotate(12deg)}40%{transform:rotate(-6deg)}60%{transform:rotate(8deg)}80%{transform:rotate(-3deg)}",
                   "36px 52px", "1s", "ease-in-out")),
    },
    "Career-and-Education/Waterloo-Highlights/Shenanigans": {
        "draw": '<path d="M10 54l8-22 14 14z"/><path d="M14 43l7 7M16 38l10 10"/>'
                '<g class="a"><path d="M34 24l3-3M42 30h4M30 14l1-4M48 18l3-2M40 10l2-3M50 40l4 1"/>'
                '<g fill="currentColor" stroke="none"><circle cx="38" cy="16" r="1.5"/><circle cx="46" cy="26" r="1.3"/><circle cx="52" cy="32" r="1.2"/></g></g>'
                '<path class="b" pathLength="1" stroke-dasharray="1" d="M26 36c4-6 8-4 10-10s6-6 10-8"/>',
        "parts": (("a", "0%{transform:scale(.2);opacity:0}20%{opacity:1}70%{transform:scale(1.1);opacity:1}100%{transform:scale(1.2);opacity:0}", "25px 39px", "1.8s", "ease-out"),
                  ("b", "0%{stroke-dashoffset:1}40%,80%{stroke-dashoffset:0}100%{stroke-dashoffset:-1}", "36px 27px", "1.8s", "ease-out")),
    },
    "Career-and-Education/Waterloo-Highlights/Relationships": {
        "draw": f'<g class="a"><path transform="translate(-37.4 -14.8) scale(1.3)" d="{_HEART}"/></g>'
                f'<g class="b"><path transform="translate(-13.8 -5.6) scale(1.1)" d="{_HEART}"/></g>',
        "parts": (("a", "0%,100%{transform:scale(1)}15%{transform:scale(1.12)}30%{transform:scale(.98)}45%{transform:scale(1.06)}", "25px 32px", "1.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(1)}15%{transform:scale(1.1)}30%{transform:scale(.97)}45%{transform:scale(1.05)}", "39px 34px", "1.4s", "ease-in-out", "0.35s")),
    },
    "Career-and-Education/Waterloo-Highlights/Adventures-and-Highlights": {
        "draw": '<path d="M6 50l16-24 10 14 8-10 18 20z"/><path opacity=".6" stroke-dasharray="2 3" d="M14 50c6-4 10-8 16-8s8-6 12-12"/>'
                '<circle cx="48" cy="14" r="4"/><path class="b" d="M48 6V4M48 22v2M40 14h-2M56 14h2M42.3 8.3 41 7M53.7 19.7 55 21M42.3 19.7 41 21M53.7 8.3 55 7"/>'
                '<circle class="a" cx="14" cy="50" r="2.4" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translate(0px,0px);opacity:0}10%{opacity:1}25%{transform:translate(8px,-5px)}50%{transform:translate(16px,-8px)}"
                        "75%{transform:translate(22px,-12px)}90%{transform:translate(28px,-20px);opacity:1}100%{transform:translate(28px,-20px);opacity:0}",
                   "14px 50px", "3s", "linear"),
                  ("b", "0%{transform:rotate(45deg)}100%{transform:rotate(90deg)}", "48px 14px", "2s", "linear")),
    },
    "Career-and-Education/Waterloo-Highlights/Academic-Excellence": {
        "draw": '<rect x="10" y="12" width="44" height="28" rx="3"/><path d="M16 20h24M16 26h18M16 32h12"/>'
                '<g class="a"><circle cx="44" cy="40" r="6"/><path d="M40 45l-3 9 4-2 2 4 2-8M48 45l3 9-4-2-2 4-2-8"/></g>'
                '<path class="b" d="M44 30v-3M52 35l2-2M36 35l-2-2"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}25%{transform:rotate(-12deg)}50%{transform:rotate(8deg)}75%{transform:rotate(-4deg)}", "44px 34px", "2s", "ease-in-out"),
                  ("b", "0%,100%{opacity:0;transform:scale(.8)}40%{opacity:1;transform:scale(1.15)}", "44px 36px", "2s", "ease-out")),
    },
    "Career-and-Education/Waterloo-Highlights/Little-Things": {
        "draw": '<path d="M14 28h30v12a12 12 0 0 1-12 12h-6a12 12 0 0 1-12-12z"/><path d="M44 32h4a5 5 0 0 1 0 10h-4"/><path d="M10 57h40"/>'
                '<path class="a" d="M22 22c-3-4 3-6 0-10M30 22c-3-4 3-6 0-10M38 22c-3-4 3-6 0-10"/>'
                '<path class="b" d="M29 44c-3-2-4-3.5-4-5a2 2 0 0 1 4-.7 2 2 0 0 1 4 .7c0 1.5-1 3-4 5z"/>',
        "parts": (("a", "0%{transform:translateY(4px);opacity:0}40%{opacity:.9}100%{transform:translateY(-4px);opacity:0}", "30px 17px", "2.2s", "ease-out"),
                  ("b", "0%,100%{transform:scale(.9)}50%{transform:scale(1.22)}", "29px 41px", "1.1s", "ease-in-out")),
    },
    "Career-and-Education/Projects/KUBO-NO2-Sensor": {
        "draw": '<rect x="10" y="24" width="32" height="28" rx="2"/><path d="M14 28h24M18 28v16M26 28v16M34 28v16M14 48h24M22 48V32M30 48V32M38 48V32"/>'
                '<path d="M42 44h6"/><circle class="a" cx="52" cy="44" r="3.2" fill="currentColor" stroke="none"/>'
                '<path class="b" d="M46 12l2 3 2-3M52 22l2 3 2-3M40 6l2 3 2-3"/>',
        "parts": (("a", "0%,100%{opacity:.25}60%,80%{opacity:1}", "52px 44px", "2.4s", "ease-in-out"),
                  ("b", "0%{transform:translate(4px,-4px);opacity:0}30%{opacity:1}100%{transform:translate(-6px,8px);opacity:0}", "48px 14px", "2.4s", "ease-in")),
    },
    "Career-and-Education/Projects/Pandas-Projects": {
        "draw": '<rect x="10" y="14" width="44" height="36" rx="2"/><path d="M10 22h44M24 14v36M38 14v36M10 30h44M10 38h44M10 46h44" opacity=".8"/>'
                '<rect class="a" x="11" y="23" width="42" height="6" rx="1" fill="currentColor" fill-opacity=".25"/>'
                '<path class="b" d="M14 57l8-3 6 1 8-4 8 2"/>',
        "parts": (("a", "0%,20%{transform:translateY(0px)}33%,53%{transform:translateY(8px)}66%,86%{transform:translateY(16px)}100%{transform:translateY(0px)}",
                   "32px 26px", "3.2s", "ease-in-out"),
                  ("b", "0%,100%{transform:scaleY(1)}50%{transform:scaleY(1.6)}", "29px 56px", "1.6s", "ease-in-out")),
    },
    "Career-and-Education/Projects/WebDev-Consulting": {
        "draw": '<g class="a"><path d="M8 12h28v18H18l-6 6v-6H8z"/><path d="M17 18l-3 3 3 3M27 18l3 3-3 3M23 17l-2 8"/></g>'
                '<g class="b"><path d="M28 34h28v16h-4v6l-6-6H28z"/><path d="M36 42l4 4 8-7"/></g>',
        "parts": (("a", "0%,100%{transform:translateY(0px)}30%{transform:translateY(-2px)}", "22px 21px", "2.4s", "ease-in-out"),
                  ("b", "0%,30%{transform:scale(0);opacity:0}50%{transform:scale(1.1);opacity:1}60%,100%{transform:scale(1);opacity:1}", "42px 42px", "2.4s", "ease-out")),
    },
    "Career-and-Education/Projects/Raspberry-Pi": {
        "draw": '<rect x="8" y="16" width="44" height="32" rx="3"/><circle cx="12" cy="20" r="1.4"/><circle cx="48" cy="20" r="1.4"/>'
                '<circle cx="12" cy="44" r="1.4"/><circle cx="48" cy="44" r="1.4"/><rect x="20" y="28" width="12" height="12" rx="1"/>'
                '<rect x="46" y="26" width="10" height="6"/><rect x="46" y="36" width="10" height="6"/>'
                '<path class="b" stroke-width="2.6" stroke-dasharray="0.1 4" d="M16 21h26"/>'
                '<circle class="a" cx="14" cy="42" r="1.6" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%,50%,100%{opacity:1}25%,75%{opacity:.15}", "14px 42px", "1.2s", "steps(1,end)"),
                  ("b", "0%{stroke-dashoffset:0}100%{stroke-dashoffset:4.1}", "29px 21px", "0.8s", "linear")),
    },
    "Career-and-Education/Projects/Mental-Map": {
        "draw": '<rect x="14" y="8" width="38" height="48" rx="3"/>'
                '<g><circle cx="14" cy="16" r="2"/><circle cx="14" cy="26" r="2"/><circle cx="14" cy="36" r="2"/><circle cx="14" cy="46" r="2"/></g>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="M30.5 30 22 22M37.5 30 46 21M34 36v10M31 34l-7 6"/>'
                '<circle class="b" cx="34" cy="32" r="4"/><circle cx="22" cy="22" r="2"/><circle cx="46" cy="21" r="2"/><circle cx="34" cy="48" r="2"/><circle cx="23" cy="41" r="2"/>',
        "parts": (("a", "0%,12%{stroke-dashoffset:1}62%,100%{stroke-dashoffset:0}", "34px 32px", "2.6s", "ease-out"),
                  ("b", "0%,100%{transform:scale(1)}50%{transform:scale(1.3)}", "34px 32px", "1.3s", "ease-in-out")),
    },
    "Career-and-Education/Projects/Future-Plans": {
        "draw": '<rect x="12" y="14" width="40" height="40" rx="3"/><path d="M22 10v8M42 10v8M12 24h40"/>'
                '<path stroke-width="2.6" stroke-dasharray="0.1 7" d="M18 32h28M18 40h28M18 48h21"/>'
                '<path class="b" d="M46 44.5l1.2 2.3 2.3 1.2-2.3 1.2-1.2 2.3-1.2-2.3-2.3-1.2 2.3-1.2z"/>'
                '<circle class="a" cx="18" cy="32" r="3.5"/>',
        "parts": (("a", "0%,15%{transform:translate(0px,0px)}35%{transform:translate(14px,0px)}55%{transform:translate(14px,8px)}75%,100%{transform:translate(28px,16px)}",
                   "18px 32px", "3.2s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(.85) rotate(0deg)}50%{transform:scale(1.25) rotate(45deg)}", "46px 48px", "1.6s", "ease-in-out")),
    },
    "Career-and-Education/Future-Planning/E-Learning": {
        "draw": '<rect x="12" y="12" width="40" height="28" rx="2"/><path d="M6 44h52l-4 4H10z"/><path opacity=".35" d="M18 35h28"/>'
                '<path class="b" pathLength="1" stroke-dasharray="1" d="M18 35h28"/><path class="a" d="M29 18v12l10-6z"/>',
        "parts": (("a", "0%,100%{transform:scale(1)}40%{transform:scale(1.18)}60%{transform:scale(.96)}", "32px 24px", "1.6s", "ease-in-out"),
                  ("b", "0%{stroke-dashoffset:1}80%,100%{stroke-dashoffset:0}", "32px 35px", "3.2s", "linear")),
    },
    "Career-and-Education/Future-Planning/Europe-Migration": {
        "draw": '<path opacity=".6" stroke-dasharray="2 3" d="M10 46q22-32 44-6"/><circle cx="10" cy="46" r="2"/>'
                '<g class="b"><path d="M54 40c-3.5-4-5-6.5-5-8.5a5 5 0 0 1 10 0c0 2-1.5 4.5-5 8.5z"/><circle cx="54" cy="31.5" r="1.6"/></g>'
                '<path class="a" d="M16 46 6 41l2.5 5L6 51z"/>',
        "parts": (("a", "0%{transform:translate(0px,0px) rotate(-55deg);opacity:0}8%{opacity:1}25%{transform:translate(11px,-12.4px) rotate(-38deg)}"
                        "50%{transform:translate(22px,-17.5px) rotate(-8deg)}75%{transform:translate(33px,-15.4px) rotate(28deg)}92%{opacity:1}"
                        "100%{transform:translate(44px,-6px) rotate(50deg);opacity:0}", "10px 46px", "3.2s", "linear"),
                  ("b", "0%,70%,100%{transform:translateY(0px)}80%{transform:translateY(-3px)}90%{transform:translateY(0px)}", "54px 40px", "3.2s", "ease-out")),
    },
    "Career-and-Education/Future-Planning/Networking-and-Connections": {
        "draw": '<g class="a"><rect x="8" y="16" width="24" height="15" rx="2"/><circle cx="14" cy="23.5" r="2.5"/><path d="M20 21h8M20 26h6"/></g>'
                '<g class="b"><rect x="32" y="30" width="24" height="15" rx="2"/><circle cx="38" cy="37.5" r="2.5"/><path d="M44 35h8M44 40h6"/></g>'
                '<path d="M26 54a4 4 0 0 1 0-8h4M38 46a4 4 0 0 1 0 8h-4M28 50h8"/>',
        "parts": (("a", "0%,100%{transform:translate(0px,0px) rotate(0deg)}50%{transform:translate(6px,4px) rotate(4deg)}", "20px 23px", "2.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:translate(0px,0px) rotate(0deg)}50%{transform:translate(-6px,-4px) rotate(-4deg)}", "44px 37px", "2.4s", "ease-in-out")),
    },
    "Career-and-Education/Future-Planning/Creative-Endeavours": {
        "draw": '<path d="M30 10c-13 0-22 9-22 20 0 10 7 16 14 14 4-1 3-6 7-7s9 3 13 0c4-3 6-7 6-11 0-9-8-16-18-16z"/>'
                '<g fill="currentColor" stroke="none"><circle cx="20" cy="24" r="2.4"/><circle cx="28" cy="18" r="2.4"/><circle cx="38" cy="20" r="2.4"/><circle cx="18" cy="33" r="2.4"/></g>'
                '<g class="a"><path d="M44 36l12-16"/><path d="M44 36l-3 5 5-2z"/></g>'
                '<path class="b" pathLength="1" stroke-dasharray="1" d="M14 54c8-4 14 2 22-2s12-2 16 0"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}50%{transform:rotate(-14deg)}", "56px 20px", "1.6s", "ease-in-out"),
                  ("b", "0%,8%{stroke-dashoffset:1}70%,100%{stroke-dashoffset:0}", "33px 53px", "1.6s", "ease-out")),
    },
    "Career-and-Education/Future-Planning/New-Age-Promotion": {
        "draw": '<g class="b"><path d="M12 26h6l20-10v32L18 38h-6z"/><path d="M18 38l2 8h4l-1-6"/></g>'
                '<path class="a" d="M44 26a8 8 0 0 1 0 12M48 21a14 14 0 0 1 0 22"/>',
        "parts": (("a", "0%{transform:scale(.8);opacity:0}30%{opacity:1}100%{transform:scale(1.25);opacity:0}", "40px 32px", "1.2s", "ease-out"),
                  ("b", "0%,100%{transform:rotate(0deg)}20%{transform:rotate(-4deg)}", "18px 32px", "1.2s", "ease-out")),
    },
    "Career-and-Education/Future-Planning/Roadmap-to-Logan": {
        "draw": '<path d="M8 56c2-12 20-10 20-20s-8-12-6-18M44 56c0-10-6-12-6-20s-6-14-10-18"/>'
                '<path class="a" stroke-dasharray="3 4" d="M26 56c0-11 10-11 10-20s-7-13-9-18"/>'
                '<path d="M26 18V6"/><path class="b" d="M26 6h8l-2 2.5 2 2.5h-8"/>',
        "parts": (("a", "0%{stroke-dashoffset:7}100%{stroke-dashoffset:0}", "31px 37px", "0.9s", "linear"),
                  ("b", "0%,100%{transform:skewY(0deg)}50%{transform:skewY(-12deg)}", "26px 8px", "1.2s", "ease-in-out")),
    },
    "Career-and-Education/Career-Paths/Logan": {
        "draw": '<path d="M6 54l20-34 10 14 6-8 16 28z"/><path opacity=".6" stroke-dasharray="2 2.5" d="M16 54l12-6-8-6 12-6-6-6"/>'
                '<path d="M26 20v-9"/><path class="b" d="M26 11h7l-2 2 2 2h-7"/>'
                '<circle class="a" cx="16" cy="54" r="2.2" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translate(0px,0px)}22%{transform:translate(12px,-6px)}44%{transform:translate(4px,-12px)}66%{transform:translate(16px,-18px)}"
                        "88%,100%{transform:translate(10px,-24px)}", "16px 54px", "3.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:scaleX(1)}50%{transform:scaleX(.7)}", "26px 13px", "0.9s", "ease-in-out")),
    },
    "Career-and-Education/Career-Paths/Amar": {
        "draw": '<circle cx="32" cy="32" r="8"/><g class="b"><ellipse cx="32" cy="32" rx="17" ry="5" transform="rotate(-20 32 32)"/></g>'
                '<g class="a"><circle cx="52" cy="32" r="2.6" fill="currentColor" stroke="none"/></g>',
        "parts": (("a", "0%{transform:rotate(30deg)}100%{transform:rotate(390deg)}", "32px 32px", "4.5s", "linear"),
                  ("b", "0%,100%{transform:rotate(0deg)}50%{transform:rotate(9deg)}", "32px 32px", "3s", "ease-in-out")),
    },
    "Career-and-Education/Career-Paths/Rhema": {
        "draw": '<path d="M8 54h10V44h10V34h10V24h10V14h8"/><path opacity=".4" d="M8 58h48"/>'
                '<circle class="a" cx="13" cy="41" r="3"/><path class="b" d="M54 5l1 2 2 1-2 1-1 2-1-2-2-1 2-1z"/>',
        "parts": (("a", "0%{transform:translate(0px,0px);opacity:1}12%{transform:translate(5px,-8px)}25%{transform:translate(10px,-10px)}37%{transform:translate(15px,-18px)}"
                        "50%{transform:translate(20px,-20px)}62%{transform:translate(25px,-28px)}75%{transform:translate(30px,-30px)}88%{transform:translate(30px,-30px);opacity:1}"
                        "100%{transform:translate(30px,-30px);opacity:0}", "13px 41px", "2.8s", "ease-out"),
                  ("b", "0%,70%{opacity:.2;transform:scale(.8)}85%{opacity:1;transform:scale(1.3)}100%{opacity:.2;transform:scale(.8)}", "54px 8px", "2.8s", "ease-in-out")),
    },
    "Career-and-Education/Career-Paths/Owen": {
        "draw": '<circle cx="32" cy="32" r="20"/><path d="M32 12v4M32 48v4M12 32h4M48 32h4"/><circle cx="32" cy="32" r="2"/>'
                '<path class="a" d="M32 18l4 14-4 14-4-14z"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}20%{transform:rotate(-40deg)}45%{transform:rotate(22deg)}65%{transform:rotate(-10deg)}82%{transform:rotate(4deg)}",
                   "32px 32px", "3s", "ease-in-out"),),
    },
    "Career-and-Education/Career-Paths/Liam": {
        "draw": '<path class="a" pathLength="1" stroke-dasharray="1" d="M12 40 22 24 34 30 44 14M34 30 52 34"/>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="12" cy="40" r="2.4"/><circle cx="22" cy="24" r="2.4"/><circle cx="34" cy="30" r="2.8"/>'
                '<circle cx="44" cy="14" r="2.4"/><circle cx="52" cy="34" r="2.4"/></g><path opacity=".4" d="M14 52h2M28 48h1M46 50h2"/>',
        "parts": (("a", "0%,5%{stroke-dashoffset:1}55%,100%{stroke-dashoffset:0}", "32px 27px", "3s", "ease-in-out"),
                  ("b", "0%,100%{opacity:.6}25%{opacity:1}50%{opacity:.4}75%{opacity:1}", "32px 27px", "3s", "linear")),
    },
    "Career-and-Education/Career-Paths/Calena": {
        "draw": '<path d="M26 54l3-30h6l3 30z"/><rect x="27" y="18" width="10" height="6"/><path d="M25 18l7-6 7 6z"/><path d="M28.2 44h7.6M28.9 34h6.2"/>'
                '<path class="a" d="M37 19l20-6M37 23l20 6"/><path class="b" d="M6 57q4-3 8 0t8 0 8 0 8 0 8 0 8 0"/>',
        "parts": (("a", "0%,100%{transform:rotate(-14deg)}50%{transform:rotate(14deg)}", "32px 21px", "2.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:translateX(-1px)}50%{transform:translateX(4px)}", "32px 57px", "2.4s", "ease-in-out")),
    },
}
