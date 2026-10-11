"""Validated, uniquely animated line icons for all 259 atlas nodes.

Each group module exports ICONS = {node_key: {"draw": svg_children, "parts": (...)}}.
A part is (class, keyframes, transform_origin, duration, easing[, delay]).
Run ``python -B -m site_content.icons --check [group ...]`` while authoring.
"""

from __future__ import annotations

import argparse
from hashlib import sha1
from html import escape
from html.parser import HTMLParser
from importlib import import_module
from pathlib import Path
import re

from ..atlas import NODES

GROUPS = {
    "base": "", "science": "Science-and-Engineering", "business": "Business-and-Economics",
    "career": "Career-and-Education", "sports": "Sports-and-Entertainment",
    "gaming": "Gaming-and-Performance-Log", "language": "Language-and-Programming",
}
BASE_KEYS = frozenset({
    "root", "Gaming-and-Performance-Log", "Business-and-Economics", "Business-and-Economics/Macroeconomics",
    "Science-and-Engineering/Physics", "Language-and-Programming", "Sports-and-Entertainment",
    "Language-and-Programming/Coding-Projects/Miscellaneous",
})

_NUMBER = r"-?\d+(?:\.\d+)?"
_ATTRIBUTES = {
    "d": r"[MmLlHhVvCcSsQqTtAaZz0-9.,\-\s]+",
    "points": r"[0-9.,\-\s]+",
    **{name: _NUMBER for name in ("cx", "cy", "r", "rx", "ry", "x", "y", "width", "height",
                                  "x1", "y1", "x2", "y2", "stroke-width", "pathlength")},
    "opacity": r"0?\.\d+|1", "fill-opacity": r"0?\.\d+|1",
    "transform": r"(?:(?:translate|rotate|scale|skewX|skewY)\([-0-9.,\s]+\)\s*)+",
    "class": r"[abc]", "fill": r"none|currentColor", "stroke": r"none|currentColor",
    "stroke-dasharray": r"[0-9.\s,]+", "stroke-linecap": r"round|butt|square",
    "stroke-linejoin": r"round|miter|bevel",
}
_TAGS = {"path", "circle", "ellipse", "rect", "line", "polyline", "polygon", "g"}
_EASING = re.compile(r"linear|ease|ease-in|ease-out|ease-in-out|steps\(\d{1,2}(?:,\s*(?:start|end|jump-none|jump-both))?\)"
                     r"|cubic-bezier\((?:-?\d*\.?\d+,\s*){3}-?\d*\.?\d+\)")
_FRAMES = re.compile(r"(?:(?:\d{1,3}%)(?:,\d{1,3}%)*\{[^{}]+\})+")
_TRANSFORM = re.compile(r"(?:(?:translate|translateX|translateY|rotate|scale|scaleX|scaleY|skewX|skewY)"
                        r"\(\s*-?\d*\.?\d+(?:px|deg)?(?:\s*,\s*-?\d*\.?\d+(?:px|deg)?)?\s*\)\s*)+|none")


