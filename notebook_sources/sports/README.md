# First to Four — documents and original diagrams

This package owns only the two sports articles, this README, the isolated
diagram generator, its document tests, and generated sports image assets.
Dashboard/home integration, the data engine, PDFs and download ZIP publication
are parent-owned. No existing shared source is modified by this package.

## Standalone articles

- [basketball_rules.tex](basketball_rules.tex): full owner-rule transcription,
  23 figures, zero/one-based game numbering, safety/consent override, visible
  ambiguities, and **three complete identical HIGH JUMP RULES paragraphs**.
- [creator_pitch.tex](creator_pitch.tex): separate original proposal, two
  figures, draft email, roughly 90-second script, flexible 6–10 minute episode,
  permissions/rights plan and a fresh-session measurement/privacy plan.
  Named creators are aspirations, not affiliations, endorsements or contracts.

Both are conventional `article` documents using geometry, amsmath, amssymb,
graphicx, enumitem and hyperref. They contain no external TeX inputs, custom
document class, TikZ, shell escape, dynamic dates or private contact fields.
Compile from the **repository root**, not from this directory: image references
are literal root-relative `tex_images/sports/<slug>.png`. Each article can be
compiled independently. The parent owns Tectonic provisioning and PDF output.

## Build and API

From the repository root, in the selected Python environment:

```text
python -B -m site_content.sports_diagrams
python -B -m unittest site_content.tests.test_sports_documents -v
```

[../../site_content/sports_diagrams.py](../../site_content/sports_diagrams.py)
exports `build_sports_diagrams(root) -> list[Path]` and the immutable `DIAGRAMS`
inventory. The function accepts a `Path` or string, returns **48 absolute paths**
in inventory order (PNG, SVG for each of 24 diagrams), and only writes beneath
`root/tex_images/sports`. Importing it does not generate or publish anything.
It does not read records, traverse private directories, download, build ZIPs or
PDFs, modify the articles, or touch the generated website.

Runtime used: Python 3.12.2, Matplotlib **3.10.9**, NumPy **2.1.3**, with bundled
DejaVu Sans. PNGs are 1920 × 1120; SVG text is retained for inspection/editing.
Fixed SVG hash salt and removed timestamps make repeated builds byte-identical
in the same pinned environment. Font/rasterizer/library upgrades can change
bytes and require asset review; cross-version byte identity is not promised.
The parent project's existing converter needs pypandoc_binary and BeautifulSoup.

## Inventory (24 unique figures, 48 files)

| Group | Figure slugs |
|---|---|
| Format | `format_overview` |
| Shooting | `shooting_progression`, `shooting_attempts`, `shooting_highjump` |
| HORSE | `horse_cycle`, `horse_letters`, `horse_outcomes` |
| 1v1 | `one_on_one_scoring`, `one_on_one_possessions`, `one_on_one_structures` |
| Backboard | `backboard_airborne`, `backboard_attempts`, `backboard_highjump` |
| 3 Point | `three_point_route`, `three_point_assistance`, `three_point_mercy` |
| Rim | `rim_airborne`, `rim_attempts`, `rim_highjump` |
| Bump | `bump_queue`, `bump_chase`, `bump_tactics` |
| Multiplayer | `multiplayer_tiebreak` |
| Pitch-only addition | `creator_episode` |

Every game has three substantive annotated figures. Court markers are schematic,
not official dimensions. HIGH JUMP RULES examples and the 3–3–1 split are hypothetical,
not extra data. Bump tactics never depict people as targets. Safety is a
condition of every tactic, including the up-through-net example.

## Converter and source-ZIP handoff

Use `convert_document(source, image_dir, asset_dir, asset_url, source_root=root)`
with `image_dir=root / "tex_images/sports"`. The articles' active PNG paths are
intentionally root-prefixed; `source_root=root` supplies the additional lookup.
Both convert with zero warnings. Tests check preserved ordered-list starts and
decoded source and copied images, not merely image file extensions.
The installed Pandoc ignores `enumitem`'s `start=0` option alone, so zero-based
lists also use conventional `\setcounter{enumi}{-1}`. This preserves both PDF
and HTML numbering without changing the shared converter. Descriptions render
as visible `figcaption` elements; the converter does not synthesize image alt text.

