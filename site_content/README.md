# Portfolio maintenance guide

This package publishes 13 portfolio pages into an **existing** static site.
Use the independent build for portfolio-only changes. The full
[site generator](../generate_liamms_site.py) now integrates the same publisher.

## Install, build, preview

Requirements: Python **3.12+** and Node.js/npm. [requirements.txt](requirements.txt)
pins `pypandoc_binary==1.17` (bundled Pandoc), `beautifulsoup4==4.15.0`, and
`vaderSentiment==3.3.2`; [package.json](package.json) pins MathJax **3.2.2**.
No TeX engine, NLTK corpus download, or OpenMM installation is needed.
Run in PowerShell; replace the Python executable consistently if necessary:

```powershell
Set-Location 'C:\Users\anime\OneDrive\Desktop\coding_projects\pandas_projects'
& 'C:/Users/anime/AppData/Local/Programs/Python/Python312/python.exe' -B -m pip install -r site_content/requirements.txt
npm ci --prefix site_content
& 'C:/Users/anime/AppData/Local/Programs/Python/Python312/python.exe' -B -m site_content.build --also-local
```

The default target is the sibling **liammspandasprojects** directory if present,
otherwise the workspace's **LiamMs_PandasProjects** directory. `--also-local`
also updates the latter; `--site-dir` selects another existing site.
Each completed target prints `Portfolio generated:` with its absolute output path.
Preview the site, not the source tree; for local output open http://127.0.0.1:8000/:

```powershell
& 'C:/Users/anime/AppData/Local/Programs/Python/Python312/python.exe' -B -m http.server 8000 --bind 127.0.0.1 --directory LiamMs_PandasProjects
```

Stop the preview with Ctrl+C. Installs may access package registries; the build
uses local dependencies and read-only Git provenance queries, with **no Git
commit/push, deployment, or molecular-dynamics (MD) run**. The independent build
does not recompute Smash rankings or execute indexed Python exercises.
MathJax is served locally for offline reading, not from a CDN. A real local npm
installation is required even if an old published vendor copy exists. Do not
commit the dependency installation directory (node_modules); publish the copied
MathJax vendor assets and license with the generated site.

## Ownership and preservation

- Maintain [analysis.py](analysis.py), [latex.py](latex.py), [views.py](views.py),
  [publishing.py](publishing.py), [emotions.json](emotions.json), and
  [web](web/). Generated portfolio HTML/data/assets are overwritten on rebuild.
- This is not a fresh-site bootstrap: base styles/scripts, Smash pages, and
  their assets must already exist. An empty output can leave broken links.
- The publisher owns the 13 portfolio routes and upgrades compatible shared
  shells only. Legacy main IDs/body attributes are retained; headers with extra
  attributes are recognized. Existing Smash bodies/data/models/downloads remain.
- Existing simulations, Phase archives, and standalone viewer/theory shells are
  preserved. The independent build does not copy missing Phase archives between
  targets. Their pre-existing duplicate embedded SVG IDs are **out of scope**,
  intentionally untouched—not silently fixed by shared-shell maintenance.

## Analysis inputs and public-data review

Defaults are sibling **music_work** and **leetcode_problems** working trees;
override with `--music-repo` and `--code-repo`. Present repositories are analyzed
locally and refresh [music](../records/site_content/music-analysis.json) and
[code](../records/site_content/code-analysis.json) snapshots under
[records/site_content](../records/site_content/). No source module is executed.
Missing repositories use saved JSON snapshots, with a console notice **and
published methodology explaining that metrics were not recomputed**. Missing
both repository and snapshot fails; parsing errors in present repositories
also fail rather than silently falling back. Review provenance: a recorded HEAD
does not establish a clean tree, and snapshot freshness/schema/lexicon fingerprints
are not automatically checked. Lexicon edits require rebuilding with local music.

**Public downloads contain full retained lyrics**, not just summaries: JSON,
the offline browser data script, and the line CSV expose original text; other
CSVs provide frequencies, metrics, cue evidence, and duplicate aliases. Source
paths/links are also public. Review authorization and sensitive content before
publishing; pagination is not redaction. JSON remains lossless; HTML escaping
and CSV formula-prefix protection do not anonymize content. Use trusted inputs.

