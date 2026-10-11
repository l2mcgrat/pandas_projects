"""The eight earlier symbols, redrawn on one grid with their own animations."""

ICONS = {
    "root": {
        "draw": '<g class="a"><path d="M32 32 12 19m20 13 20-13M32 32v23m0-23V9M32 32 12 46m20-14 20 14"/>'
                '<circle cx="12" cy="19" r="4"/><circle cx="52" cy="19" r="4"/><circle cx="12" cy="46" r="4"/>'
                '<circle cx="52" cy="46" r="4"/><circle cx="32" cy="9" r="4"/><circle cx="32" cy="55" r="4"/></g>'
                '<circle class="b" cx="32" cy="32" r="7"/>',
        "parts": (("a", "0%,100%{transform:scale(1)}50%{transform:scale(1.09)}", "32px 32px", "1.8s", "ease-in-out"),
                  ("b", "0%,100%{opacity:1}35%{opacity:.3}70%{opacity:.85}", "32px 32px", "1.8s", "ease-in-out")),
    },
    "Gaming-and-Performance-Log": {
        "draw": '<g class="a"><path d="M18 22h28l6 21c1 5-4 8-8 4l-6-6H26l-6 6c-4 4-9 1-8-4Z"/><path d="M23 27v12m-6-6h12"/>'
                '<g class="b"><circle cx="41" cy="29" r="2"/><circle cx="46" cy="35" r="2"/></g></g>',
        "parts": (("a", "0%,100%{transform:rotate(0deg)}20%{transform:rotate(-7deg)}40%{transform:rotate(6deg)}"
                        "60%{transform:rotate(-4deg)}80%{transform:rotate(2deg)}", "32px 36px", "1.2s", "ease-in-out"),
                  ("b", "0%,49%,100%{opacity:1}50%,74%{opacity:.15}", "43px 32px", "0.6s", "steps(1,end)")),
    },
    "Business-and-Economics": {
        "draw": '<g class="a"><rect x="12" y="20" width="40" height="30" rx="5"/><path d="M24 20v-7h16v7M12 32q20 12 40 0M28 35h8"/></g>',
        "parts": (("a", "0%,100%{transform:translateY(0) scale(1,1)}30%{transform:translateY(-4px) scale(.97,1.03)}"
                        "60%{transform:translateY(0) scale(1.04,.96)}", "32px 50px", "1.4s", "ease-in-out"),),
    },
    "Business-and-Economics/Macroeconomics": {
        "draw": '<path d="M12 48h40"/><path class="b" d="M16 41V30m10 11V24m11 17V19m11 22V10"/>'
                '<path class="a" pathLength="1" stroke-dasharray="1" d="m12 25 13-9 11 3L51 7"/>',
        "parts": (("a", "0%{stroke-dashoffset:1}60%,100%{stroke-dashoffset:0}", "32px 16px", "1.8s", "ease-out"),
                  ("b", "0%,100%{transform:scaleY(1)}50%{transform:scaleY(.78)}", "32px 41px", "1.8s", "ease-in-out")),
    },
    "Science-and-Engineering/Physics": {
        "draw": '<g class="a"><ellipse cx="32" cy="32" rx="25" ry="10"/><ellipse cx="32" cy="32" rx="25" ry="10" transform="rotate(60 32 32)"/>'
                '<ellipse cx="32" cy="32" rx="25" ry="10" transform="rotate(120 32 32)"/></g><circle class="b" cx="32" cy="32" r="4"/>',
        "parts": (("a", "0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}", "32px 32px", "6s", "linear"),
                  ("b", "0%,100%{transform:scale(1)}50%{transform:scale(1.55)}", "32px 32px", "1s", "ease-in-out")),
    },
    "Language-and-Programming": {
        "draw": '<path class="b" d="M14 14h36v28H29L17 51v-9h-3Z"/><path class="a" d="M22 27v6m7-12v18m7-16v12m7-9v6"/>',
        "parts": (("a", "0%,100%{transform:scaleY(1)}25%{transform:scaleY(.45)}75%{transform:scaleY(1.22)}", "32px 30px", "1.1s", "ease-in-out"),
                  ("b", "0%,100%{transform:rotate(0deg)}50%{transform:rotate(-4deg)}", "17px 51px", "2.2s", "ease-in-out")),
    },
    "Sports-and-Entertainment": {
        "draw": '<g class="a"><circle cx="32" cy="12" r="7"/><path d="M25 12h14M32 5v14"/></g>'
                '<ellipse cx="32" cy="28" rx="13" ry="3.5"/>'
                '<path class="b" d="m20 30 5 17h14l5-17M26 31l2 16m4-15v15m6-16-2 16M22 37h20M24 43h16"/>',
        "parts": (("a", "0%,100%{transform:translateY(0) scale(1);opacity:1}45%{transform:translateY(19px) scale(.82);opacity:1}"
                        "62%{transform:translateY(31px) scale(.74);opacity:0}63%{transform:translateY(-10px) scale(1);opacity:0}"
                        "82%{transform:translateY(0) scale(1);opacity:1}", "32px 12px", "1.6s", "ease-in"),
                  ("b", "0%,40%,100%{transform:scale(1,1)}55%{transform:scale(.9,1.14)}70%{transform:scale(1.04,.96)}",
                   "32px 30px", "1.6s", "ease-in-out")),
    },
    "Language-and-Programming/Coding-Projects/Miscellaneous": {
        "draw": '<path class="a" d="m32 8 7 17 17 7-17 7-7 17-7-17-17-7 17-7Z"/><circle class="b" cx="32" cy="32" r="5"/>',
        "parts": (("a", "0%{transform:rotate(0deg) scale(1)}50%{transform:rotate(45deg) scale(.82)}100%{transform:rotate(90deg) scale(1)}",
                   "32px 32px", "1.6s", "ease-in-out"),
                  ("b", "0%,100%{opacity:1}30%{opacity:.2}60%{opacity:.8}", "32px 32px", "1.6s", "linear")),
    },
}
