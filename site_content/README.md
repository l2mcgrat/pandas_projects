# Portfolio maintenance guide

This package publishes 273 portfolio pages and 24 forwarding pages into an
**existing** static site. Use the independent build for portfolio-only changes. The full
[site generator](../generate_liamms_site.py) now integrates the same publisher.
Every page footer carries the copyright line, and the build writes the site's
`LICENSE.txt` (all rights reserved); the repository's [LICENSE](../LICENSE) is identical.

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
- The publisher owns the 273 portfolio routes and upgrades compatible shared
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

The canonical [mental_map.tex](../mental_map.tex) merges External Brain and the
earlier notebook, plus explicitly marked study additions. Original inputs are
preserved under [notebook_sources/originals](../notebook_sources/originals/).
See the [merge and source guide](../notebook_sources/README.md) before editing or
regenerating. Ordinary publishing never overwrites the canonical source.

**The Mental Map follows the website.** Since 4 October 2026, [mental_map.tex](../mental_map.tex)
is hand-edited and has six numbered sections (fields), 36 subsections (topics) and 216
subsubsections (destinations), numbered like the site; front matter and the image
archive are unnumbered. [restructure.py](restructure.py) produced it once from the
reproducible merge, now archived at
[notebook_sources/merged/](../notebook_sources/merged/mental_map.merged.tex), moving every
block of prose, 682 display blocks, 79 images and every label; its placement table and
[manifest](../notebook_sources/restructure-manifest.json) record where each earlier heading
went. Each outline heading is preceded by `% atlas: <route>` and carries a `\label{sec:...}`;
`atlas.ANCHORS` reads those markers, so each hexagon's centre opens its own section and the
build fails if a marker disappears. Add notes under a destination with
`\subsubsubsection` and `\subparagraph`; the [contribution guide](../notebook_sources/guides/mental_map_guide.tex)
(published as a reader and PDF on the Mental Map) gives the full steps.
The reader has **447 headings, 682 display blocks and 79 images**.
MathJax renders **683 sequentially numbered rows** (1)–(683); block and row
counts differ because of alignment rows and one unnumbered display.

The supplied [Quantum_Mechanics.tex](../Quantum_Mechanics.tex) uses its exact
mixed-case filename, with a lowercase-name compatibility fallback. The hydrogen
reader identifies its editorial corrections; its original is archived. Control
and algorithm readers reuse the same body fragments included in Mental Map.
These focused ZIPs contain fragments, not standalone TeX documents; the Mental
Map ZIP supplies a complete preamble. Use trusted UTF-8 source and local images;
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

## Site atlas: hexagons, icons, routes

[atlas.py](atlas.py) is the single outline: 6 fields → 36 topics → 216
destinations (259 nodes with the centre), validated at import so every parent has
exactly six children. Positions are fixed for every hexagon: top, upper-left,
upper-right, lower-left, bottom, lower-right. Routes are slugs of the titles
(`&` → `and`), e.g. `Science-and-Engineering/Physics/Quantum-Mechanics/`.
`ANCHORS` comes from the Mental Map's `% atlas:` markers (see above).

- **Change requests.** The Mental Map's Request a change button opens a dialog
  ([web/request-change.js](web/request-change.js)) with name, date and cascading
  section/subsection/subsubsection menus from the site outline; it drafts an email to
  l2mcgrat@uwaterloo.ca and stores nothing. Without JavaScript the button is a plain
  `mailto:` link. The database plan is in the Upcoming Changes reader.
- **Website Changes** hosts two dated readers,
  [change_log.tex](../notebook_sources/website/change_log.tex) and
  [upcoming_changes.tex](../notebook_sources/website/upcoming_changes.tex). Feature cards
  show the `date` each item was added.

- [atlas_views.py](atlas_views.py) renders field/topic hexagons, destination
  pages and the home hero. `FEATURES` attaches existing readers/explorers to
  nodes; `HOSTED` destinations are replaced by the real reader, which receives an
  atlas location bar. Edit the route constants there when moving a reader.
- [atlas_tree.py](atlas_tree.py) and [web/atlas-tree.js](web/atlas-tree.js)
  build the radial atlas recursively from a compact nested schema (no 259-node
  hand-written JSON); a static nested list is the no-JS/accessible fallback.
- [icons](icons/) holds 259 original line icons in seven group files. Each part
  animates on hover/focus, or once when scrolled into view on touch screens.
  Run `python -B -m site_content.icons --check` after editing: it enforces safe
  SVG, transform/opacity/dash-only keyframes, 0.4–6 s durations and globally
  unique drawings and animations. Never put a `transform` attribute on an
  animated element; wrap it in `<g>`.