The recorded corpus baseline is **66 retained versions, 34,382 tokens, 5,096
distinct forms, and 4,064 lines**, with **3,635 Unclassified lines**. These are
baseline data counts, not a new test result or permanent archive expectations.
Unclassified means no active cue—not neutrality or absence of emotion.
The 12 families/48 branches are heuristic text-cue labels, **not mental-state
claims, diagnoses, probabilities, or confidence scores**. VADER is separate
polarity scoring; neither system establishes the writer's feelings.
Normalized duplicate texts count once; revisions/repeated verses remain.

For lexicon changes, review evidence/false positives, edit [emotions.json](emotions.json),
deduplicate nonempty cues, and preserve category order unless deliberately
changing tie-breaking. Add phrase/negation/ambiguity cases to
[tests/test_analysis.py](tests/test_analysis.py), rebuild with local music,
and review changed labels. Fewer Unclassified lines alone do not prove accuracy.

## LaTeX readers and source bundles

Keep the original [mental_map.tex](../mental_map.tex) unchanged; its images live
under [tex_images/mental_map](../tex_images/mental_map/). The reader baseline is
**110 headings/TOC entries, 70 inline math spans, 5 display equation blocks,
and all 35 images**. Block counts are not counts of numbered alignment rows.

To add the optional quantum manuscript, create **quantum_mechanics.tex** at the
workspace root and put images under **tex_images/quantum_mechanics** (same stem).
The **next ordinary build automatically replaces the placeholder** with the
reader and ZIP. Use trusted single-file UTF-8 source and local image references;
the image lookup falls back to the source parent if the designated folder is absent.
PNG/JPEG/SVG/GIF/WebP/AVIF are supported; export PDF/EPS figures first. Missing,
remote, absolute, or traversal image paths fail validation.

Source + images ZIPs use the converter's explicit image manifest to recreate
the exact referenced relative paths alongside unchanged TeX. Only current
references enter the bundle; old images left in public assets are excluded.
This does **not** remove stale public files: deliberately review and manually
remove obsolete managed images/downloads without touching unrelated assets.
Deleting a manuscript alone is not an unpublish operation.

Pandoc handles ordinary prose, lists, tables, and headings; `\subsubsubsection`
maps to level four. Supported math environments retain labels/tags for MathJax.
Configure reviewed custom macros in `tex.macros` in
[web/math-config.js](web/math-config.js); escape JavaScript backslashes and use
`[replacement, arity]` for arguments. Supported extensions must be configured
in both `loader.load` and `tex.packages`. Arbitrary preambles are **not compiled**;
source `\newcommand`/`\usepackage` declarations do not configure browser math.
Equation-counter customizations are **rejected, not silently renumbered**;
use explicit `\tag{...}` or design a dedicated converter. This is not a universal
LaTeX compiler: arbitrary TikZ/PGF, multi-file inclusion, bibliography processing,
and package/layout code are not supported. Export figures and flatten sources.
Review conversion warnings and unresolved references; **even reviewed equations
need visual browser verification** of layout, numbering, and cross-references.

## Validation and remaining limits

Build before validation so generated-site audits have manifests; otherwise
they can skip. Run after any concurrent publishing work finishes:

```powershell
& 'C:/Users/anime/AppData/Local/Programs/Python/Python312/python.exe' -B -m unittest discover -s site_content/tests -v
node --check site_content/web/analysis.js
node --check site_content/web/portfolio.js
node --check site_content/web/math-config.js
```

Site-wide shell audits cover only pages this publisher actually owns/upgrades,
not standalone Phase viewers or their pre-existing SVG identifiers.

Verified 2026-09-26: **80 tests run, 79 passed, one skipped** because Windows
denied symlink creation. All three authored scripts passed Node syntax checks.
Browser checks covered 14 routes at 390px and 1440px with no page overflow,
missing images, or JavaScript errors. Equation labels (1)–(5), all 35 images,
word/stopword/song filters, URL restoration, wheel keyboard selection, timeline
focus/deep links, and reduced-motion handling were verified.

Browser review must cover keyboard/mobile navigation, TOC links, local/offline
math, downloads, and timeline hover/focus before and after repeated Reset clicks.
Syntax checks alone cannot verify interactions. Builds are not atomic: failure
can leave mixed output. Full lyric JSON is duplicated for offline readers, so
payload size grows with the corpus. Résumé/work-term report and Honda details
remain placeholders; **no automatic document importer exists**. Supplying PDFs
requires explicit reviewed copying/linking and `about_html()` changes in
[publishing.py](publishing.py); credential links also need independent review.