class _Markup(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.errors: list[str] = []
        self.classes: set[str] = set()
        self.elements = 0
        self.stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        self._element(tag, attrs)
        self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self._element(tag, attrs)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            self.errors.append(f"unbalanced </{tag}>")

    def handle_data(self, data):
        if data.strip():
            self.errors.append("text content is not allowed")

    def handle_entityref(self, name):
        self.errors.append("entities are not allowed")

    handle_charref = handle_entityref

    def handle_comment(self, data):
        self.errors.append("comments are not allowed")

    def _element(self, tag, attrs):
        self.elements += 1
        if tag not in _TAGS:
            self.errors.append(f"<{tag}> is not allowed")
        for name, value in attrs:
            # HTMLParser lowercases names; browsers restore SVG pathLength casing.
            pattern = _ATTRIBUTES.get(name)
            if pattern is None or value is None or not re.fullmatch(pattern, value):
                self.errors.append(f"unsafe or unsupported {name}={value!r} on <{tag}>")
            elif name == "class":
                self.classes.add(value)


def _normal(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _frames_ok(frames: str) -> list[str]:
    errors = []
    compact = re.sub(r"\s*([,{}])\s*", r"\1", frames.strip())
    if not _FRAMES.fullmatch(compact):
        return ["keyframes must look like '0%,100%{...}50%{...}'"]
    stops = {int(stop) for stop in re.findall(r"(\d{1,3})%(?=[,{])", compact)}
    if 0 not in stops or 100 not in stops or max(stops) > 100:
        errors.append("keyframes need explicit 0% and 100% stops within 0-100%")
    for block in re.findall(r"\{([^{}]+)\}", frames):
        for declaration in filter(None, (part.strip() for part in block.split(";"))):
            name, _, value = (item.strip() for item in declaration.partition(":"))
            if name == "transform" and _TRANSFORM.fullmatch(value):
                continue
            if name == "opacity" and re.fullmatch(r"0?\.\d+|0|1", value):
                continue
            if name == "stroke-dashoffset" and re.fullmatch(_NUMBER + r"(?:px)?", value):
                continue
            errors.append(f"unsupported keyframe declaration {declaration!r}")
    return errors


def validate(icons: dict[str, dict], allowed: set[str] | None = None) -> list[str]:
    errors, drawings, motions = [], {}, {}
    for key, icon in icons.items():
        where = f"{key}: "
        if key not in NODES:
            errors.append(where + "not an atlas node")
        if allowed is not None and key not in allowed:
            errors.append(where + "belongs to another group")
        if not isinstance(icon, dict) or set(icon) != {"draw", "parts"}:
            errors.append(where + "expected exactly 'draw' and 'parts'")
            continue
        parser = _Markup()
        parser.feed(icon["draw"])
        parser.close()
        if parser.stack:
            errors.append(where + "unclosed element")
        errors.extend(where + error for error in parser.errors)
        if parser.elements < 2:
            errors.append(where + "draw at least two elements")
        parts = icon["parts"]
        if not isinstance(parts, tuple) or not 1 <= len(parts) <= 3:
            errors.append(where + "parts must be a tuple of one to three animations")
            continue
        seen = set()
        for part in parts:
            if not isinstance(part, tuple) or len(part) not in (5, 6):
                errors.append(where + "each part is (class, frames, origin, duration, easing[, delay])")
                continue
            cls, frames, origin, duration, easing, *delay = part
            if cls not in {"a", "b", "c"} or cls in seen or cls not in parser.classes:
                errors.append(where + f"part class {cls!r} must be unique and used in draw")
            seen.add(cls)
            errors.extend(where + error for error in _frames_ok(frames))
            if not re.fullmatch(_NUMBER + r"px " + _NUMBER + r"px", origin):
                errors.append(where + f"origin {origin!r} must be 'Xpx Ypx'")
            seconds = re.fullmatch(r"(\d+(?:\.\d+)?)s", duration)
            if not seconds or not 0.4 <= float(seconds[1]) <= 6:
                errors.append(where + "duration must be 0.4s-6s")
            if not _EASING.fullmatch(easing):
                errors.append(where + f"unsupported easing {easing!r}")
            if delay and not re.fullmatch(r"\d(?:\.\d+)?s", delay[0]):
                errors.append(where + "delay must look like 0.2s")
            motion = _normal(frames)
            if motion in motions:
                errors.append(where + f"keyframes duplicate {motions[motion]}")
            motions.setdefault(motion, key)
        if parser.classes - seen:
            errors.append(where + "every animated class needs a part")
        drawing = _normal(icon["draw"])
        if drawing in drawings:
            errors.append(where + f"drawing duplicates {drawings[drawing]}")
        drawings.setdefault(drawing, key)
    return errors


def group_keys(group: str) -> set[str]:
    prefix = GROUPS[group]
    if not prefix:
        return set(BASE_KEYS)
    return {key for key in NODES if (key == prefix or key.startswith(prefix + "/")) and key not in BASE_KEYS}


def load(groups=GROUPS) -> dict[str, dict]:
    icons: dict[str, dict] = {}
    for group in groups:
        try:
            module = import_module(f"{__name__}.{group}")
        except ModuleNotFoundError as error:
            if error.name != f"{__name__}.{group}":
                raise
            continue
        overlap = set(icons) & set(module.ICONS)
        if overlap:
            raise ValueError(f"Duplicate icon keys: {sorted(overlap)}")
        icons.update(module.ICONS)
    return icons


ICONS = load()


def require_complete(icons: dict[str, dict] | None = None) -> None:
    icons = ICONS if icons is None else icons
    errors = validate(icons)
    missing = sorted(set(NODES) - set(icons))
    if missing:
        errors.append(f"{len(missing)} atlas nodes have no icon, e.g. {missing[:3]}")
    if errors:
        raise ValueError("Icon registry is invalid:\n" + "\n".join(errors[:40]))


def css_class(key: str) -> str:
    return "ai-" + sha1(key.encode("utf-8")).hexdigest()[:8]


def icon_svg(key: str, extra: str = "") -> str:
    name = css_class(key) + (" " + escape(extra, quote=True) if extra else "")
    return (f'<svg class="atlas-icon {name}" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{ICONS[key]["draw"]}</svg>')


def icons_css(icons: dict[str, dict] | None = None) -> str:
    icons = ICONS if icons is None else icons
    parts = ".atlas-icon :is(.a,.b,.c)"
    rules = [f"{parts}{{transform-box:view-box;transform-origin:var(--o)}}"
             f".atlas-hover:is(:hover,:focus-visible) {parts},.is-playing {parts},.atlas-icon.is-playing :is(.a,.b,.c)"
             "{animation:var(--n) var(--t) infinite}"]
    for key in sorted(icons, key=lambda item: css_class(item)):
        name = css_class(key)
        for cls, frames, origin, duration, easing, *delay in icons[key]["parts"]:
            timing = " ".join([duration, easing, *delay])
            rules.append(f".{name} .{cls}{{--o:{origin};--n:{name}-{cls};--t:{timing}}}"
                         f"@keyframes {name}-{cls}{{{_normal(frames)}}}")
    rules.append("@media (prefers-reduced-motion:reduce){.atlas-icon *{animation:none!important}}")
    return "\n".join(rules) + "\n"


def preview(keys: list[str]) -> str:
    """Standalone local review sheet; hover a tile or tick 'play all'."""
    tiles = "".join(f'<a class="atlas-hover tile" href="#{escape(key)}" id="{escape(key)}">{icon_svg(key)}'
                    f'<span>{escape(NODES[key].title)}</span><small>{escape(key)}</small></a>' for key in keys)
    return (f"<!doctype html><meta charset=utf-8><title>Icon preview</title><style>{icons_css()}"
            "body{background:#141826;color:#d9d3ff;font:12px system-ui;margin:24px}"
            ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px}"
            ".tile{display:grid;justify-items:center;gap:6px;padding:14px;border:1px solid #3a3f5c;border-radius:10px;color:inherit;text-decoration:none}"
            ".tile svg{width:72px;height:72px}.tile small{color:#8088a8;font-size:9px;word-break:break-all;text-align:center}"
            "label{display:block;margin-bottom:16px}</style>"
            "<label><input type=checkbox onchange=\"document.body.classList.toggle('is-playing',this.checked)\"> Play all</label>"
            f"<div class=grid>{tiles}</div>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", nargs="*", metavar="GROUP", help="Validate groups (default: all, requiring 259 icons)")
    parser.add_argument("--preview", nargs=2, metavar=("GROUP", "HTML"), help="Write a local hover preview for one group")
    args = parser.parse_args(argv)
    if args.preview:
        group, target = args.preview
        Path(target).write_text(preview(sorted(set(ICONS) & group_keys(group))), encoding="utf-8")
        print(f"Preview written: {target}")
    groups = args.check if args.check else list(GROUPS)
    errors = validate(ICONS)
    for group in groups:
        module_icons = load([group])
        allowed = group_keys(group)
        errors += [f"[{group}] {error}" for error in validate(module_icons, allowed)]
        missing = sorted(allowed - set(module_icons))
        print(f"{group}: {len(module_icons)}/{len(allowed)} icons" + (f"; missing {missing}" if missing else ""))
    if not args.check:
        missing = set(NODES) - set(ICONS)
        if missing:
            errors.append(f"{len(missing)} atlas nodes still need icons")
    for error in dict.fromkeys(errors):
        print("ERROR", error)
    print("OK" if not errors else f"{len(set(errors))} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