- [creators.py](creators.py) renders the snap-scrolling showcase. Friends'
  entries stay hidden until both `url` and `consent=True` are set. No merch links.
  Owen Paget's consented photo lives in [web/creators](web/creators/) (re-encoded
  without metadata); a highlight with `url=None` shows as "Coming soon".
- `REDIRECTS` in [publishing.py](publishing.py) keeps 24 earlier URLs working,
  including the NBA Analytics → Sports Analytics rename;
  [web/redirect.js](web/redirect.js) preserves query strings and fragments.

## Athletics logs

Running, swimming and weightlifting logs live in
[records/athletics](../records/athletics/) (copies of the files first placed under
LiamMs_PandasProjects; append new entries to the records copies). [athletics.py](athletics.py)
parses them strictly, stopping with a line number on anything unreadable, and never
corrects a written value: the 26 September running average (3:56 written, 3:55.25
computed) is flagged instead. [athletics_views.py](athletics_views.py) renders static
dashboards styled by [web/athletics.css](web/athletics.css) on top of sports.css, with
JSON and CSV downloads, and each has an overview reader from
[notebook_sources/athletics](../notebook_sources/athletics/). The I1 route map in
[tex_images/athletics](../tex_images/athletics/) has its start pin and coordinates removed.
Each dashboard's **Add a session** section shows the file, line format and rebuild
command. If an older copy under LiamMs_PandasProjects/Gaming-and-Performance-Log/Athletics
differs from the records copy, the build stops rather than ignore the edit. Weightlifting
charts plot the heaviest set and the heaviest weight for 10+ and 12+ reps
(`REP_TARGETS`), with reps at the heaviest set on a second axis.

## LeetCode and Rap destinations

[catalog.py](catalog.py) splits leetcode_problems at its column-0 `# Title` comments
and reads every music_work lyric folder; [catalog_views.py](catalog_views.py) renders
the twelve destination pages (escaped code and lyrics in collapsible entries, styled by
[web/catalog.css](web/catalog.css)). Page rules: `MODULE_PAGES`, the Graphs title
pattern, recursion from the syntax tree, dp/memo names, `HARD_TITLES`; lyric folders map
through `RAP_PAGES`, and an unplaced folder lands on Future Projects. Snapshots are
saved as records/site_content/{leetcode,rap}-catalog.json. Nothing is imported or run.

## Sports and the work-term report

The Series Hub (Sports & Entertainment → Series Hub) links to the basketball
Analytics dashboard, House Rules and Creator Petition readers.

- [Basketball source and schema](../records/basketball/README.md): 13 completed
  series, 73 challenges; Liam/Owen series wins 12–1, challenge wins 50–23.
  Winner strings are checked against each played round. The 60 within-series
  transitions comprise 35 holds and 25 switches. Picker identity is inferred
  from the previous winner, not independently recorded; selection is not random.
- [basketball.py](basketball.py) validates and analyzes without changing the raw
  log. [sports_views.py](sports_views.py) and [web/sports.js](web/sports.js) provide
  static charts plus series/round selection, log filters, transition heatmaps,
  and timing coverage. Global totals stay global when filtering the log.
  TBD, N/A and unplayed timings remain missing, not zero. Twelve CSV tables and
  lossless raw/enriched JSON downloads retain the evidence and caveats.
- [House rules](../notebook_sources/sports/basketball_rules.tex) have 23 original
  diagrams, including three per challenge. The separate
  [creator pitch](../notebook_sources/sports/creator_pitch.tex) has two diagrams
  (one shared). [sports_diagrams.py](sports_diagrams.py) regenerates 24 PNG/SVG
  pairs. Unresolved mechanics stay explicit; safety/consent overrides, social
  jokes and actual scoring are kept separate. The pitch is not sent and implies
  no creator affiliation. Team/next-season analysis remains pending.
- [Public report edition](../notebook_sources/work-report/README.md): **Waters
  in a 1D Carbon Nanotube**, linked from About, the résumé and Physics. Its
  completion date is unverified. [work_report.py](work_report.py) preserves the
  scientific content, 96 display blocks, 179 inline math blocks, seven figures,
  one table, nine glossary definitions, eight appendices and eleven references.
  Only the sanitized article and its images are exported; never ZIP the raw
  report folder, private résumé, administrative preamble or original class.

