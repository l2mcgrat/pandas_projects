"""Science & Engineering icons: one animated metaphor per discipline, drawn on the shared 64-unit grid."""

ICONS = {
    "Science-and-Engineering": {
        "draw": '<g class="a"><polygon points="53,17 55.9,17.5 55.9,20.5 53,21 52,23.2 53.8,25.6 51.6,27.8 49.2,26 47,27 46.5,29.9 '
                '43.5,29.9 43,27 40.8,26 38.4,27.8 36.2,25.6 38,23.2 37,21 34.1,20.5 34.1,17.5 37,17 38,14.8 36.2,12.4 38.4,10.2 '
                '40.8,12 43,11 43.5,8.1 46.5,8.1 47,11 49.2,12 51.6,10.2 53.8,12.4 52,14.8"/><circle cx="45" cy="19" r="3.5"/></g>'
                '<path d="M15 24h12M17 24v9L8 51a3 3 0 0 0 2.7 4.3h20.6A3 3 0 0 0 34 51L25 33v-9"/>'
                '<path d="M12.5 44c3 1.4 5.5 1.4 8.5 0s5.5-1.4 8.5 0"/>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="20" cy="50" r="1.8"/><circle cx="23" cy="46.5" r="1.3"/></g>',
        "parts": (("a", "0%{transform:rotate(0deg)}62%{transform:rotate(49deg)}78%{transform:rotate(43deg)}90%,100%{transform:rotate(45deg)}",
                   "45px 19px", "2.4s", "ease-in-out"),
                  ("b", "0%{transform:translateY(0);opacity:0}14%{opacity:1}68%{opacity:.85}100%{transform:translateY(-17px);opacity:0}",
                   "21px 48px", "1.6s", "ease-in")),
    },
    "Science-and-Engineering/Mathematics": {
        "draw": '<path opacity=".3" stroke-width="1.2" d="M32 10v44M10 32h44"/><path class="a" d="M20 11v18M11 20h18"/>'
                '<path d="M35 20h18M35 44h18"/><path class="b" d="m13.6 37.6 12.8 12.8m0-12.8L13.6 50.4"/>'
                '<g class="c" fill="currentColor" stroke="none"><circle cx="44" cy="36.5" r="2.2"/><circle cx="44" cy="51.5" r="2.2"/></g>',
        "parts": (("a", "0%,24%{transform:rotate(0deg)}48%,100%{transform:rotate(90deg)}", "20px 20px", "2.6s", "cubic-bezier(.5,-.4,.5,1.4)"),
                  ("b", "0%,52%{transform:rotate(0deg)}76%,100%{transform:rotate(-90deg)}", "20px 44px", "2.6s", "cubic-bezier(.5,-.4,.5,1.4)"),
                  ("c", "0%,100%{transform:scaleY(1)}30%{transform:scaleY(1.22)}60%{transform:scaleY(.84)}", "44px 44px", "2.6s", "ease-in-out")),
    },
    "Science-and-Engineering/Mathematics/Calculus-and-Vectors": {
        "draw": '<path d="M9 9v45h46"/><path d="M12 41.8Q34-1.8 56 41.8"/>'
                '<g class="a"><circle cx="22" cy="26.5" r="2.4" fill="currentColor" stroke="none"/>'
                '<path transform="translate(22 26.5) rotate(-47.2)" d="M0 0h13m-4.5-4 4.5 4-4.5 4"/></g>',
        "parts": (("a", "0%{transform:translate(-6px,8.1px) rotate(-11.1deg);opacity:0}10%{opacity:1}"
                        "14%{transform:translate(0px,0px) rotate(0deg)}28%{transform:translate(6px,-4.9px) rotate(18.8deg)}"
                        "44%{transform:translate(12px,-6.5px) rotate(47.2deg)}60%{transform:translate(18px,-4.9px) rotate(75.6deg)}"
                        "76%{transform:translate(24px,0px) rotate(94.4deg)}86%{opacity:1}88%{transform:translate(27px,3.6px) rotate(100.7deg)}"
                        "100%{transform:translate(27px,3.6px) rotate(100.7deg);opacity:0}", "22px 26.5px", "3.4s", "linear"),),
    },
    "Science-and-Engineering/Mathematics/Probability-and-Statistics": {
        "draw": '<path d="M8 55h50"/><path opacity=".45" stroke-dasharray="2 3" d="M34 21v34"/>'
                '<path class="b" pathLength="1" stroke-dasharray="1" d="M10 52C21 52 25 18 34 18s13 34 24 34"/>'
                '<g class="a"><rect x="10" y="12" width="12" height="12" rx="2.5"/><g fill="currentColor" stroke="none">'
                '<circle cx="13.2" cy="15.2" r="1.1"/><circle cx="18.8" cy="15.2" r="1.1"/><circle cx="16" cy="18" r="1.1"/>'
                '<circle cx="13.2" cy="20.8" r="1.1"/><circle cx="18.8" cy="20.8" r="1.1"/></g></g>',
        "parts": (("a", "0%{transform:translateY(0) rotate(0deg)}30%{transform:translateY(-3.5px) rotate(55deg)}"
                        "52%{transform:translateY(0) rotate(90deg)}62%{transform:translateY(-1.2px) rotate(90deg)}"
                        "72%,100%{transform:translateY(0) rotate(90deg)}", "16px 18px", "2.6s", "ease-out"),
                  ("b", "0%,6%{stroke-dashoffset:1}58%,100%{stroke-dashoffset:0}", "34px 36px", "2.6s", "ease-in-out")),
    },
    "Science-and-Engineering/Mathematics/Linear-Algebra": {
        "draw": '<g class="a"><path stroke-width="1.3" opacity=".5" d="M14 14h36v36H14ZM26 14v36M38 14v36M14 26h36M14 38h36"/>'
                '<path class="b" stroke-width="2.6" d="M26 38h12m-4-3.5 4 3.5-4 3.5M26 38V26m-3.5 4 3.5-4 3.5 4"/>'
                '<circle cx="26" cy="38" r="2" fill="currentColor" stroke="none"/></g>',
        "parts": (("a", "0%,100%{transform:skewX(0deg) scaleY(1)}28%,42%{transform:skewX(-24deg) scaleY(1)}70%,82%{transform:skewX(16deg) scaleY(.86)}",
                   "32px 32px", "3.6s", "ease-in-out"),
                  ("b", "0%,20%,100%{transform:scale(1)}56%{transform:scale(1.2)}", "26px 38px", "3.6s", "ease-in-out")),
    },
    "Science-and-Engineering/Mathematics/Number-Theory": {
        "draw": '<circle cx="32" cy="32" r="21" opacity=".3" stroke-width="1.2"/>'
                '<polygon class="a" pathLength="1" stroke-dasharray="1" stroke-width="1.8" '
                'points="32,11 52.5,36.7 22.9,50.9 15.6,18.9 48.4,18.9 41.1,50.9 11.5,36.7"/>'
                '<g fill="currentColor" stroke="none"><circle cx="32" cy="11" r="2.6"/><circle cx="48.4" cy="18.9" r="2.6"/>'
                '<circle cx="52.5" cy="36.7" r="2.6"/><circle cx="41.1" cy="50.9" r="2.6"/><circle cx="22.9" cy="50.9" r="2.6"/>'
                '<circle cx="11.5" cy="36.7" r="2.6"/><circle cx="15.6" cy="18.9" r="2.6"/></g>'
                '<circle class="b" cx="32" cy="11" r="5" stroke-width="1.6"/>',
        "parts": (("a", "0%,12%{stroke-dashoffset:1}16%,26%{stroke-dashoffset:0.857}30%,40%{stroke-dashoffset:0.714}"
                        "44%,54%{stroke-dashoffset:0.571}58%,68%{stroke-dashoffset:0.429}72%,82%{stroke-dashoffset:0.286}"
                        "86%,96%{stroke-dashoffset:0.143}100%{stroke-dashoffset:0}", "32px 32px", "4.2s", "ease-in-out"),
                  ("b", "0%,12%{transform:rotate(0deg)}16%,26%{transform:rotate(102.86deg)}30%,40%{transform:rotate(205.71deg)}"
                        "44%,54%{transform:rotate(308.57deg)}58%,68%{transform:rotate(411.43deg)}72%,82%{transform:rotate(514.29deg)}"
                        "86%,96%{transform:rotate(617.14deg)}100%{transform:rotate(720deg)}", "32px 32px", "4.2s", "ease-in-out")),
    },
    "Science-and-Engineering/Mathematics/Set-Theory": {
        "draw": '<g class="a"><circle cx="25.5" cy="32" r="12.5"/><circle cx="19" cy="32" r="1.8" fill="currentColor" stroke="none"/></g>'
                '<g class="b"><circle cx="38.5" cy="32" r="12.5"/><circle cx="45" cy="32" r="1.8" fill="currentColor" stroke="none"/></g>'
                '<g class="c" fill="currentColor" stroke="none"><path fill-opacity=".3" d="M32 21.3A12.5 12.5 0 0 1 32 42.7A12.5 12.5 0 0 1 32 21.3Z"/>'
                '<circle cx="32" cy="32" r="1.8"/></g>',
        "parts": (("a", "0%,100%{transform:translateX(0)}34%,62%{transform:translateX(-6.5px)}", "25.5px 32px", "3.2s", "ease-in-out"),
                  ("b", "0%,100%{transform:translateX(0)}34%,62%{transform:translateX(6.5px)}", "38.5px 32px", "3.2s", "ease-in-out"),
                  ("c", "0%,100%{opacity:1}20%,74%{opacity:0}", "32px 32px", "3.2s", "ease-in-out")),
    },
    "Science-and-Engineering/Mathematics/Abstract-Algebra": {
        "draw": '<g class="a"><polygon points="32,14 46.7,39.5 17.3,39.5"/><circle cx="32" cy="14" r="3.4" fill="currentColor"/></g>'
                '<circle cx="32" cy="31" r="1.4" fill="currentColor" stroke="none"/>'
                '<path class="b" d="M50.8 44.2A23 23 0 0 1 13.2 44.2M18.6 45.9 13.2 44.2l-.3 5.7"/>',
        "parts": (("a", "0%,14%{transform:rotate(0deg)}30%,47%{transform:rotate(120deg)}63%,80%{transform:rotate(240deg)}96%,100%{transform:rotate(360deg)}",
                   "32px 31px", "4.5s", "cubic-bezier(.65,0,.35,1)"),
                  ("b", "0%,14%,47%,80%,100%{opacity:.45}22%,55%,88%{opacity:1}", "32px 44px", "4.5s", "ease-in-out")),
    },
    "Science-and-Engineering/Physics/Classical-Mechanics": {
        "draw": '<path stroke-width="2.4" d="M10 13h44"/><path d="M27.75 13v23.4M36.25 13v23.4"/>'
                '<circle cx="27.75" cy="40" r="3.6" fill="currentColor" fill-opacity=".25"/>'
                '<circle cx="36.25" cy="40" r="3.6" fill="currentColor" fill-opacity=".25"/>'
                '<g class="a"><path d="M19.25 13v23.4"/><circle cx="19.25" cy="40" r="3.6" fill="currentColor" fill-opacity=".25"/></g>'
                '<g class="b"><path d="M44.75 13v23.4"/><circle cx="44.75" cy="40" r="3.6" fill="currentColor" fill-opacity=".25"/></g>',
        "parts": (("a", "0%,100%{transform:rotate(19deg)}26%,74%{transform:rotate(0deg)}", "19.25px 13px", "1.8s", "cubic-bezier(.45,0,.55,1)"),
                  ("b", "0%,26%,74%,100%{transform:rotate(0deg)}50%{transform:rotate(-19deg)}", "44.75px 13px", "1.8s", "cubic-bezier(.45,0,.55,1)")),
    },
    "Science-and-Engineering/Physics/Quantum-Mechanics": {
        "draw": '<path stroke-width="2.2" d="M10 8v46h44V8"/>'
                '<path opacity=".45" stroke-width="1.2" stroke-dasharray="2 3" d="M10 22h44M10 42h44"/>'
                '<path class="a" d="M10 42C28.7 30 35.3 30 54 42"/>'
                '<path class="b" d="M10 22C19.3 12.7 22.7 12.7 32 22S44.7 31.3 54 22"/>',
        "parts": (("a", "0%,100%{transform:scaleY(1)}50%{transform:scaleY(-.96)}", "32px 42px", "2.8s", "ease-in-out"),
                  ("b", "0%,100%{transform:scaleY(1)}50%{transform:scaleY(-.94)}", "32px 22px", "1.4s", "ease-in-out")),
    },
    "Science-and-Engineering/Physics/General-and-Special-Relativity": {
        "draw": '<g class="b"><ellipse cx="32" cy="24" rx="24" ry="8"/><ellipse cx="32" cy="31" rx="13" ry="4.4" opacity=".6"/>'
                '<ellipse cx="32" cy="37" rx="5.5" ry="1.8" opacity=".45"/><path d="M8 24c9 3 16 8 20 18M56 24c-9 3-16 8-20 18"/></g>'
                '<circle cx="32" cy="48" r="6" fill="currentColor" fill-opacity=".25"/>'
                '<g fill="currentColor" stroke="none" opacity=".6"><circle cx="11" cy="9" r="1.2"/><circle cx="50" cy="8" r="1"/>'
                '<circle cx="21" cy="12" r="0.8"/></g>'
                '<circle class="a" cx="56" cy="24" r="2.8" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%,100%{transform:translate(0px,0px) scale(1)}8%{transform:translate(-3.2px,-4px) scale(.92)}"
                        "17%{transform:translate(-12px,-6.9px) scale(.8)}25%{transform:translate(-24px,-8px) scale(.72)}"
                        "33%{transform:translate(-36px,-6.9px) scale(.8)}42%{transform:translate(-44.8px,-4px) scale(.92)}"
                        "50%{transform:translate(-48px,0px) scale(1)}58%{transform:translate(-44.8px,4px) scale(1.1)}"
                        "67%{transform:translate(-36px,6.9px) scale(1.2)}75%{transform:translate(-24px,8px) scale(1.25)}"
                        "83%{transform:translate(-12px,6.9px) scale(1.2)}92%{transform:translate(-3.2px,4px) scale(1.1)}",
                   "56px 24px", "4s", "linear"),
                  ("b", "0%,100%{transform:scaleY(1)}40%{transform:scaleY(1.06)}70%{transform:scaleY(.97)}", "32px 24px", "4s", "ease-in-out")),
    },
    "Science-and-Engineering/Physics/Electromagnetism": {
        "draw": '<g class="b"><path d="M12 46V28a20 20 0 0 1 40 0v18H42V28a10 10 0 0 0-20 0v18Z"/><path d="M12 38h10M42 38h10"/></g>'
                '<g class="a" stroke-dasharray="2.2 2.6"><path d="M17 49c1 8.5 29 8.5 30 0"/><path d="M21.5 49c1 4 20 4 21 0"/></g>'
                '<path class="c" d="M34 30l-5 8h6l-5 8"/>',
        "parts": (("a", "0%{stroke-dashoffset:0}100%{stroke-dashoffset:-9.6}", "32px 52px", "1.2s", "linear"),
                  ("b", "0%,100%{transform:translateY(0)}45%{transform:translateY(-1.6px)}", "32px 30px", "2.4s", "ease-in-out"),
                  ("c", "0%,100%{opacity:1}12%{opacity:.25}20%{opacity:1}58%{opacity:.5}64%{opacity:1}", "32px 38px", "2.4s", "linear")),
    },
    "Science-and-Engineering/Physics/Optics": {
        "draw": '<path fill="currentColor" fill-opacity=".12" d="M28 10q8 22 0 44q-8-22 0-44Z"/>'
                '<g class="a"><path pathLength="1" stroke-dasharray="1" d="M6 18h22l28 21.8"/>'
                '<path pathLength="1" stroke-dasharray="1" d="M6 32h50"/>'
                '<path pathLength="1" stroke-dasharray="1" d="M6 46h22l28-21.8"/></g>'
                '<g class="b"><circle cx="46" cy="32" r="2.2" fill="currentColor" stroke="none"/>'
                '<circle cx="46" cy="32" r="5.5" stroke-width="1.2" opacity=".6"/></g>',
        "parts": (("a", "0%,4%{stroke-dashoffset:1}52%,100%{stroke-dashoffset:0}", "28px 32px", "2.6s", "cubic-bezier(.3,.1,.6,1)"),
                  ("b", "0%,40%{transform:scale(.3);opacity:0}54%{transform:scale(1.3);opacity:1}68%,100%{transform:scale(1);opacity:1}",
                   "46px 32px", "2.6s", "ease-out")),
    },
    "Science-and-Engineering/Physics/Thermodynamics": {
        "draw": '<path stroke-width="2.2" d="M10 16h4v38h36V16h4"/>'
                '<g class="a"><rect x="16" y="22" width="32" height="6" rx="1.5"/><path d="M32 22V11M27 11h10"/></g>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="22" cy="40" r="1.8"/><circle cx="40" cy="46" r="1.8"/>'
                '<circle cx="30" cy="50" r="1.8"/></g>'
                '<g class="c" fill="currentColor" stroke="none"><circle cx="34" cy="37" r="1.8"/><circle cx="43" cy="38" r="1.8"/>'
                '<circle cx="21" cy="49" r="1.8"/></g>',
        "parts": (("a", "0%,100%{transform:translateY(0)}30%{transform:translateY(-3.6px)}70%{transform:translateY(4.2px)}", "32px 25px", "2.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:translate(0px,0px)}20%{transform:translate(1.6px,-1.2px)}40%{transform:translate(-1.2px,1.4px)}"
                        "60%{transform:translate(1.4px,1.6px)}80%{transform:translate(-1.5px,-1px)}", "31px 45px", "0.8s", "linear"),
                  ("c", "0%,100%{transform:translate(0px,0px)}25%{transform:translate(-1.4px,1.3px)}50%{transform:translate(1.3px,-1.5px)}"
                        "75%{transform:translate(1.1px,1.2px)}", "33px 41px", "0.7s", "linear")),
    },
    "Science-and-Engineering/Chemistry": {
        "draw": '<path d="M29 28h2v23a4 4 0 0 0 4 4h14a4 4 0 0 0 4-4V28h2"/>'
                '<path opacity=".5" stroke-width="1.2" d="M47 35h3M47 40h3"/>'
                '<path class="c" d="M31 44q1.8-2 3.7 0t3.7 0 3.7 0 3.6 0 3.7 0 3.6 0"/>'
                '<g class="a"><path transform="translate(36 22) rotate(121)" d="M-5.5 0h11M-4 0v13a4 4 0 0 0 8 0V0"/></g>'
                '<path class="b" fill="currentColor" stroke="none" d="M34 28c1.4 2 2 3 2 4a2 2 0 0 1-4 0c0-1 .6-2 2-4Z"/>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}24%,64%{transform:rotate(10deg)}84%{transform:rotate(-2deg)}", "35px 22px", "2.8s", "ease-in-out"),
                  ("b", "0%,30%{transform:translateY(0) scale(.3);opacity:0}38%{transform:translateY(0) scale(1);opacity:1}"
                        "60%{transform:translateY(9px) scale(1);opacity:1}64%,100%{transform:translateY(10px) scale(.5);opacity:0}",
                   "34px 31px", "2.8s", "ease-in"),
                  ("c", "0%,58%{transform:scaleY(.5)}66%{transform:scaleY(2.2)}78%{transform:scaleY(.8)}88%{transform:scaleY(1.4)}100%{transform:scaleY(.5)}",
                   "42px 44px", "2.8s", "ease-out")),
    },
    "Science-and-Engineering/Chemistry/Organic-Chemistry": {
        "draw": '<polygon points="25,22 38,29.5 38,44.5 25,52 12,44.5 12,29.5"/>'
                '<path class="a" d="M26.3 27L33 30.8M33 43.2L26.3 47M15.6 40.9L15.6 33.1"/>'
                '<g class="b"><path d="M38 29.5l8.7-5 8.6 5M45.4 24.2V14.5M48 24.2V14.5"/><circle cx="46.7" cy="11" r="2.6"/></g>',
        "parts": (("a", "0%,35%{transform:rotate(0deg)}50%,85%{transform:rotate(60deg)}100%{transform:rotate(120deg)}", "25px 37px", "3.6s", "ease-in-out"),
                  ("b", "0%,100%{transform:rotate(0deg)}30%{transform:rotate(-8deg)}65%{transform:rotate(5deg)}", "38px 29.5px", "1.8s", "ease-in-out")),
    },
    "Science-and-Engineering/Chemistry/Inorganic-Chemistry": {
        "draw": '<g class="a"><path opacity=".3" stroke-width="1" d="M32 12 52 32 32 52 12 32Z"/>'
                '<path d="M32 26.5V15M32 37.5V49M26.5 32H15M37.5 32H49"/><path stroke-width="3" d="M28 36l-6.5 6"/>'
                '<path stroke-dasharray="2 2.4" d="M36 28l6-5.4"/><circle cx="32" cy="12" r="3"/><circle cx="32" cy="52" r="3"/>'
                '<circle cx="12" cy="32" r="3"/><circle cx="52" cy="32" r="3"/><circle cx="18.6" cy="45" r="3.6"/>'
                '<circle cx="44.6" cy="20.4" r="2.4"/></g>'
                '<circle class="b" cx="32" cy="32" r="5.5" fill="currentColor" fill-opacity=".25"/>',
        "parts": (("a", "0%,100%{transform:scale(1) rotate(0deg)}35%{transform:scale(1.08) rotate(6deg)}70%{transform:scale(.95) rotate(-4deg)}",
                   "32px 32px", "2.2s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(1)}35%{transform:scale(.86)}70%{transform:scale(1.1)}", "32px 32px", "2.2s", "ease-in-out")),
    },
    "Science-and-Engineering/Chemistry/Electrochemistry": {
        "draw": '<path d="M10 28v22a4 4 0 0 0 4 4h36a4 4 0 0 0 4-4V28"/><path opacity=".45" d="M12 34h40"/>'
                '<rect x="19" y="20" width="6" height="26" rx="1"/><rect x="39" y="20" width="6" height="26" rx="1"/>'
                '<path d="M29 6.5v9M35 8.5v5"/><path stroke-width="1.6" d="M13.5 16h5M16 13.5v5M45.5 16h5"/>'
                '<path class="a" stroke-dasharray="3 2.2" d="M22 20V11h7M35 11h7v9"/>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="48" cy="46" r="1.5"/><circle cx="49.5" cy="41" r="1.1"/>'
                '<circle cx="47.5" cy="37.5" r="0.9"/></g>',
        "parts": (("a", "0%{stroke-dashoffset:0}100%{stroke-dashoffset:-10.4}", "32px 13px", "1.3s", "linear"),
                  ("b", "0%{transform:translateY(3px);opacity:0}25%{opacity:1}80%{opacity:.7}100%{transform:translateY(-6px);opacity:0}",
                   "48px 42px", "1.5s", "ease-in")),
    },
    "Science-and-Engineering/Chemistry/Physical-Chemistry": {
        "draw": '<path d="M7 8v47h50"/><path d="M10 34h6c6 0 8-20 14-20s8 32 16 32h10"/>'
                '<path opacity=".45" stroke-width="1.2" stroke-dasharray="2 2.5" d="M16 34h14M30 34V18"/>'
                '<path class="b" stroke-width="1.5" d="M50 34c-1.5-1.5 1.5-3 0-4.5s1.5-3 0-4.5M55 34c-1.5-1.5 1.5-3 0-4.5s1.5-3 0-4.5"/>'
                '<circle class="a" cx="12" cy="29" r="3" fill="currentColor"/>',
        "parts": (("a", "0%{transform:translate(0px,0px);opacity:0}5%{opacity:1}12%{transform:translate(4px,0px)}"
                        "22%{transform:translate(4.4px,-2.3px)}32%{transform:translate(6.4px,-6.9px)}41%{transform:translate(8.5px,-12px)}"
                        "49%{transform:translate(11.5px,-16.8px)}58%{transform:translate(18px,-20px)}63%{transform:translate(25.1px,-15.1px)}"
                        "66%{transform:translate(27.8px,-8.2px)}69%{transform:translate(30.1px,-0.4px)}72%{transform:translate(32.3px,7px)}"
                        "75%{transform:translate(34px,12px)}84%{transform:translate(40px,12px)}90%{opacity:1}"
                        "100%{transform:translate(40px,12px);opacity:0}", "12px 29px", "3.4s", "linear"),
                  ("b", "0%,74%{transform:translateY(2px);opacity:0}84%{opacity:1}100%{transform:translateY(-4px);opacity:0}",
                   "52px 30px", "3.4s", "ease-out")),
    },
    "Science-and-Engineering/Chemistry/Analytical-Chemistry": {
        "draw": '<path d="M8 8v46h48"/>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="M8 54h6c2 0 2-26 4-26s2 26 4 26h4c2 0 2-14 4-14s2 14 4 14h6c2 0 2-36 4-36s2 36 4 36h8"/>'
                '<path class="b" opacity=".6" stroke-width="1.2" d="M37 10v42"/>',
        "parts": (("a", "0%{stroke-dashoffset:1}78%,100%{stroke-dashoffset:0}", "32px 36px", "3.6s", "linear"),
                  ("b", "0%{transform:translateX(-29px);opacity:0}3%{transform:translateX(-23px);opacity:.8}14%{transform:translateX(-19px)}"
                        "26%{transform:translateX(-15px)}27%{transform:translateX(-11px)}34%{transform:translateX(-7px)}40%{transform:translateX(-3px)}"
                        "43%{transform:translateX(3px)}59%{transform:translateX(7px)}75%{transform:translateX(11px)}"
                        "78%{transform:translateX(19px);opacity:.8}90%,100%{transform:translateX(19px);opacity:0}", "37px 31px", "3.6s", "linear")),
    },
    "Science-and-Engineering/Chemistry/Materials-Chemistry": {
        "draw": '<g class="a"><path d="M14 16l18-6 18 6-18 6ZM14 16v2.5l18 6 18-6V16"/><g fill="currentColor" stroke="none">'
                '<circle cx="23" cy="16" r="1.4"/><circle cx="32" cy="16" r="1.4"/><circle cx="41" cy="16" r="1.4"/></g></g>'
                '<g class="b"><path d="M14 31l18-6 18 6-18 6ZM14 31v2.5l18 6 18-6V31"/><g fill="currentColor" stroke="none">'
                '<circle cx="23" cy="31" r="1.4"/><circle cx="32" cy="31" r="1.4"/><circle cx="41" cy="31" r="1.4"/></g></g>'
                '<path d="M14 46l18-6 18 6-18 6ZM14 46v2.5l18 6 18-6V46"/><g fill="currentColor" stroke="none">'
                '<circle cx="23" cy="46" r="1.4"/><circle cx="32" cy="46" r="1.4"/><circle cx="41" cy="46" r="1.4"/></g>',
        "parts": (("a", "0%,100%{transform:translateX(0)}30%,48%{transform:translateX(6px)}78%{transform:translateX(-4px)}", "32px 17px", "3s", "ease-in-out"),
                  ("b", "0%,100%{transform:translateX(0)}30%,48%{transform:translateX(2.8px)}78%{transform:translateX(-1.8px)}", "32px 32px", "3s", "ease-in-out")),
    },
    "Science-and-Engineering/Biology": {
        "draw": '<rect x="14" y="51" width="34" height="4" rx="2"/><path d="M30 18h2a10 10 0 0 1 10 10v23M14 40h28"/>'
                '<path stroke-width="1.5" d="M19 38h14"/>'
                '<g class="a"><rect x="21" y="7" width="10" height="5" rx="1.5"/><rect x="22.5" y="12" width="7" height="17" rx="1"/>'
                '<path d="M24 29v5h4v-5"/></g>'
                '<g class="b"><circle cx="46.5" cy="34" r="3.5"/><path d="M46.5 34l2-2"/></g>'
                '<g class="c"><circle cx="26" cy="46" r="2" fill="currentColor" stroke="none"/><path stroke-width="1.5" d="M20.5 46h-2M31.5 46h2"/></g>',
        "parts": (("a", "0%,100%{transform:translateY(0)}35%{transform:translateY(1.8px)}55%{transform:translateY(0.8px)}75%{transform:translateY(1.4px)}",
                   "26px 20px", "2.6s", "ease-in-out"),
                  ("b", "0%,100%{transform:rotate(0deg)}35%{transform:rotate(80deg)}55%{transform:rotate(36deg)}75%{transform:rotate(62deg)}",
                   "46.5px 34px", "2.6s", "ease-in-out"),
                  ("c", "0%,100%{transform:scale(.9);opacity:.45}50%{transform:scale(1.2);opacity:1}", "26px 46px", "2.6s", "ease-in-out")),
    },
    "Science-and-Engineering/Biology/Quantum-Biology": {
        "draw": '<g class="c"><path fill="currentColor" fill-opacity=".12" d="M54 20C34 20 22 32 24 54c22 2 32-12 30-34Z"/>'
                '<path d="M20 58l4-4 28-32"/><g class="b" stroke-width="1.4">'
                '<path pathLength="1" stroke-dasharray="1" d="M32.4 44.4 30.4 34.4"/><path pathLength="1" stroke-dasharray="1" d="M32.4 44.4 42.4 42.4"/>'
                '<path pathLength="1" stroke-dasharray="1" d="M38 38 36.4 30"/><path pathLength="1" stroke-dasharray="1" d="M38 38 46.5 36.3"/>'
                '<path pathLength="1" stroke-dasharray="1" d="M43.6 31.6 42.4 25.6"/><path pathLength="1" stroke-dasharray="1" d="M43.6 31.6 49.6 30.4"/>'
                '</g></g>'
                '<g class="a"><path transform="translate(7 9) rotate(45)" d="M0 0q2-4.4 4 0t4 0 4 0 4 0m-3.5-3.2 3.5 3.2-3.5 3.2"/></g>',
        "parts": (("a", "0%{transform:translate(-1px,-1px);opacity:0}18%{opacity:1}56%{transform:translate(8px,8px);opacity:1}"
                        "66%,100%{transform:translate(9.5px,9.5px);opacity:0}", "14px 16px", "2.8s", "ease-in"),
                  ("b", "0%,56%{stroke-dashoffset:1}84%,100%{stroke-dashoffset:0}", "40px 38px", "2.8s", "ease-out"),
                  ("c", "0%,58%,100%{transform:scale(1)}70%{transform:scale(1.04)}", "24px 54px", "2.8s", "ease-in-out")),
    },
    "Science-and-Engineering/Biology/Biochemistry": {
        "draw": '<path class="b" d="M38 22c-3-6-9-10-16-10-9 0-15 8-15 18v4c0 10 7 18 16 18 7 0 12-4 15-10l-9-10Z"/>'
                '<polygon class="a" fill="currentColor" fill-opacity=".2" points="31,32 39,23 50,23 54,32 50,41 39,41"/>',
        "parts": (("a", "0%,22%,92%,100%{transform:translate(0px,0px) rotate(0deg)}48%{transform:translate(4px,-9px) rotate(12deg)}"
                        "68%{transform:translate(3px,-10px) rotate(5deg)}", "42px 32px", "3.2s", "ease-in-out"),
                  ("b", "0%,22%,92%,100%{transform:scale(1)}50%,70%{transform:scale(1.03,.97)}", "20px 32px", "3.2s", "ease-in-out")),
    },
    "Science-and-Engineering/Biology/Genetics": {
        "draw": '<g class="a"><path d="M32 8c14.7 5.1 14.7 6.9 0 12s-14.7 6.9 0 12 14.7 6.9 0 12-14.7 6.9 0 12"/>'
                '<path d="M32 8c-14.7 5.1-14.7 6.9 0 12s14.7 6.9 0 12-14.7 6.9 0 12 14.7 6.9 0 12"/>'
                '<path class="b" stroke-width="1.6" d="M24 12h16M24 16h16M24 24h16M24 28h16M24 36h16M24 40h16M24 48h16M24 52h16"/></g>',
        "parts": (("a", "0%,100%{transform:scaleX(1)}24%{transform:scaleX(.12)}50%{transform:scaleX(-1)}76%{transform:scaleX(-.12)}",
                   "32px 32px", "3s", "linear"),
                  ("b", "0%,50%,100%{opacity:.85}24%,76%{opacity:.2}", "32px 32px", "3s", "linear")),
    },
    "Science-and-Engineering/Biology/Cellular-Biology": {
        "draw": '<path class="a" d="M33 8c13 1 23 10 23 23 0 14-10 25-25 25C17 56 8 46 8 33S19 7 33 8Z"/>'
                '<g class="b"><circle cx="27" cy="29" r="8.5"/><circle cx="29" cy="27" r="2.5" fill="currentColor" stroke="none"/></g>'
                '<g class="c"><rect x="35" y="38" width="13" height="7" rx="3.5"/><path stroke-width="1.2" d="M37.5 41.5 40 39.5l2.5 4 2.5-4 1.5 2"/></g>'
                '<g fill="currentColor" stroke="none"><circle cx="17" cy="44" r="1.8"/><circle cx="44" cy="20" r="1.6"/><circle cx="47" cy="27" r="1.2"/></g>',
        "parts": (("a", "0%,100%{transform:scale(1,1)}25%{transform:scale(1.035,.965)}50%{transform:scale(.97,1.03)}75%{transform:scale(1.02,.98)}",
                   "32px 32px", "3.2s", "ease-in-out"),
                  ("b", "0%,100%{transform:translate(0px,0px) scale(1)}40%{transform:translate(1.4px,0.8px) scale(1.04)}", "27px 29px", "3.2s", "ease-in-out"),
                  ("c", "0%,100%{transform:rotate(0deg)}30%{transform:rotate(-14deg)}70%{transform:rotate(9deg)}", "32px 32px", "3.2s", "ease-in-out")),
    },
    "Science-and-Engineering/Biology/Neuroscience": {
        "draw": '<g class="b"><circle cx="22" cy="21" r="6"/><path d="M22 15v-5m0 0-3-2.5m3 2.5 3-2.5M17.8 16.8 13 12m0 0V8.5m0 3.5H9.5'
                'M16 21h-6m0 0-2.5-2m2.5 2-2.5 2M18 25.5l-4 4.5M27 17l4-4"/></g>'
                '<path d="M26.3 25.3 47 46"/>'
                '<rect x="28.5" y="29.5" width="9" height="5" rx="2.5" transform="rotate(45 33 32)"/>'
                '<rect x="36" y="37" width="9" height="5" rx="2.5" transform="rotate(45 40.5 39.5)"/>'
                '<g class="c"><path d="M47 46l8-1M47 46l2 9M47 46l7.5 6"/><g fill="currentColor" stroke="none"><circle cx="55" cy="45" r="1.8"/>'
                '<circle cx="49" cy="55" r="1.8"/><circle cx="54.5" cy="52" r="1.8"/></g></g>'
                '<circle class="a" cx="26.5" cy="25.5" r="2.8" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translate(0px,0px);opacity:0}8%{opacity:1}20%,32%{transform:translate(0px,0px)}"
                        "42%,54%{transform:translate(10.2px,10.2px)}64%{transform:translate(19px,19px);opacity:1}"
                        "74%,100%{transform:translate(20.5px,20.5px);opacity:0}", "26.5px 25.5px", "2.4s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(1)}10%{transform:scale(1.1)}22%{transform:scale(1)}", "22px 21px", "2.4s", "ease-out"),
                  ("c", "0%,62%{opacity:.5}72%{opacity:1}92%,100%{opacity:.5}", "50px 49px", "2.4s", "ease-in-out")),
    },
    "Science-and-Engineering/Biology/Evolutionary-Biology": {
        "draw": '<g class="a"><polyline pathLength="1" stroke-dasharray="1" points="32,55 32,44 21,33 12,11"/>'
                '<polyline pathLength="1" stroke-dasharray="1" points="32,55 32,44 21,33 26,11"/>'
                '<polyline pathLength="1" stroke-dasharray="1" points="32,55 32,44 43,32 38,11"/>'
                '<polyline pathLength="1" stroke-dasharray="1" points="32,55 32,44 43,32 52,11"/></g>'
                '<g class="b" fill="currentColor" stroke="none"><circle cx="12" cy="11" r="3"/><rect x="23" y="8" width="6" height="6" rx="1"/>'
                '<polygon points="38,7.2 41.6,13.6 34.4,13.6"/><polygon points="52,7 56,11 52,15 48,11"/></g>',
        "parts": (("a", "0%,3%{stroke-dashoffset:1}66%,100%{stroke-dashoffset:0}", "32px 33px", "3s", "ease-out"),
                  ("b", "0%,52%{opacity:0}70%,100%{opacity:1}", "32px 11px", "3s", "ease-in-out")),
    },
    "Science-and-Engineering/Psychology": {
        "draw": '<path d="M22 57v-9c-6-4-10-11-10-19 0-13 10-22 22-22 11 0 20 8 20 19l3 7c.5 1.5 0 2.5-2 2.5h-2v6c0 2.5-2 4.5-4.5 4.5H44v10"/>'
                '<path class="a" d="M24 18c0 8 3 11 8 11s8-3 8-11M32 14v22M28 36h8"/>'
                '<circle class="b" cx="32" cy="25" r="12" opacity=".35" stroke-width="1.2" stroke-dasharray="2 3"/>',
        "parts": (("a", "0%,100%{transform:scale(1)}20%{transform:scale(1.1)}40%{transform:scale(.97)}60%{transform:scale(1.04)}", "32px 25px", "2.4s", "ease-in-out"),
                  ("b", "0%{transform:scale(.6);opacity:.9}100%{transform:scale(1.25);opacity:0}", "32px 25px", "2.4s", "ease-out")),
    },
    "Science-and-Engineering/Psychology/Biological-Psychology": {
        "draw": '<path d="M31 9c-5-3-12-1-14 4-6 0-10 6-8 11-3 4-1 10 4 11 1 5 7 7 11 4 3 3 9 3 12 0 4 3 10 1 11-4 5-1 7-7 4-11 2-5-2-11-8-11-2-4-8-6-12-4Z"/>'
                '<path class="b" stroke-width="1.5" d="M31 9c-3 5 2 9-1 15M18 17c4 0 6 3 5 7M44 16c-3 1-4 4-2 7M15 30c3-2 7-1 9 2M38 32c2-3 7-3 9-1"/>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="M7 51h8l2.5-5 3.5 10 3.5-12 3 7h5l2-3 2 3h4l2.5-6 3 11 2.5-5h7"/>',
        "parts": (("a", "0%,4%{stroke-dashoffset:1}74%,100%{stroke-dashoffset:0}", "31px 50px", "2.4s", "linear"),
                  ("b", "0%,100%{opacity:1}30%{opacity:.35}55%{opacity:.9}80%{opacity:.5}", "31px 24px", "2.4s", "ease-in-out")),
    },
    "Science-and-Engineering/Psychology/Cognitive-Psychology": {
        "draw": '<path d="M21 10h33v44M43 54H10V10"/><path d="M21 10v22M10 43h22M43 21H32v22M43 32v11"/>'
                '<polyline class="a" pathLength="1" stroke-dasharray="1" opacity=".55" stroke-width="1.4" '
                'points="15.5,10 15.5,37.5 26.5,37.5 26.5,15.5 48.5,15.5 48.5,26.5 37.5,26.5 37.5,48.5 48.5,48.5 48.5,54"/>'
                '<circle class="b" cx="15.5" cy="10" r="2.6" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{stroke-dashoffset:1}86%,100%{stroke-dashoffset:0}", "32px 32px", "4.2s", "linear"),
                  ("b", "0%{transform:translate(0px,0px);opacity:1}17%{transform:translate(0px,27.5px)}23%{transform:translate(11px,27.5px)}"
                        "36%{transform:translate(11px,5.5px)}50%{transform:translate(33px,5.5px)}56%{transform:translate(33px,16.5px)}"
                        "63%{transform:translate(22px,16.5px)}76%{transform:translate(22px,38.5px)}83%{transform:translate(33px,38.5px)}"
                        "86%{transform:translate(33px,44px);opacity:1}100%{transform:translate(33px,44px);opacity:0}", "15.5px 10px", "4.2s", "linear")),
    },
    "Science-and-Engineering/Psychology/Personality-Psychology": {
        "draw": '<polygon points="32,11 52.9,26.2 44.9,50.8 19.1,50.8 11.1,26.2"/>'
                '<g opacity=".35" stroke-width="1"><polygon points="32,22 42.5,29.6 38.5,41.9 25.5,41.9 21.5,29.6"/>'
                '<path d="M32 33V11M32 33l20.9-6.8M32 33l12.9 17.8M32 33 19.1 50.8M32 33 11.1 26.2"/></g>'
                '<polygon class="a" fill="currentColor" fill-opacity=".2" points="32,14.3 43.5,29.3 41.7,46.3 26.8,40.1 18.4,28.6"/>'
                '<polygon class="b" opacity=".45" stroke-dasharray="2 2" points="32,22 49.8,27.2 37.8,41 21.7,47.2 19.4,28.9"/>',
        "parts": (("a", "0%,100%{transform:scale(1);opacity:1}44%,61%{transform:scale(.78);opacity:.15}", "32px 33px", "3.6s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(1);opacity:.45}44%,61%{transform:scale(1.05);opacity:1}", "32px 33px", "3.6s", "ease-in-out")),
    },
    "Science-and-Engineering/Psychology/Developmental-Psychology": {
        "draw": '<path d="M6 55h52"/><path opacity=".6" stroke-dasharray="2.5 3" d="M9 31C14 19 27 12 41 11"/><path d="M37.5 7.5 41.2 11l-3.7 3.5"/>'
                '<g class="a"><path d="M10 55v-6a4 4 0 0 1 8 0v6"/><circle cx="14" cy="39.5" r="3.5"/></g>'
                '<g class="b"><path d="M25 55V44a5 5 0 0 1 10 0v11"/><circle cx="30" cy="32" r="4.5"/></g>'
                '<g class="c"><path d="M42 55V40a6 6 0 0 1 12 0v15"/><circle cx="48" cy="25.5" r="5.5"/></g>',
        "parts": (("a", "0%,40%,100%{transform:translateY(0) scale(1,1)}10%{transform:translateY(0) scale(1.1,.88)}"
                        "22%{transform:translateY(-4.5px) scale(.95,1.06)}34%{transform:translateY(0) scale(1.06,.94)}", "14px 55px", "1.8s", "ease-in-out"),
                  ("b", "0%,40%,100%{transform:translateY(0) scale(1,1)}10%{transform:translateY(0) scale(1.08,.9)}"
                        "22%{transform:translateY(-4px) scale(.96,1.05)}34%{transform:translateY(0) scale(1.05,.95)}", "30px 55px", "1.8s", "ease-in-out", "0.2s"),
                  ("c", "0%,40%,100%{transform:translateY(0) scale(1,1)}10%{transform:translateY(0) scale(1.06,.92)}"
                        "22%{transform:translateY(-3.5px) scale(.97,1.04)}34%{transform:translateY(0) scale(1.04,.96)}", "48px 55px", "1.8s", "ease-in-out", "0.4s")),
    },
    "Science-and-Engineering/Psychology/Clinical-Psychology": {
        "draw": '<path d="M12 14h36a4 4 0 0 1 4 4v20a4 4 0 0 1-4 4H28l-9 8v-8h-7a4 4 0 0 1-4-4V18a4 4 0 0 1 4-4Z"/>'
                '<circle class="b" cx="30" cy="28" r="12" stroke-width="1.2" stroke-dasharray="1 3.5" opacity=".5"/>'
                '<path class="a" fill="currentColor" fill-opacity=".2" d="M30 36c-6-4-10-7-10-11a5 5 0 0 1 10-2 5 5 0 0 1 10 2c0 4-4 7-10 11Z"/>',
        "parts": (("a", "0%,100%{transform:scale(.94)}40%,55%{transform:scale(1.1)}", "30px 28px", "5s", "ease-in-out"),
                  ("b", "0%,100%{transform:scale(.88);opacity:.2}40%,55%{transform:scale(1.05);opacity:.6}", "30px 28px", "5s", "ease-in-out")),
    },
    "Science-and-Engineering/Psychology/Social-Psychology": {
        "draw": '<g class="b"><circle cx="15" cy="20" r="4.5"/><path d="M7 36c0-6 3.5-9 8-9s8 3 8 9"/></g>'
                '<g class="c"><circle cx="49" cy="20" r="4.5"/><path d="M41 36c0-6 3.5-9 8-9s8 3 8 9"/></g>'
                '<circle cx="32" cy="30" r="6"/><path d="M21 54c0-9 5-14 11-14s11 5 11 14"/>'
                '<path class="a" stroke-dasharray="2 2.6" opacity=".7" d="M19 13.5Q32 3 45 13.5M20.5 23.5 26 27M43.5 23.5 38 27"/>',
        "parts": (("a", "0%{stroke-dashoffset:0}100%{stroke-dashoffset:-9.2}", "32px 18px", "1.5s", "linear"),
                  ("b", "0%,100%{transform:rotate(0deg)}30%,50%{transform:rotate(7deg)}", "15px 36px", "3s", "ease-in-out"),
                  ("c", "0%,100%{transform:rotate(0deg)}55%,75%{transform:rotate(-7deg)}", "49px 36px", "3s", "ease-in-out")),
    },
    "Science-and-Engineering/Computer-Science": {
        "draw": '<path d="M6 34h52M6 46h52M10.5 34v12M21.5 34v12M32.5 34v12M43.5 34v12M54.5 34v12"/>'
                '<path d="M16 36.5v7M49 36.5v7"/><ellipse cx="38" cy="40" rx="2.6" ry="3.6"/>'
                '<path class="c" d="M27 36.5v7"/>'
                '<g class="a"><rect x="19" y="12" width="16" height="12" rx="2.5"/><polygon points="23.5,24 30.5,24 27,29" fill="currentColor"/>'
                '<circle class="b" cx="27" cy="18" r="2.4" fill="currentColor" stroke="none"/></g>',
        "parts": (("a", "0%,14%{transform:translateX(0)}22%,30%{transform:translateX(11px)}38%,46%{transform:translateX(22px)}"
                        "54%,60%{transform:translateX(11px)}68%,74%{transform:translateX(0)}82%,90%{transform:translateX(-11px)}"
                        "98%,100%{transform:translateX(0)}", "27px 20px", "4.4s", "ease-in-out"),
                  ("b", "0%,3%,12%,64%,74%,100%{opacity:1}7%,69%{opacity:.2}", "27px 18px", "4.4s", "linear"),
                  ("c", "0%,4%{transform:scaleY(0);opacity:0}10%,69%{transform:scaleY(1);opacity:1}75%,100%{transform:scaleY(0);opacity:0}",
                   "27px 40px", "4.4s", "ease-out")),
    },
    "Science-and-Engineering/Computer-Science/Artificial-Intelligence": {
        "draw": '<path opacity=".45" stroke-width="1" d="M16.5 16.9L27.5 14.1M16.3 19.7L27.7 24.3M15.2 21.3L28.8 35.7M14.3 22L29.7 48'
                'M15.3 28.8L28.7 16.2M16.4 30.7L27.6 27.3M16.3 33.5L27.7 37.5M15.3 35.3L28.7 48.7M14.4 42.1L29.6 16.9M15.3 42.7L28.7 29.3'
                'M16.3 44.5L27.7 40.5M16.4 47.3L27.6 50.7M35.9 15.4L48.1 22.6M34.8 16.6L49.2 35.4M36.6 25.8L47.4 25.2M35.9 28.5L48.1 36.5'
                'M35.8 36.4L48.2 27.6M36.6 39L47.4 39M34.7 48.3L49.3 28.7M35.9 49.5L48.1 41.5"/>'
                '<g class="a" fill="currentColor" fill-opacity=".25"><circle cx="12" cy="18" r="3.6"/><circle cx="12" cy="32" r="3.6"/>'
                '<circle cx="12" cy="46" r="3.6"/></g>'
                '<g class="b" fill="currentColor" fill-opacity=".25"><circle cx="32" cy="13" r="3.6"/><circle cx="32" cy="26" r="3.6"/>'
                '<circle cx="32" cy="39" r="3.6"/><circle cx="32" cy="52" r="3.6"/></g>'
                '<g class="c" fill="currentColor" fill-opacity=".25"><circle cx="52" cy="25" r="3.6"/><circle cx="52" cy="39" r="3.6"/></g>',
        "parts": (("a", "0%,100%{opacity:.35}8%,22%{opacity:1}36%{opacity:.35}", "12px 32px", "2.4s", "ease-in-out"),
                  ("b", "0%,26%,100%{opacity:.35}38%,50%{opacity:1}64%{opacity:.35}", "32px 32px", "2.4s", "ease-in-out"),
                  ("c", "0%,54%,100%{opacity:.35}66%,80%{opacity:1}92%{opacity:.35}", "52px 32px", "2.4s", "ease-in-out")),
    },
    "Science-and-Engineering/Computer-Science/Simulations": {
        "draw": '<rect x="8" y="8" width="48" height="48" rx="3"/>'
                '<path opacity=".4" stroke-width="1.2" stroke-dasharray="2 2.5" d="M14 51Q32-17 50 51"/>'
                '<g fill="currentColor" stroke="none" opacity=".55"><circle cx="14" cy="51" r="1.3"/><circle cx="18.5" cy="36.1" r="1.3"/>'
                '<circle cx="23" cy="25.5" r="1.3"/><circle cx="27.5" cy="19.1" r="1.3"/><circle cx="32" cy="17" r="1.3"/>'
                '<circle cx="36.5" cy="19.1" r="1.3"/><circle cx="41" cy="25.5" r="1.3"/><circle cx="45.5" cy="36.1" r="1.3"/>'
                '<circle cx="50" cy="51" r="1.3"/></g>'
                '<circle class="a" cx="32" cy="17" r="3.2" fill="currentColor"/>',
        "parts": (("a", "0%{transform:translate(-18px,34px)}11%{transform:translate(-13.5px,19.1px)}22%{transform:translate(-9px,8.5px)}"
                        "33%{transform:translate(-4.5px,2.1px)}44%{transform:translate(0px,0px)}55%{transform:translate(4.5px,2.1px)}"
                        "66%{transform:translate(9px,8.5px)}77%{transform:translate(13.5px,19.1px)}88%,100%{transform:translate(18px,34px)}",
                   "32px 17px", "2.7s", "steps(1,end)"),),
    },
    "Science-and-Engineering/Computer-Science/Data-Structures-and-Algorithms": {
        "draw": '<path d="M28.8 17.4L22.2 26.6M35.2 17.4L41.8 26.6M17.3 36.1L14.7 43.9M20.7 36.1L23.3 43.9M43.3 36.1L40.7 43.9M46.7 36.1L49.3 43.9"/>'
                '<g fill="currentColor" fill-opacity=".2"><circle cx="32" cy="13" r="4.4"/><circle cx="19" cy="31" r="4.4"/>'
                '<circle cx="45" cy="31" r="4.4"/><circle cx="13" cy="49" r="4.4"/><circle cx="25" cy="49" r="4.4"/>'
                '<circle cx="39" cy="49" r="4.4"/><circle cx="51" cy="49" r="4.4"/></g>'
                '<circle class="a" cx="32" cy="13" r="6.6" stroke-width="1.6"/>',
        "parts": (("a", "0%,8%{transform:translate(0px,0px)}13%,21%{transform:translate(-13px,18px)}26%,34%{transform:translate(-19px,36px)}"
                        "39%,47%{transform:translate(-7px,36px)}52%,60%{transform:translate(13px,18px)}65%,73%{transform:translate(7px,36px)}"
                        "78%,86%{transform:translate(19px,36px)}93%,100%{transform:translate(0px,0px)}", "32px 13px", "4.8s", "ease-in-out"),),
    },
    "Science-and-Engineering/Computer-Science/Computer-Architecture": {
        "draw": '<rect x="7" y="19" width="20" height="20" rx="2"/><path d="M12 19v-4M17 19v-4M22 19v-4M12 39v4M17 39v4M22 39v4"/>'
                '<rect class="b" x="12" y="24" width="10" height="10" rx="1" fill="currentColor" fill-opacity=".25"/>'
                '<rect x="42" y="12" width="15" height="34" rx="2"/><path d="M42 23h15M42 35h15"/>'
                '<path opacity=".6" d="M27 25h15M27 33h15"/>'
                '<path stroke-width="1.5" d="M7 53h5v-5h5v5h5v-5h5v5h5v-5h5v5h5v-5h5v5h5"/>'
                '<rect class="a" x="28" y="23.5" width="3" height="3" fill="currentColor" stroke="none"/>'
                '<rect class="c" x="38" y="31.5" width="3" height="3" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%{transform:translateX(0);opacity:0}12%{opacity:1}50%{transform:translateX(10px);opacity:1}"
                        "58%,100%{transform:translateX(11px);opacity:0}", "29.5px 25px", "2s", "ease-in-out"),
                  ("b", "0%,14%,50%,64%,100%{transform:scale(1)}6%,56%{transform:scale(.8)}", "17px 29px", "2s", "ease-out"),
                  ("c", "0%,46%{transform:translateX(0);opacity:0}56%{opacity:1}92%{transform:translateX(-10px);opacity:1}"
                        "100%{transform:translateX(-11px);opacity:0}", "39.5px 33px", "2s", "ease-in-out")),
    },
    "Science-and-Engineering/Computer-Science/Operating-Systems": {
        "draw": '<path class="c" d="M18 20V11a3 3 0 0 1 3-3h32a3 3 0 0 1 3 3v22a3 3 0 0 1-3 3h-5M18 14h38"/>'
                '<rect x="8" y="20" width="40" height="34" rx="3"/><path d="M8 27h40"/>'
                '<g fill="currentColor" stroke="none"><circle cx="12.5" cy="23.5" r="1.2"/><circle cx="16.5" cy="23.5" r="1.2"/></g>'
                '<path d="M13 33.5l4 3.5-4 3.5"/><path opacity=".5" d="M13 47h22"/>'
                '<path class="b" pathLength="1" stroke-dasharray="1" d="M21 37h12"/>'
                '<rect class="a" x="35" y="33.5" width="3" height="7" fill="currentColor" stroke="none"/>',
        "parts": (("a", "0%,42%{opacity:1}43%,92%{opacity:0}93%,100%{opacity:1}", "36.5px 37px", "1.1s", "linear"),
                  ("b", "0%,10%{stroke-dashoffset:1}60%,100%{stroke-dashoffset:0}", "27px 37px", "2.2s", "steps(6,end)"),
                  ("c", "0%,100%{opacity:.55}45%,60%{opacity:1}", "37px 22px", "2.2s", "ease-in-out")),
    },
    "Science-and-Engineering/Computer-Science/Programming-Languages": {
        "draw": '<path class="a" d="M21 10c-4 0-6 2-6 6v7c0 4-2 7-6 7 4 0 6 3 6 7v7c0 4 2 6 6 6"/>'
                '<path class="b" d="M43 10c4 0 6 2 6 6v7c0 4 2 7 6 7-4 0-6 3-6 7v7c0 4-2 6-6 6"/>'
                '<path class="c" stroke-width="2.6" d="M24 14c3 0 5 1 6 4l10 26M33 26l-9 18"/>',
        "parts": (("a", "0%,100%{transform:translateX(0)}35%{transform:translateX(-2.5px)}60%{transform:translateX(0.8px)}", "15px 30px", "2s", "ease-in-out"),
                  ("b", "0%,100%{transform:translateX(0)}35%{transform:translateX(2.5px)}60%{transform:translateX(-0.8px)}", "49px 30px", "2s", "ease-in-out"),
                  ("c", "0%,100%{transform:rotate(0deg) scale(1)}35%{transform:rotate(-8deg) scale(1.1)}62%{transform:rotate(3deg) scale(.97)}",
                   "32px 30px", "2s", "ease-in-out")),
    },
}
