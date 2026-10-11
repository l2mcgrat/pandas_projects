# Verified standalone PDF cache

This directory contains only generated public artifacts, not original report
sources, classes, raw resume material, private administrative values, compiler
logs, temporary paths or wall-clock timestamps. The JSON manifests are the cache
authority; this guide and the previews are supporting inspection evidence only.

## Parent API

`site_content.pdf.copy_verified_pdf(root: Path, key: str, assets: Path) -> str | None`

- Keys: `work-term-report`, `basketball-rules`, `creator-pitch`.
- Returns `document.pdf` after writing the exact verified PDF into the supplied
  assets directory. All three current artifacts have passed this API check.
- Returns `None` only when both cache files are absent; do not fabricate a link.
- Partial, stale, malformed, mismatched, corrupted or linked paths raise
  `ValueError` with the explicit recompile command. Do not suppress that error
  and fall back to an older PDF.
- Import is stdlib-only. Validation lazily uses the existing public-report and
  LaTeX converters. It never invokes a TeX engine, downloads tools or imports the
  publisher. The report's original-input and privacy checks remain mandatory;
  missing originals do not bypass them.

## Explicit compilation and reproducibility

Run from the repository root with the selected Python:

`python -B -m site_content.pdf --engine <path-to-installed-official-tectonic>`

Optional: `--document work-term-report|basketball-rules|creator-pitch`, and
`--root <fixture-or-repository-root>`. These are explicit operations, separate
from any site build. No integration files or generated site directories were
modified by this compilation task.

The actual engine invocation for each document was:

`tectonic --untrusted --keep-logs --keep-intermediates --outdir output document.tex`

It ran without a shell in a new private temporary directory. The only staged
inputs were the canonical standalone article under a safe filename, plus its
exact converter-mapped PNG inputs at their archive-relative paths. Neither the
original report preamble/class nor arbitrary includes were compiled. Logs and
intermediates were inspected locally and removed with the temporary directory;
only value-free diagnostic counts/line numbers were printed.

The compiler was official **Tectonic 0.17.0**. `SOURCE_DATE_EPOCH=946684800`,
`FORCE_SOURCE_DATE=1`, `TZ=UTC`, and untrusted mode are enforced. The fixed epoch
is a reproducibility input, not a report date. Each manifest records compiler
version/options, SHA256 of the exact canonical source and referenced PNGs with
workspace-relative paths, and the final PDF SHA256. Repeat compiles were
byte-identical in the current compiler/resource environment. Preserve the same
engine and Tectonic resource cache for cross-machine byte comparisons; do not
assume arbitrary compiler/bundle upgrades produce identical bytes.

Individual cache files are replaced atomically after successful compilation,
PDF envelope validation, and a second input validation. A filesystem failure
between the two replacements leaves an incomplete/mismatched pair that the API
rejects. The manifests provide integrity, not an external cryptographic
signature against someone able to replace both PDF and manifest.

## Actual results

| Key | Pages | PDF bytes | Image placements | Final TeX diagnostics |
| --- | ---: | ---: | ---: | --- |
| work-term-report | 26 | 779660 | 7 | None |
| basketball-rules | 26 | 3324471 | 23 | One harmless underfull paragraph |
| creator-pitch | 7 | 391045 | 2 | None |

All three have zero undefined commands, undefined references, missing glyphs,
overfull boxes, LaTeX warnings and package warnings in their final logs.
The historical missing report reference remains an explicit review note, not a
guessed reference or a hidden compiler warning.

### Content-preserving layout adaptations

- Work report: 0.75-inch article margins, 3em emergency stretch, and six
  xurl-backed bibliography addresses. Only URL whitespace, hard breaks and
  underscore escaping changed. These adaptations are recorded by
  `FORMAT_CHANGES` and the regenerated public-edition manifest. All 275 math
  payloads, scientific prose, seven figures, one table, eight appendices and
  eleven references retain their existing preservation tests.
- Sports: exact **HIGH JUMP RULES** naming and complete repeated origin/explanation
  in all three relevant games; matching diagram text; 24 original PNG/SVG pairs.
  Paragraph stretch and breakable, non-linking pitch filenames fix observed
  overflows. All other mechanics, safety/consent rules, prose and snapshot facts
  are unchanged.

## Inspection evidence and limits

Installed **pypdf 6.19.0** parsed every PDF strictly and extracted every page's
text. The existing value-withheld report privacy oracle passed against the
sanitized staged source/images, extracted text, PDF metadata and public
manifests. Extracted report text includes all eight appendix headings, all eleven
reference entries and the explicit unresolved-historical-reference note. The
rules extraction contains all three full high-jump-origin explanations.

The embedded browser did not render PDF pages, so the installed Windows
`Windows.Data.Pdf.PdfDocument` engine was used instead. All **59 pages** rendered
and decoded as nonblank PNGs (1530 by 1980 pixels at this machine's display DPI).
The contact sheets below were visually inspected, alongside full-resolution
pages for the report title, bibliography and wide equation, the complete Shooting
clause, and the pitch source credits. No clipping was observed. This is a layout
and extracted-text privacy check, not new scientific validation, OCR of every
historical figure, or a legal publication-rights determination.

- [Report contact sheet](inspection/work-term-report-contact.png)
- [Rules contact sheet](inspection/basketball-rules-contact.png)
- [Pitch contact sheet](inspection/creator-pitch-contact.png)
- [Report references](inspection/work-term-report-19.png)
- [Report wide equation](inspection/work-term-report-21.png)
- [Complete Shooting clause](inspection/basketball-rules-04.png)
- [Pitch source credits](inspection/creator-pitch-07.png)

The parent owns PDF-link integration and the subsequent full site build/browser
checks. Nothing here commits, pushes or publishes a site.

## Regression tests actually run

`python -B -m unittest site_content.tests.test_pdf site_content.tests.test_work_report site_content.tests.test_sports_documents site_content.tests.test_basketball`

Result: **126 tests, 125 passed, 1 skipped**. The skip is the native Windows
symlink-creation test because this account lacks permission; privilege-independent
symlink/junction checks and native hard-link checks passed. Tests cover missing,
current, stale, partial, tainted and malformed caches; hash and PDF-envelope
corruption; unsafe paths and TeX inputs; protected destinations; failed compiler
output; input changes during compilation; and preserved originals/privacy/math.
The final repeat compile reproduced all three PDFs **and their manifests**
byte-for-byte, and all three real API copies matched their cached PDFs exactly.