All three new standalone articles have real compiled PDFs. [pdf.py](pdf.py)
stages only validated public source/image inputs and runs an explicitly supplied
Tectonic executable in untrusted mode. Invoke `python -B -m site_content.pdf
--engine <path-to-tectonic>` to regenerate after a source/image edit. The normal
site build needs no TeX engine and copies only hash-verified cached PDFs; stale,
corrupt or partial caches fail with a recompile instruction. Missing caches omit
the PDF link rather than claiming a PDF exists. Keep the three PDF/JSON cache
pairs when distributing a complete source checkout.

[Compilation and inspection evidence](../reports/site_content/pdfs/README.md):
Tectonic 0.17.0 produced a 26-page report, 26-page rules and 7-page pitch. No
undefined commands/references, missing glyphs or overfull boxes remain; the rules
have one harmless underfull paragraph. Repeated PDFs/manifests were byte-identical
in the pinned local compiler/cache environment. Successful compilation and
MathJax rendering are not scientific or legal certification.

## Validation and remaining limits

Build before validation so generated-site audits have manifests; otherwise
they can skip. Run after any concurrent publishing work finishes:

```powershell
& 'C:/Users/anime/AppData/Local/Programs/Python/Python312/python.exe' -B -m unittest discover -s site_content/tests -v
node --check site_content/web/analysis.js
node --check site_content/web/portfolio.js
node --check site_content/web/math-config.js
node --check site_content/web/sports.js
node --check site_content/web/atlas-tree.js
node --check site_content/web/creators.js
node --check site_content/web/redirect.js
& 'C:/Users/anime/AppData/Local/Programs/Python/Python312/python.exe' -B -m site_content.icons --check
```

Site-wide shell audits cover only pages this publisher actually owns/upgrades,
not standalone Phase viewers or their pre-existing SVG identifiers.

Latest complete run: **374 tests, 372 passed, 2 skipped** because native Windows
symlink creation requires permissions unavailable to this account. Atlas browser
checks: all 43 hexagon pages at 320 and 390 pixels with no split words or label
overflow; home, field, topic, destination, reader and atlas pages without page
overflow at 320/390/768/1440; hover animation on every home node; snap scrolling
and the creators cue; redirects preserving query strings. Earlier checks cover
the five sports/report routes at the same widths, with no page
overflow, broken images, duplicate IDs or undefined MathJax commands. All three
PDF/source bundles download successfully. Keyboard round selection, log reset,
picker filters (38 Liam / 22 Owen / 60 combined transitions), TOC navigation,
URL restore and reduced-motion behavior were exercised. Report-specific browser
fixes map `Tilde` to `tilde` and constrain inline math at tablet widths as well
as phones. An inactive browser tab can suppress keyboard/stability events;
repeat interaction checks in the active page before diagnosing a site defect.

The public release audit scanned 334 changed/new generated files, including
seven source ZIPs and the extracted text/metadata of three PDFs, against private
report and résumé fields: no matches. All 176 modified legacy shared-shell
pages had header-only differences; protected content/data were unchanged. The
publishing repository additionally includes byte-preserving source attributes.
Exact staged bytes were checked before commit. Preserve authored CRLF and
historical source whitespace rather than silently altering verified bundles.

The original 110-heading/35-image document remains an exact archived regression
fixture. Tests also cover merged source/manifest reproducibility, every imported
math payload and content-bearing chapter, explicit correction exceptions, all
source-ZIP paths and bytes, original diagrams, public résumé privacy, and both
generated sites. Install [diagram-requirements.txt](diagram-requirements.txt) to
run illustration regeneration/tests; the ordinary publisher uses stored PNGs.

Browser checks of Mental Map, About, résumé, hydrogen, control and algorithm
readers at 390px and 1440px found no horizontal page overflow, missing images,
MathJax errors or undefined commands. All 232 TOC targets exist and numbered rows
are sequential from (1) to (683). Scientific correctness of every historical
derivation is not implied by successful rendering.

Browser review must cover keyboard/mobile navigation, TOC links, local/offline
math, downloads, and timeline hover/focus before and after repeated Reset clicks.
Syntax checks alone cannot verify interactions. Builds are not atomic: failure
can leave mixed output. Full lyric JSON is duplicated for offline readers, so
payload size grows with the corpus. The public résumé is a curated allowlist in
[career.py](career.py); do not publish private template contacts or source files.
Print / Save PDF for the résumé uses the browser, not the original Awesome CV
layout. The work-term report has its own sanitized article/PDF reader; the raw
résumé remains private and no résumé folder is bulk-exported. Credential links still need
independent availability review. Builds update both previews but never commit
or push to the public publishing repository.