The parent source ZIP must preserve each active `includegraphics` path. Include
the selected standalone article and **every PNG it references**, retaining the
`tex_images/sports/` tree so compilation from the extracted root works. Include
this README and optional SVG companions/generator for reproducibility. The rules
article references 23 PNGs; the pitch references two, sharing `format_overview`
with the rules. The union is all 24 PNGs. Do not bulk-archive records, raw video,
private contacts or unrelated source directories. This package does not create
or publish the source ZIP itself.

## Interpretation and evidence boundary

- Normal two-player first-to-four is distinct from the multiplayer house
  extension. No invented first-to-five Bump model or unique multiplayer
  tiebreak algorithm is supplied.
- First picker, repeats, countback ties, mercy-count accounting, BALL reset
  handling, made-basket possession/free-throw administration, 3 Point reset
  state and simultaneous finishes remain explicit pre-play agreement items.
- Dinner conventions intentionally differ: Shooting usually for loser(s),
  HORSE for the others win or lose. Both (and costumes) are voluntary opt-in.
- The old financial-access contact joke is **not a rule**. Reckless contact
  stops play for care; there is no credit-card/password/financial access.
- The pitch snapshot is engine-verified: 13 series, 12–1, 50–23 across 73
  challenges, an 11-series streak, best listed winner time 82 seconds, and
  35 holds / 60 within-series transitions. These are descriptions, not future
  odds or causal evidence. Tests intentionally fail if that snapshot changes,
  prompting a reviewed update rather than silent prose regeneration.
- Recording and data publication need separate consent. Only approved
  aggregate fresh-session CSV is proposed; nothing auto-publishes raw/private
  data or sends the draft email.

## Validation scope

[../../site_content/tests/test_sports_documents.py](../../site_content/tests/test_sports_documents.py)
checks standalone structure, owner-rule budgets and named clauses, three complete
HIGH JUMP RULES copies, ambiguity and safety language, figure coverage, real PNG decode,
SVG content, same-environment deterministic generation, generator write scope,
converter warnings/list starts/image copying, and pitch facts against the engine.
All builds/conversions made by tests use temporary directories. No dashboard,
home page, publisher, data engine or historical record is edited.

## Executed standalone PDF check

Both articles were actually compiled with Tectonic 0.17.0 in isolated, untrusted
staging via `python -B -m site_content.pdf --engine <installed-tectonic>`.
The rules PDF is 26 pages (23 figures); the pitch is 7 pages (2 figures).
There are no undefined commands/references, missing glyphs, or overfull boxes.
One underfull paragraph in the rules is harmless spacing, not clipped content.
The two articles still convert without warnings through the existing converter.

The exact name is **HIGH JUMP RULES**, with complete explanations and the creators'
high-jump origin repeated in Shooting, Backboard and Rim. Diagram titles and text
use the same name; stable image filenames have not changed. All 24 original
diagram pairs were regenerated (48 PNG/SVG files).

Observed PDF overflows justified only paragraph emergency stretch in both
articles and xurl-backed `\nolinkurl` for the pitch's three source-credit
filenames. Those filenames remain exact, non-linking inline code in HTML. No
game mechanics, numerical claims, safeguards or substantive pitch prose changed.

The safe cache, fingerprints, inspection evidence and parent handoff are described
in [../../reports/site_content/pdfs/README.md](../../reports/site_content/pdfs/README.md).
The publisher must call `copy_verified_pdf(root, key, assets)` and link only the
returned filename. Missing cache returns `None`; stale/unsafe cache raises an
actionable error rather than providing a stale link. No TeX engine is needed for
that read-only cache validation and copying operation.