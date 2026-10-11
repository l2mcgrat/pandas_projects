# Mental Map source and editorial history

## What is authoritative?

- **[../mental_map.tex](../mental_map.tex)** is the assembled, single-file reader source.
- **[originals/](originals/)** contains byte-identical imports: the earlier Mental Map, every supplied External Brain file, and the original November 2023 quantum manuscript. Never regenerate these from edited documents.
- **[additions/](additions/)** contains six explicitly marked AI-assisted study-note fragments: maths, physics, chemistry, computation, control and nanotechnology. Edit these for the new material.
- **[editorial.tex](editorial.tex)** records provenance, assumptions and identified historical errors. These corrections are not a claim of complete scientific review.
- **[merge-manifest.json](merge-manifest.json)** records every original file's SHA-256, retained chapters, equation-label mapping, ambiguous reference candidates and the assembled source hash.
- **[../Quantum_Mechanics.tex](../Quantum_Mechanics.tex)** is the separately edited hydrogen reader. Its normalized Laguerre radial functions, angular equation, reduced mass and checks replace errors in the archived version. Letter case matters on Linux.

## Merge policy

External Brain supplies the main structure. All eight content-bearing chapters from the earlier Mental Map are retained in appropriate chapters: introduction, sciences, psychology, ML/NLP, nanotechnology, economics, theology and job-related study. Empty scaffolding is preserved in the original archive; broad future-writing headings remain in the reader. Existing deep sections, not merely their headings, remain intact.

The companion rotor manuscript differs from the corresponding main-notebook material. Both versions remain, with the companion explicitly labelled historical and unverified. Dates, economic tables, job advertisements and informal speculation are not presented as current verified facts or new employment claims.

Hundreds of copied labels in External Brain originally reused `eq:1`, `eq:256` and others. Every imported occurrence is now uniquely namespaced. Unique references are updated; ambiguous/missing references become visible editorial notes instead of guessing their targets. `ep:209` is corrected to its unique `eq:209` target. The manifest provides candidate identifiers for subsequent human review.

Limited layout/syntax corrections: one matrix `\i` row ending, one `\veq{q}` vector typo, six in-math `\vspace` spacers, one dirtytalk quotation, and an orphan companion cancellation command. Scientific claims remain, with prominent corrections for the calculus slope, boson spin, p–n junction carriers, rotor energy/matrix conventions and canonical internal energy. Originals remain available for comparison.

## Illustrations and attribution

There are **36 original study diagrams**, each supplied as PNG and SVG, produced by [../site_content/diagrams.py](../site_content/diagrams.py). PNGs are referenced in LaTeX for conventional compilation. Captions state schematic assumptions and normalized units. Three original pgfplots expressions (`10*x+5`, `x^2`, `x^4`) and their marked sample coordinates are redrawn by the notebook assembler. All five supplied External Brain images are copied byte-for-byte; four previously unreferenced/commented images appear in an explicitly historical gallery. The earlier 35 image references remain.

Authorship and reuse permissions for imported images were not established by the supplied files. Review attribution before a public release. New diagrams do not assert ownership of older textbook/course illustrations. The 2022/23 Waterloo calendars guide scope only; some entries postdate the degree. Only SYDE 352 completion is specifically confirmed by the owner, and DSA is described as self-taught.

## Regeneration and publishing

The ordinary portfolio build **does not overwrite the canonical notebook**. To regenerate after editing fragments, run the selected Python interpreter with `-B -m site_content.notebook --write`. This is an explicit replacement operation; move direct canonical edits into the appropriate inputs first. `-B -m site_content.notebook` computes the merge without writing.

Optional illustration regeneration uses `-B -m site_content.diagrams`. Rendering dependencies are separate in [../site_content/diagram-requirements.txt](../site_content/diagram-requirements.txt). Byte reproducibility is tested within the selected rendering environment, not across different fonts or library releases.

Then build with `-B -m site_content.build --also-local` and test with `-B -m unittest discover -s site_content/tests`. This updates the sibling publishing repository and workspace preview but **never commits or pushes**. Full generator runs are not needed and would recalculate unrelated Smash content.

The canonical source ZIP reconstructs every active image path. The focused control/algorithm downloads contain **body fragments**, intended for inclusion in an article using amsmath, amssymb, graphicx and hyperref; the full Mental Map ZIP includes the complete preamble. Bibliography/import comments and unused assets remain in the archival source folder rather than being silently discarded.

## Résumé privacy and limitations

[../site_content/career.py](../site_content/career.py) is an explicit public allowlist of résumé facts, not a bulk export of the supplied Awesome CV template. The public HTML excludes private phone/email/address and original source downloads. Honda work is described as supporting Manufacturing Division **with** Pillar Leads, without an invented division-transition date or claim of division oversight. Current job dates come from the résumé.

Print / Save PDF creates a browser-formatted résumé. No original Awesome CV PDF was compiled: a XeLaTeX installation was not available. The original template and license notices remain untouched. **The local résumé folder contains private contacts; do not publish or commit it to a public repository without reviewing/redacting those files.** Work-term-report publication has not been integrated in this change.