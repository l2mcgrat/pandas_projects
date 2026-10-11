"""Reproducibly assemble the Mental Map from immutable imports and study notes.

Run with --write to replace the archived merge in notebook_sources/merged/.
site_content.restructure turns that merge into the outline-shaped mental_map.tex,
which is hand-edited from then on; nothing here overwrites it.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
MERGED = ROOT / 'notebook_sources' / 'merged' / 'mental_map.merged.tex'
SECTION = re.compile(r"(?m)^\\section\{([^{}]+)\}")
LABEL = re.compile(r"\\label\{([^{}]+)\}")
REFERENCE = re.compile(r"\\(ref|eqref|autoref)\{([^{}]+)\}")


def body(text: str) -> str:
    return text.split(r"\begin{document}", 1)[1].rsplit(r"\end{document}", 1)[0]


def sections(text: str) -> list[tuple[str, str]]:
    matches = list(SECTION.finditer(text))
    return [(m[1], text[m.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)])
            for i, m in enumerate(matches)]


def active_text(text: str) -> str:
    """Ignore TeX line comments without mistaking escaped percent for a comment."""
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def normalize_labels(text: str, namespace: str) -> tuple[str, dict]:
    """Never guess which of hundreds of reused equation labels was intended."""
    text = active_text(text)
    counts = Counter(LABEL.findall(text))
    occurrences: Counter[str] = Counter()
    mapping: dict[str, list[str]] = {}
    used: set[str] = set()
    unresolved = []

    def label(match: re.Match[str]) -> str:
        old = match[1]
        occurrences[old] += 1
        new = f'{namespace}-{old.replace(":", "-")}-{occurrences[old]}'
        while new in used:
            new += '-distinct'
        used.add(new)
        mapping.setdefault(old, []).append(new)
        return r"\label{" + new + "}"

    text = LABEL.sub(label, text)

    def reference(match: re.Match[str]) -> str:
        old = match[2]
        # This misspelling has one unambiguous target in the imported source.
        lookup = 'eq:209' if old == 'ep:209' and counts['eq:209'] == 1 else old
        if counts[lookup] == 1:
            return '\\' + match[1] + '{' + mapping[lookup][0] + '}'
        reason = 'ambiguous' if counts[old] > 1 else 'unresolved'
        unresolved.append({'label': old, 'reason': reason, 'candidates': mapping.get(old, [])})
        return r"\textit{[" + reason + ' historical reference: ' + old + ']}'

    return REFERENCE.sub(reference, text), {'labels': mapping, 'referencesNeedingReview': unresolved}


def import_external(text: str) -> tuple[str, dict]:
    text, audit = normalize_labels(body(text), 'eb')
    plots = iter(('derivative-line', 'derivative-square', 'derivative-quartic'))

    def plot(_: re.Match[str]) -> str:
        name = next(plots)
        return (r'\begin{figure}[htbp]\centering' + '\n'
                + r'\includegraphics[width=0.85\linewidth]{tex_images/mental_map/external/' + name + '.png}\n'
                + r'\caption{Recreated from the original pgfplots expression and marked coordinates; domain zero to ten.}'
                + '\n' + r'\end{figure}')

    text, count = re.subn(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', plot, text, flags=re.S)
    if count != 3:
        raise ValueError('Expected exactly three original pgfplots figures; review the import.')
    text = text.replace('0 & 0 & 1 \\i', '0 & 0 & 1 \\\\')
    text = text.replace(r'\vspace{0.025cm}', '').replace(r'\veq{q}', r'\vec{q}')
    text = text.replace(r'\say{string}', "``string''")
    text = re.sub(r'\\includegraphics(\[[^]]*\])?\{(GOODErotvsT.png)\}',
                  r'\\includegraphics\1{tex_images/mental_map/external/\2}', text)
    # Original figure labels were unused and attached to an uncaptioned image.
    text = re.sub(r'\\label\{eb-fig-label-\d+\}', '', text)
    audit['formatCorrections'] = ['Three pgfplots recreated as PNG with original expressions/points.',
                                  'Invalid matrix row-ending \\i changed to \\\\.',
                                  'Six unsupported in-math \\vspace{0.025cm} spacers removed; vector typo \\veq{q} corrected to \\vec{q}.',
                                  'dirtytalk \\say{string} expanded to typographic quotation.',
                                  'Unused original figure label removed; image retained.',
                                  'Misspelled ep:209 reference linked to unique eq:209.']
    return text, audit


def legacy_content(text: str) -> bool:
    stripped = active_text(text)
    stripped = re.sub(r'\\(?:sub)*section\{[^}]+\}|\\(?:newpage|clearpage|maketitle|tableofcontents)', '', stripped)
    return bool(stripped.strip())


def assemble(root: Path = ROOT) -> tuple[str, dict]:
    originals = root / 'notebook_sources' / 'originals'
    old_path = originals / 'mental_map.pre-merge.tex'
    main_path = originals / 'External_Brain' / 'main.tex'
    rotor_path = originals / 'External_Brain' / 'Perturbed Linear Rotor.tex'
    old, original_main, rotor = [p.read_text(encoding='utf-8-sig') for p in (old_path, main_path, rotor_path)]
    external, audit = import_external(original_main)
    chapters = dict(sections(external))
    order = list(chapters)
    retained, outlines = [], []
    for title, content in sections(body(old)):
        target = {'Introduction': 'Introductory Summary', 'Mathematics': 'Math'}.get(title, title)
        if not legacy_content(content):
            outlines.append(title)
            continue
        content = re.sub(r'\\includegraphics(\[[^]]*\])?\{([^}]+)\}',
                         r'\\includegraphics\1{tex_images/mental_map/\2}', content)
        if target in chapters:
            # Macroeconomics/Microeconomics in the old notebook were empty.
            if title == 'Economics':
                content = re.sub(r'\\subsection\{(?:Macroeconomics|Microeconomics)\}', '', content)
            elif title == 'Introduction':
                content = '\\subsection{Earlier perspective}\n' + content
            chapters[target] += '\n\\textit{Retained from the earlier Mental Map.}\n' + content
        else:
            chapters[target] = '\n\\textit{Retained from the earlier Mental Map.}\n' + content
            order.append(target)
        retained.append({'sourceSection': title, 'destinationSection': target})
    # The satellite has meaningful differences from the notebook variant.
    rotor_body, rotor_audit = normalize_labels(body(rotor), 'rotor')
    rotor_body = rotor_body.replace('\\cancelto{1}\n', '')
    chapters['Physics'] += ('\n\\subsection{Perturbed linear rotor -- companion draft}\n'
                            '\\textit{Historical companion manuscript, retained separately because it differs from the version above. '
                            'Its intermediate algebra and numerical claims have not been fully verified. '
                            'See the editorial corrections and conventions at the start of this notebook.}\n' + rotor_body)
    chapters['Engineering'] = ''
    if 'Engineering' not in order:
        order.append('Engineering')
    additions = {'Math': 'math', 'Physics': 'physics', 'Chemistry': 'chemistry',
                 'Computation': 'computation', 'Engineering': 'control', 'Nanotechnology': 'nano'}
    for chapter, name in additions.items():
        fragment = (root / 'notebook_sources' / 'additions' / (name + '.tex')).read_text(encoding='utf-8')
        chapters[chapter] = '\n' + fragment + '\n\\textit{Historical notes follow; read alongside the editorial corrections.}\n' + chapters.get(chapter, '')
    # Preserve useful stable top-level anchors from the first edition.
    for title in ('Philosophy', 'Business', 'History', 'Sociology', 'YouTube Videos'):
        if title not in chapters:
            chapters[title] = '\nOutline retained from the earlier Mental Map; no original prose was supplied for this heading.\n'
            order.append(title)
    order = ['Introductory Summary', 'Philosophy', 'Sciences', 'Math', 'Physics', 'Chemistry', 'Biology',
             'Psychology', 'Computation', 'Machine Learning/Data Science/Artificial Intelligence',
             'Nanotechnology', 'Engineering', 'Business', 'Economics', 'History', 'Sociology',
             'Theology', 'Job Related Endeavors',
             "Things I understand at a High Level, but I don't understand at a Low enough Level", 'YouTube Videos']
    chapters['Introductory Summary'] = (root / 'notebook_sources' / 'editorial.tex').read_text(encoding='utf-8') + chapters['Introductory Summary']
    preamble = old.split(r'\begin{document}', 1)[0]
    preamble = preamble.replace(r'\title{Mental Map}', r'\title{Mental Map: An External Brain}')
    preamble += '\\DeclareMathOperator{\\Tr}{Tr}\n'
    output = preamble + '\n\\begin{document}\n\\maketitle\n\\tableofcontents\n'
    for title in order:
        output += '\n% BEGIN MERGED CHAPTER: ' + title + '\n\\section{' + title + '}\n' + chapters[title]
    output += '\n\\section{Imported image archive}\n'
    output += ('These supplementary assets arrived with External Brain. Their original authorship, dates and reuse permissions '
               'were not documented in the supplied folder. They are preserved as historical notebook assets, '
               'not presented as newly generated research results. The original working rotation plot also remains at its original discussion.\n')
    for name in ('ExternalBrain.jpg', 'universe.jpg', 'Oblate.jpg', 'BADErotvsT.png'):
        output += ('\n\\begin{figure}[htbp]\\centering\n\\includegraphics[width=0.85\\linewidth]{tex_images/mental_map/external/'
                   + name + '}\n\\caption{Imported historical asset: ' + name.replace('_', r'\_') + '. Context and attribution need review.}\n\\end{figure}\n')
    output += '\n\\end{document}\n'
    manifest = {'schemaVersion': 1, 'sources': {p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest()
                                              for p in sorted(originals.rglob('*')) if p.is_file()},
                'retainedEarlierSections': retained, 'archivedOutlineSections': outlines,
                'externalBrain': audit, 'companionRotor': rotor_audit, 'studyAdditions': additions,
                'policy': 'Historical prose retained; comments/preambles preserved in immutable originals. Ambiguous references are visible review notes, never guessed links.',
                'outputSha256': sha256(output.encode('utf-8')).hexdigest()}
    return output, manifest


def import_assets(root: Path = ROOT) -> None:
    """Copy supplied assets and faithfully redraw the three original pgfplots."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    target = root / 'tex_images' / 'mental_map' / 'external'
    target.mkdir(parents=True, exist_ok=True)
    for image in (root / 'notebook_sources' / 'originals' / 'External_Brain').iterdir():
        if image.suffix.lower() in {'.jpg', '.png'}:
            shutil.copy2(image, target / image.name)
    x = np.linspace(0, 10, 200)
    for name, f, expression in [('line', lambda x: 10*x+5, '10x + 5'),
                                ('square', lambda x: x**2, 'x²'), ('quartic', lambda x: x**4, 'x⁴')]:
        fig, ax = plt.subplots(figsize=(7, 4), layout='constrained')
        ax.plot(x, f(x), color='#273959', label='f(x) = ' + expression)
        if name != 'line':
            for points, color in [([2, 4, 6, 8, 10], '#7854a3'), ([2, 6, 10], '#bf3f43')]:
                points = np.array(points)
                ax.scatter(points, f(points), marker='x', c=color)
        ax.set(xlabel='x', ylabel='f(x)', title='Original calculus example: ' + expression)
        ax.grid(alpha=.2)
        ax.legend()
        fig.savefig(target / ('derivative-' + name + '.png'), dpi=160)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Explicitly replace the archived merge and merge manifest')
    args = parser.parse_args()
    output, manifest = assemble()
    if args.write:
        import_assets()
        MERGED.write_text(output, encoding='utf-8', newline='\n')
        (ROOT / 'notebook_sources' / 'merge-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Merged notebook: {len(output.splitlines())} lines; write={args.write}')


if __name__ == '__main__':
    main()