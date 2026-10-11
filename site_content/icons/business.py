"""Business & Economics icons: law, markets, metrics, industries and company case studies."""

_STAR = "{0},{1} {2},{3} {4},{5} {6},{7} {8},{9} {10},{11} {12},{13} {14},{15} {16},{17} {18},{19}"


def _star(cx: float, cy: float) -> str:
    offsets = (0, -4.5, 1.12, -1.54, 4.28, -1.39, 1.81, .59, 2.65, 3.64, 0, 1.9, -2.65, 3.64, -1.81, .59, -4.28, -1.39, -1.12, -1.54)
    return _STAR.format(*(round((cx, cy)[i % 2] + value, 2) for i, value in enumerate(offsets)))


_BLADE = "M32 24c-2.5-6-1.5-13 0-17 1.5 4 2.5 11 0 17z"

ICONS = {
    "Business-and-Economics/Law-and-Policy": {
        "draw": '<path d="M32 14v38M22 54h20"/><circle cx="32" cy="11" r="2.5"/>'
                '<g class="a"><path d="M13 19h38"/><path d="M15 19 9 33m6-14 6 14M49 19l-6 14m6-14 6 14"/>'
                '<path d="M8 33q7 6 14 0zM42 33q7 6 14 0z"/></g>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}28%{transform:rotate(-9deg)}62%{transform:rotate(6deg)}84%{transform:rotate(-2deg)}",
                   "32px 19px", "2.2s", "ease-in-out"),),
    },
    "Business-and-Economics/Microeconomics": {
        "draw": '<path d="M12 10v42h42"/><path d="M17 15 51 45"/><path class="a" d="M17 45 51 15"/>'
                '<circle class="b" cx="34" cy="30" r="2.6" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%,100%{transform:translateX(0px)}45%,60%{transform:translateX(6px)}", "34px 30px", "2.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:translate(0px,0px)}45%,60%{transform:translate(3px,2.6px)}", "34px 30px", "2.4s", "ease-in-out")),
    },
    "Business-and-Economics/Key-Performance-Indicators": {
        "draw": '<path d="M10 44a22 22 0 0 1 44 0"/><path d="M12.9 33l3.5 2M21 24.9l2 3.5M32 22v4M43 24.9l-2 3.5M51.1 33l-3.5 2"/>'
                '<path d="M10 50h44"/><g class="a"><path d="M32 44V28"/><circle cx="32" cy="44" r="3"/></g>',
        "parts": (("a", "0%,100%{transform:rotate(-62deg)}52%{transform:rotate(44deg)}64%{transform:rotate(33deg)}74%{transform:rotate(39deg)}",
                   "32px 44px", "2.6s", "ease-in-out"),),
    },
    "Business-and-Economics/Emerging-Industries": {
        "draw": '<path d="M10 52h44M16 52v-5h7M48 52v-7h-7M41 45v-4"/><circle cx="23" cy="47" r="1.5"/><circle cx="41" cy="40" r="1.5"/>'
                '<g class="a"><path d="M32 52V30"/><path d="M32 40c-7 0-11-4-11-10 6.5 0 11 3.5 11 10ZM32 35c0-7.5 5-12 12-12 0 7.5-5 12-12 12Z"/></g>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="18" cy="20" r="1.4"/><circle cx="48" cy="14" r="1.2"/><circle cx="26" cy="12" r="1"/></g>',
        "parts": (("a", "0%{transform:scale(.35)}42%{transform:scale(1.07)}56%{transform:scale(.97)}66%,100%{transform:scale(1)}",
                   "32px 52px", "2.4s", "ease-out"),
                  ("b", "0%,100%{opacity:.12}46%{opacity:1}70%{opacity:.5}", "32px 16px", "2.4s", "ease-in-out")),
    },
    "Business-and-Economics/Best-Practices-and-Success-Stories": {
        "draw": '<path d="M22 7h20l-6 16h-8z"/><g class="a"><circle cx="32" cy="38" r="13"/>'
                '<path class="b" d="m32 30 2.4 4.9 5.4.8-3.9 3.8.9 5.4-4.8-2.5-4.8 2.5.9-5.4-3.9-3.8 5.4-.8z"/></g>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}20%{transform:rotate(10deg)}45%{transform:rotate(-7deg)}68%{transform:rotate(4deg)}86%{transform:rotate(-1.5deg)}",
                   "32px 23px", "2.2s", "ease-out"),
                  ("b", "0%,100%{transform:scale(1)}35%{transform:scale(1.25)}55%{transform:scale(.92)}", "32px 38px", "2.2s", "ease-in-out")),
    },
    "Business-and-Economics/Law-and-Policy/Constitutional-Law": {
        "draw": '<g class="b"><path d="M10 22 32 10l22 12z"/><path d="M12 25h40"/></g>'
                '<path class="a" d="M17 28v18M26 28v18M38 28v18M47 28v18"/><path d="M11 50h42M9 54h46"/>',
        "parts": (("a", "0%,100%{transform:scaleY(1)}35%{transform:scaleY(.82)}62%{transform:scaleY(1.04)}", "32px 46px", "1.8s", "ease-in-out"),
                  ("b", "0%,100%{transform:translateY(0px)}35%{transform:translateY(3.2px)}62%{transform:translateY(-.7px)}", "32px 18px", "1.8s", "ease-in-out")),
    },
    "Business-and-Economics/Law-and-Policy/Corporate-Law": {
        "draw": '<path d="M14 8h22l8 8v38H14z"/><path d="M36 8v8h8M19 20h14M19 26h20M19 32h17"/>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="M19 45c2-5 4-5 5 0s3 3 5-2 3 1 4 2 3-1 5-2"/>'
                '<g class="b"><path d="M45 31 56 20l3 3-11 11z"/><path d="M45 31l-1.5 4.5L48 34"/></g>',
        "parts": (("a", "0%,15%{stroke-dashoffset:1}60%,92%{stroke-dashoffset:0}100%{stroke-dashoffset:1}", "28px 44px", "3s", "linear"),
                  ("b", "0%,100%{transform:translate(0px,0px)}15%{transform:translate(-24.5px,10.5px)}60%{transform:translate(-5.5px,8.5px)}80%{transform:translate(0px,0px)}",
                   "50px 28px", "3s", "ease-in-out")),
    },
    "Business-and-Economics/Law-and-Policy/Criminal-Law": {
        "draw": '<g class="a"><rect x="29" y="20.5" width="14" height="7" rx="2" transform="rotate(42 36 24)"/><path d="M16 46 33 27"/></g>'
                '<path d="M36 50h20v5H36z"/><path class="b" d="M38 45l-3-3M46 44v-4M54 45l3-3"/>',
        "parts": (("a", "0%,100%{transform:rotate(-4deg)}36%{transform:rotate(-10deg)}50%{transform:rotate(41deg)}57%{transform:rotate(35deg)}"
                        "64%{transform:rotate(41deg)}80%{transform:rotate(-4deg)}", "16px 46px", "1.8s", "ease-in-out"),
                  ("b", "0%,48%,72%,100%{opacity:0}52%,66%{opacity:1}", "46px 43px", "1.8s", "linear")),
    },
    "Business-and-Economics/Law-and-Policy/International-Law": {
        "draw": '<circle cx="32" cy="28" r="15"/><path d="M17 28h30M32 13v30"/><ellipse class="a" cx="32" cy="28" rx="7" ry="15"/>'
                '<path d="M32 43v6M22 54h20M24 49h16"/>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="32" cy="7" r="1.6"/><circle cx="52" cy="35" r="1.6"/><circle cx="12" cy="35" r="1.6"/></g>',
        "parts": (("a", "0%,100%{transform:scaleX(1)}25%{transform:scaleX(.15)}50%{transform:scaleX(-1)}75%{transform:scaleX(.15)}", "32px 28px", "2.4s", "linear"),
                  ("b", "0%{transform:rotate(0deg)}100%{transform:rotate(-360deg)}", "32px 28px", "6s", "linear")),
    },
    "Business-and-Economics/Law-and-Policy/Public-Policy": {
        "draw": '<path d="M12 54h40M14 50h36"/><path d="M17 50V34M25 50V34M39 50V34M47 50V34"/>'
                '<path d="M14 34h36M18 34a14 12 0 0 1 28 0"/><path d="M32 22V9"/><path class="a" d="M32 9h10l-2.5 3 2.5 3H32"/>',
        "parts": (("a", "0%,100%{transform:skewY(0deg) scaleX(1)}30%{transform:skewY(-9deg) scaleX(.88)}65%{transform:skewY(7deg) scaleX(1.06)}",
                   "32px 12px", "1.4s", "ease-in-out"),),
    },
    "Business-and-Economics/Law-and-Policy/Regulatory-Frameworks": {
        "draw": '<rect x="14" y="12" width="36" height="44" rx="3"/><path class="b" d="M26 9h12v6H26z"/>'
                '<path d="M20 24h6v6h-6zM20 34h6v6h-6zM20 44h6v6h-6zM31 27h13M31 37h13M31 47h9"/>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="M21 27l2 2 4-5M21 37l2 2 4-5M21 47l2 2 4-5"/>',
        "parts": (("a", "0%,10%{stroke-dashoffset:1}45%,100%{stroke-dashoffset:0}", "24px 37px", "2s", "ease-out"),
                  ("b", "0%,100%{transform:translateY(0px)}20%{transform:translateY(-2px)}35%{transform:translateY(.6px)}", "32px 12px", "2s", "ease-out")),
    },
    "Business-and-Economics/Microeconomics/Consumer-Theory": {
        "draw": '<path d="M12 10v42h42"/><path d="M16 18c2 18 10 26 34 28"/><path opacity=".5" d="M22 13c2 14 9 22 30 24"/>'
                '<path class="a" d="M12 22 46 52"/><circle class="b" cx="25" cy="34" r="2.4" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}45%,60%{transform:rotate(-8deg)}", "12px 22px", "2.6s", "ease-in-out"),
                  ("b", "0%,100%{transform:translate(0px,0px)}45%,60%{transform:translate(3px,-1.5px)}", "25px 34px", "2.6s", "ease-in-out")),
    },
    "Business-and-Economics/Microeconomics/Producer-Theory": {
        "draw": '<path d="M8 52V32l10 6v-6l10 6v-6l10 6V18h7v34z"/><path d="M8 52h48"/><path d="M15 44h4M25 44h4"/>'
                '<g class="a"><rect x="45" y="44" width="8" height="8" rx="1"/><path d="M45 48h8"/></g>'
                '<g class="b"><circle cx="41.5" cy="13" r="2.2"/><circle cx="45" cy="8.5" r="1.6"/></g>',
        "parts": (("a", "0%{transform:translateX(-8px);opacity:0}20%{opacity:1}75%{transform:translateX(4px);opacity:1}100%{transform:translateX(5px);opacity:0}",
                   "49px 48px", "2s", "ease-out"),
                  ("b", "0%{transform:translate(0px,3px) scale(.6);opacity:0}30%{opacity:.9}100%{transform:translate(2px,-3px) scale(1.2);opacity:0}",
                   "43px 11px", "2s", "ease-out")),
    },
    "Business-and-Economics/Microeconomics/Market-Structures": {
        "draw": '<path d="M10 48h44M10 45v6M54 45v6"/><circle cx="15" cy="30" r="7"/><circle cx="29" cy="30" r="4.5"/><circle cx="38" cy="30" r="4.5"/>'
                '<g fill="currentColor" stroke="none"><circle cx="47" cy="25" r="1.6"/><circle cx="52" cy="25" r="1.6"/><circle cx="47" cy="30" r="1.6"/>'
                '<circle cx="52" cy="30" r="1.6"/><circle cx="47" cy="35" r="1.6"/><circle cx="52" cy="35" r="1.6"/></g><path class="a" d="M15 41l3 5h-6z"/>',
        "parts": (("a", "0%,8%,100%{transform:translateX(0px)}28%,38%{transform:translateX(18.5px)}58%,72%{transform:translateX(34.5px)}",
                   "15px 43px", "3.2s", "ease-in-out"),),
    },
    "Business-and-Economics/Microeconomics/Game-Theory": {
        "draw": '<rect x="14" y="14" width="36" height="36" rx="2"/><path d="M32 14v36M14 32h36"/><path d="M8 23h3M8 41h3M23 8v3M41 8v3"/>'
                '<rect class="a" x="17" y="17" width="12" height="12" rx="2"/>',
        "parts": (("a", "0%,22%{transform:translate(0px,0px)}25%,47%{transform:translate(18px,0px)}50%,72%{transform:translate(18px,18px)}"
                        "75%,97%{transform:translate(0px,18px)}100%{transform:translate(0px,0px)}", "23px 23px", "3.6s", "ease-in-out"),),
    },
    "Business-and-Economics/Microeconomics/Behavioral-Economics": {
        "draw": '<path d="M26 54h12l-6-9z"/><g class="a"><path d="M10 45h44"/><circle cx="16" cy="38" r="6"/><circle cx="16" cy="38" r="2.5"/>'
                '<path d="M48 43c-6-4-8-7-8-10a4 4 0 0 1 8-1.5A4 4 0 0 1 56 33c0 3-2 6-8 10z"/></g>',
        "parts": (("a", "0%,100%{transform:rotate(8deg)}46%,54%{transform:rotate(-8deg)}", "32px 45px", "2.8s", "ease-in-out"),),
    },
    "Business-and-Economics/Microeconomics/Information-Economics": {
        "draw": '<path d="M12 8h24l8 8v38H12z"/><path d="M36 8v8h8M17 22h14M17 29h20"/><path stroke-dasharray="2 3" d="M17 36h20M17 43h16"/>'
                '<g class="a"><circle cx="40" cy="40" r="7"/><path d="M45 45l7 7"/></g>',
        "parts": (("a", "0%,100%{transform:translate(0px,0px)}25%{transform:translate(-9px,-12px)}50%{transform:translate(-14px,-4px)}75%{transform:translate(-4px,2px)}",
                   "40px 40px", "3.4s", "ease-in-out"),),
    },
    "Business-and-Economics/Macroeconomics/Economic-Growth": {
        "draw": '<path d="M8 54h48"/><g class="b"><circle cx="50" cy="16" r="5"/><path d="M50 8V6M56.5 9.5 58 8M57 16h2"/></g>'
                '<g class="a"><path d="M12 54V40h9v14M24 54V30h9v24M36 54V22h9v32"/><path d="M27 35h3M27 41h3M39 27h3M39 33h3M39 39h3"/></g>',
        "parts": (("a", "0%{transform:scaleY(.45)}48%{transform:scaleY(1.05)}58%,100%{transform:scaleY(1)}", "32px 54px", "2.6s", "ease-out"),
                  ("b", "0%{transform:translateY(12px);opacity:.2}48%,100%{transform:translateY(0px);opacity:1}", "50px 16px", "2.6s", "ease-out")),
    },
    "Business-and-Economics/Macroeconomics/Monetary-Policy": {
        "draw": '<path d="M8 20h18a8 8 0 0 1 8 8v4h-6v-3a3 3 0 0 0-3-3H8z"/><path d="M14 20v-6h6v6M11 14h12"/>'
                '<ellipse cx="31" cy="50" rx="14" ry="4"/><ellipse class="b" cx="31" cy="50" rx="5" ry="1.4"/>'
                '<circle class="a" cx="31" cy="37" r="2.6" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translateY(0px) scale(.4);opacity:0}15%{transform:translateY(0px) scale(1);opacity:1}70%{transform:translateY(12px) scale(1);opacity:1}"
                        "76%,100%{transform:translateY(13px) scale(.6);opacity:0}", "31px 37px", "1.6s", "ease-in"),
                  ("b", "0%,70%{transform:scale(.3);opacity:0}76%{opacity:1}100%{transform:scale(2.2);opacity:0}", "31px 50px", "1.6s", "ease-out")),
    },
    "Business-and-Economics/Macroeconomics/Fiscal-Policy": {
        "draw": '<path d="M30 14a18 18 0 1 0 18 18H30z"/><path d="M30 32 17.3 44.7M30 32v18"/>'
                '<path class="a" d="M33 29V11a18 18 0 0 1 18 18z"/>',
        "parts": (("a", "0%,100%{transform:translate(0px,0px)}40%,60%{transform:translate(3px,-3px)}", "42px 20px", "2s", "ease-in-out"),),
    },
    "Business-and-Economics/Macroeconomics/International-Trade": {
        "draw": '<g class="a"><path d="M8 38h48l-7 11H15z"/><rect x="16" y="28" width="9" height="10"/><rect x="26" y="28" width="9" height="10"/>'
                '<rect x="21" y="19" width="9" height="9"/><path d="M44 38V24h6v14"/></g>'
                '<path class="b" d="M6 55q4-3 8 0t8 0 8 0 8 0 8 0 8 0"/>',
        "parts": (("a", "0%,100%{transform:rotate(-3deg) translateY(0px)}50%{transform:rotate(3deg) translateY(1.5px)}", "32px 44px", "2.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:translateX(2px)}50%{transform:translateX(-6px)}", "30px 55px", "2.4s", "ease-in-out")),
    },
    "Business-and-Economics/Macroeconomics/Business-Cycles": {
        "draw": '<path d="M8 50h48"/><path opacity=".4" d="M6 34h52"/><path d="M8 34c4.5-12 7.5-12 12 0s7.5 12 12 0 7.5-12 12 0 7.5 12 12 0"/>'
                '<circle class="a" cx="8" cy="34" r="3" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translate(0px,0px)}12%{transform:translate(6px,-9px)}25%{transform:translate(12px,0px)}38%{transform:translate(18px,9px)}"
                        "50%{transform:translate(24px,0px)}62%{transform:translate(30px,-9px)}75%{transform:translate(36px,0px)}88%{transform:translate(42px,9px)}"
                        "100%{transform:translate(48px,0px)}", "8px 34px", "4s", "linear"),),
    },
    "Business-and-Economics/Macroeconomics/Development-Economics": {
        "draw": '<path d="M6 40h10v14M58 40H48v14"/><path class="a" pathLength="1" stroke-dasharray="1" d="M16 40h32"/>'
                '<path d="M16 40q16-22 32 0"/><path d="M24 40v-8.25M32 40v-11M40 40v-8.25"/><path class="b" d="M18 50q3-2 6 0t6 0 6 0 6 0"/>',
        "parts": (("a", "0%,6%{stroke-dashoffset:1}52%,100%{stroke-dashoffset:0}", "32px 40px", "2.8s", "ease-out"),
                  ("b", "0%,100%{transform:translateX(0px)}50%{transform:translateX(3.5px)}", "30px 50px", "2.8s", "ease-in-out")),
    },
    "Business-and-Economics/Key-Performance-Indicators/Profitability-Metrics": {
        "draw": '<ellipse cx="24" cy="50" rx="10" ry="3"/><path d="M14 50v-5M34 50v-5"/><ellipse cx="24" cy="45" rx="10" ry="3"/>'
                '<path d="M14 45v-5M34 45v-5"/><ellipse cx="24" cy="40" rx="10" ry="3"/>'
                '<ellipse class="a" cx="24" cy="35" rx="10" ry="3"/><path class="b" d="M46 46V16m-7 7 7-7 7 7"/>',
        "parts": (("a", "0%{transform:translateY(-16px);opacity:0}28%{opacity:1}52%{transform:translateY(0px)}60%{transform:translateY(-2.5px)}68%,100%{transform:translateY(0px)}",
                   "24px 35px", "2.2s", "ease-in"),
                  ("b", "0%,100%{transform:translateY(1px) scaleY(.92)}55%{transform:translateY(-3px) scaleY(1.05)}", "46px 46px", "2.2s", "ease-in-out")),
    },
    "Business-and-Economics/Key-Performance-Indicators/Liquidity-Metrics": {
        "draw": '<path d="M14 18v32a4 4 0 0 0 4 4h28a4 4 0 0 0 4-4V18"/><path d="M50 26h5M50 34h5M50 42h5"/>'
                '<path class="a" d="M14 34q4.5-3 9 0t9 0 9 0 9 0"/>'
                '<path class="b" d="M32 6c3 4 4.5 6.5 4.5 8.5a4.5 4.5 0 0 1-9 0c0-2 1.5-4.5 4.5-8.5z"/>',
        "parts": (("a", "0%,100%{transform:rotate(-4.5deg)}50%{transform:rotate(4.5deg)}", "32px 34px", "2.2s", "ease-in-out"),
                  ("b", "0%{transform:translateY(0px);opacity:1}60%{transform:translateY(16px);opacity:1}70%,100%{transform:translateY(18px);opacity:0}",
                   "32px 14px", "2.2s", "ease-in")),
    },
    "Business-and-Economics/Key-Performance-Indicators/Efficiency-Metrics": {
        "draw": '<circle cx="32" cy="36" r="18"/><path d="M28 10h8M32 10v8M47 21l3-3"/><path d="M32 22v2M46 36h-2M32 50v-2M18 36h2"/>'
                '<path class="a" d="M32 36V25"/><circle cx="32" cy="36" r="2" fill="currentColor" stroke="none"/>'
                '<path class="b" d="M40 38l-4 6h4l-3 5"/>',
        "parts": (("a", "0%{transform:rotate(0deg)}50%{transform:rotate(180deg)}100%{transform:rotate(360deg)}", "32px 36px", "1.4s", "linear"),
                  ("b", "0%,100%{opacity:.35;transform:scale(1)}50%{opacity:1;transform:scale(1.15)}", "38px 43px", "0.7s", "ease-in-out")),
    },
    "Business-and-Economics/Key-Performance-Indicators/Growth-Metrics": {
        "draw": '<path d="M10 54h44"/><path class="a" d="M14 54V42h7v12M26 54V34h7v20M38 54V24h7v30"/>'
                '<path class="b" d="M12 30 26 22l8 4 16-14m-7 0h7v7"/>',
        "parts": (("a", "0%,100%{transform:scaleY(1)}22%{transform:scaleY(.58)}56%{transform:scaleY(1.07)}72%{transform:scaleY(.98)}", "32px 54px", "2.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:translate(0px,0px)}22%{transform:translate(-2px,2px)}56%{transform:translate(2px,-2px)}", "32px 20px", "2.4s", "ease-in-out")),
    },
    "Business-and-Economics/Key-Performance-Indicators/Customer-Metrics": {
        "draw": '<g class="b"><circle cx="32" cy="17" r="7"/><path d="M18 40c1.5-8 7-12 14-12s12.5 4 14 12"/></g>'
                f'<g class="a"><polygon points="{_star(18, 51)}"/><polygon points="{_star(32, 51)}"/><polygon points="{_star(46, 51)}"/></g>',
        "parts": (("a", "0%,100%{transform:scale(1)}30%{transform:scale(1.16)}50%{transform:scale(.94)}68%{transform:scale(1.04)}", "32px 51px", "1.6s", "ease-out"),
                  ("b", "0%,100%{transform:translateY(0px)}30%{transform:translateY(-1.5px)}", "32px 25px", "1.6s", "ease-in-out")),
    },
    "Business-and-Economics/Key-Performance-Indicators/Operational-Metrics": {
        "draw": '<g class="a"><circle cx="24" cy="30" r="8"/><circle cx="24" cy="30" r="2.5"/>'
                '<path d="M32 30h3M29.7 35.7l2.1 2.1M24 38v3M18.3 35.7l-2.1 2.1M16 30h-3M18.3 24.3l-2.1-2.1M24 22v-3M29.7 24.3l2.1-2.1"/></g>'
                '<g class="b"><circle cx="41" cy="40" r="6"/><path d="M47 40h3M44 45.2l1.5 2.6M38 45.2l-1.5 2.6M35 40h-3M38 34.8l-1.5-2.6M44 34.8l1.5-2.6"/></g>'
                '<path d="M10 55h44"/>',
        "parts": (("a", "0%{transform:rotate(0deg)}100%{transform:rotate(45deg)}", "24px 30px", "1.2s", "linear"),
                  ("b", "0%{transform:rotate(0deg)}100%{transform:rotate(-60deg)}", "41px 40px", "1.2s", "linear")),
    },
    "Business-and-Economics/Emerging-Industries/Artificial-Intelligence": {
        "draw": '<rect x="18" y="20" width="26" height="26" rx="3"/>'
                '<path d="M24 20v-5M31 20v-5M38 20v-5M24 46v5M31 46v5M38 46v5M18 27h-5M18 33h-5M18 39h-5M44 27h5M44 33h5M44 39h5"/>'
                '<path class="a" d="M31 25l2.2 5.8L39 33l-5.8 2.2L31 41l-2.2-5.8L23 33l5.8-2.2z"/><path class="b" d="M47 13l9-7m-6 0h6v6"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg) scale(.85)}50%{transform:rotate(90deg) scale(1.12)}", "31px 33px", "2s", "ease-in-out"),
                  ("b", "0%,100%{transform:translate(0px,0px);opacity:.5}50%{transform:translate(2px,-2px);opacity:1}", "51px 9px", "2s", "ease-in-out")),
    },
    "Business-and-Economics/Emerging-Industries/Biotechnology": {
        "draw": '<ellipse cx="30" cy="46" rx="20" ry="7"/><path d="M10 46v3c0 4 9 7 20 7s20-3 20-7v-3"/>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="22" cy="46" r="2"/><circle cx="34" cy="44" r="2.6"/><circle cx="38" cy="48.5" r="1.6"/><circle cx="27" cy="49" r="1.3"/></g>'
                '<g class="a"><path d="M42 8l4 4-10 18-4-4z"/><path d="M40 6l8 8M34 28l-3 5"/></g>'
                '<circle class="c" cx="31" cy="35" r="1.6" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%,100%{transform:translate(0px,0px)}40%,55%{transform:translate(-1.5px,3px)}", "38px 18px", "2.4s", "ease-in-out"),
                  ("b", "0%,70%{transform:scale(1)}82%{transform:scale(1.3)}100%{transform:scale(1)}", "30px 46px", "2.4s", "ease-out"),
                  ("c", "0%,45%{transform:translateY(0px);opacity:0}50%{opacity:1}75%{transform:translateY(9px);opacity:1}82%,100%{transform:translateY(10px);opacity:0}",
                   "31px 35px", "2.4s", "ease-in")),
    },
    "Business-and-Economics/Emerging-Industries/Renewable-Energy": {
        "draw": '<path d="M30.5 30 28 56h8l-2.5-26"/><path d="M22 56h20"/><circle cx="32" cy="27" r="3"/>'
                f'<g class="a"><path d="{_BLADE}"/><path transform="rotate(120 32 27)" d="{_BLADE}"/><path transform="rotate(240 32 27)" d="{_BLADE}"/></g>'
                '<g class="b"><circle cx="13" cy="13" r="3.5"/><path d="M13 6.5V5M6.5 13H5M19.5 13H21M13 19.5V21M8.4 8.4 7.3 7.3M17.6 8.4l1.1-1.1"/></g>',
        "parts": (("a", "0%{transform:rotate(0deg)}100%{transform:rotate(120deg)}", "32px 27px", "0.9s", "linear"),
                  ("b", "0%,100%{transform:scale(1) rotate(0deg)}50%{transform:scale(1.15) rotate(22deg)}", "13px 13px", "2.4s", "ease-in-out")),
    },
    "Business-and-Economics/Emerging-Industries/Space-Industry": {
        "draw": '<g class="a"><path d="M32 8c7 6 9 16 7 30H25c-2-14 0-24 7-30z"/><circle cx="32" cy="22" r="3.5"/>'
                '<path d="M25 32l-6 8v4l7-3M39 32l6 8v4l-7-3"/><path class="b" d="M28 40c0 6 2 9 4 12 2-3 4-6 4-12"/></g>'
                '<path opacity=".5" d="M14 57q4-4 8 0 4-4 8 0 4-4 8 0 4-4 8 0"/>',
        "parts": (("a", "0%,100%{transform:translate(0px,0px)}20%{transform:translate(-.6px,-1px)}40%{transform:translate(.6px,-2.5px)}"
                        "60%{transform:translate(-.6px,-3.5px)}80%{transform:translate(.4px,-1.5px)}", "32px 30px", "1.2s", "ease-in-out"),
                  ("b", "0%,100%{transform:scaleY(1);opacity:.9}25%{transform:scaleY(1.35);opacity:1}50%{transform:scaleY(.8);opacity:.7}75%{transform:scaleY(1.2);opacity:1}",
                   "32px 40px", "0.5s", "linear")),
    },
    "Business-and-Economics/Emerging-Industries/Robotics-and-Automation": {
        "draw": '<path d="M12 54h22M17 54v-4h12v4"/><rect x="42" y="46" width="10" height="8" rx="1"/>'
                '<g class="b"><circle cx="23" cy="47" r="3"/><path d="M24.5 44.4 36 30"/>'
                '<g class="a"><circle cx="38" cy="28" r="2.6"/><path d="M40 26.5 46 19"/><path d="M46 19l4-1M46 19l1 4M50 18l1.5 2M47 23l2 1"/></g></g>',
        "parts": (("a", "0%,100%{transform:rotate(-6deg)}50%{transform:rotate(24deg)}", "38px 28px", "2.6s", "ease-in-out"),
                  ("b", "0%,100%{transform:rotate(3deg)}50%{transform:rotate(-9deg)}", "23px 47px", "2.6s", "ease-in-out")),
    },
    "Business-and-Economics/Emerging-Industries/Quantum-Technologies": {
        "draw": '<circle cx="32" cy="32" r="18"/><ellipse class="b" cx="32" cy="32" rx="18" ry="6"/><path d="M32 12v40" stroke-dasharray="2 3" opacity=".6"/>'
                '<g class="a"><path d="M32 32 42 19"/><circle cx="42" cy="19" r="2.4" fill="currentColor" stroke="none"/></g>',
        "parts": (("a", "0%,100%{transform:scaleX(1)}50%{transform:scaleX(-1)}", "32px 32px", "2.4s", "linear"),
                  ("b", "0%,100%{transform:scaleY(1)}50%{transform:scaleY(.55)}", "32px 32px", "2.4s", "ease-in-out")),
    },
    "Business-and-Economics/Best-Practices-and-Success-Stories/Honda": {
        "draw": '<path d="M8 51h48"/><g fill="currentColor" stroke="none" opacity=".6"><circle cx="14" cy="54" r="1.3"/><circle cx="26" cy="54" r="1.3"/>'
                '<circle cx="38" cy="54" r="1.3"/><circle cx="50" cy="54" r="1.3"/></g>'
                '<g class="a"><path d="M13 44v-5l6-8h16l7 8h5a2 2 0 0 1 2 2v3H13z"/><circle cx="20" cy="46" r="3.2"/><circle cx="42" cy="46" r="3.2"/><path d="M27 31v8M15 39h27"/></g>'
                '<g class="b"><path d="M48 9a7 7 0 1 1-6.5 4.4"/><path d="M40 10l1.5 3.4 3.4-1.4"/></g>',
        "parts": (("a", "0%{transform:translateX(-5px)}45%,55%{transform:translateX(5px)}100%{transform:translateX(-5px)}", "31px 40px", "3s", "ease-in-out"),
                  ("b", "0%{transform:rotate(0deg)}40%{transform:rotate(200deg)}100%{transform:rotate(360deg)}", "48px 16px", "3s", "ease-in-out")),
    },
    "Business-and-Economics/Best-Practices-and-Success-Stories/Costco": {
        "draw": '<path d="M10 54h44M12 54v-3h40v3"/><rect x="13" y="37" width="18" height="14" rx="1"/><rect x="33" y="37" width="18" height="14" rx="1"/>'
                '<path d="M22 37v5M42 37v5"/><g class="a"><rect x="23" y="21" width="18" height="16" rx="1"/><path d="M32 21v6"/></g>'
                '<path opacity=".55" d="M8 15 32 6l24 9"/>',
        "parts": (("a", "0%{transform:translate(12px,-10px) rotate(24deg);opacity:0}40%{transform:translate(0px,0px) rotate(0deg);opacity:1}"
                        "50%{transform:translate(0px,-1.5px) rotate(-3deg)}60%,100%{transform:translate(0px,0px) rotate(0deg)}", "32px 37px", "2.4s", "ease-out"),),
    },
    "Business-and-Economics/Best-Practices-and-Success-Stories/Berkshire-Hathaway": {
        "draw": '<path d="M6 17.75 58 50.25"/><path d="M6 56h52" opacity=".4"/>'
                '<g class="a"><circle cx="14" cy="16" r="6"/><path d="M10 14q4 3 8 0"/></g>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="40" cy="10" r="1.2"/><circle cx="52" cy="22" r="1"/><circle cx="30" cy="8" r="0.9"/></g>',
        "parts": (("a", "0%{transform:translate(0px,3px) rotate(0deg) scale(.6);opacity:1}82%{transform:translate(30px,18.75px) rotate(320deg) scale(1.15);opacity:1}"
                        "100%{transform:translate(30px,18.75px) rotate(320deg) scale(1.15);opacity:0}", "14px 16px", "3s", "ease-in"),
                  ("b", "0%,100%{opacity:.25}40%{opacity:1}75%{opacity:.55}", "40px 14px", "3s", "ease-in-out")),
    },
    "Business-and-Economics/Best-Practices-and-Success-Stories/Microsoft": {
        "draw": '<rect x="12" y="30" width="40" height="24" rx="2.5"/><path d="M12 36h40"/>'
                '<g fill="currentColor" stroke="none"><circle cx="16" cy="33" r="1"/><circle cx="20" cy="33" r="1"/></g>'
                '<path class="a" d="M22 22a6 6 0 0 1 1.5-11.8A8 8 0 0 1 39 9.5 6.5 6.5 0 1 1 42 22z"/><path class="b" d="M32 50v-8m-4 4 4-4 4 4"/>',
        "parts": (("a", "0%,100%{transform:translate(0px,0px)}50%{transform:translate(4px,-1.5px)}75%{transform:translate(1px,-.5px)}", "32px 16px", "3s", "ease-in-out"),
                  ("b", "0%{transform:translateY(3px);opacity:0}35%{opacity:1}100%{transform:translateY(-5px);opacity:0}", "32px 46px", "1.6s", "ease-out")),
    },
    "Business-and-Economics/Best-Practices-and-Success-Stories/NVIDIA": {
        "draw": '<rect x="8" y="22" width="48" height="24" rx="3"/><path d="M12 46v6h14v-6"/><path d="M42 26v16M46 26v16M50 26v16"/>'
                '<g class="a"><circle cx="24" cy="34" r="8.5"/><path d="M24 34c0-4 2-6 5-6M24 34c4 0 6 2 6 5M24 34c0 4-2 6-5 6M24 34c-4 0-6-2-6-5"/></g>'
                '<path class="b" d="M42 18c-1.5-2 1.5-4 0-6M47 18c-1.5-2 1.5-4 0-6M52 18c-1.5-2 1.5-4 0-6"/>',
        "parts": (("a", "0%{transform:rotate(0deg)}100%{transform:rotate(90deg)}", "24px 34px", "0.45s", "linear"),
                  ("b", "0%{transform:translateY(2px);opacity:0}40%{opacity:1}100%{transform:translateY(-4px);opacity:0}", "47px 15px", "1.4s", "ease-out")),
    },
    "Business-and-Economics/Best-Practices-and-Success-Stories/Amazon": {
        "draw": '<path d="M6 47h52"/><g fill="currentColor" stroke="none" opacity=".55"><circle cx="12" cy="51" r="2"/><circle cx="24" cy="51" r="2"/>'
                '<circle cx="36" cy="51" r="2"/><circle cx="48" cy="51" r="2"/></g>'
                '<g class="a"><rect x="22" y="28" width="20" height="18" rx="1.5"/><path d="M32 28v7M22 35h20M26 40h6"/></g>'
                '<path class="b" d="M10 34h6M8 39h8"/>',
        "parts": (("a", "0%{transform:translateX(-16px);opacity:0}20%{opacity:1}78%{opacity:1}100%{transform:translateX(14px);opacity:0}", "32px 37px", "2.6s", "linear"),
                  ("b", "0%,100%{opacity:0;transform:translateX(0px)}35%{opacity:.9;transform:translateX(-2px)}70%{opacity:.4;transform:translateX(-4px)}",
                   "12px 36px", "2.6s", "linear")),
    },
}
