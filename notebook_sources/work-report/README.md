# Public work-term report edition

This directory holds the reproducible public article edition of **Waters in a
1D Carbon Nanotube**, an **undated historical 3B Nanotechnology Engineering
work-term report**. The automatically generated date in the original is not
evidence of its completion date. Dates within the written references are retained
as bibliography content, not promoted to report metadata.

## Ownership and publication boundary

- The importer reads the original report and glossary in the private working
  folder. It never modifies those originals.
- The generator writes exactly two files in this directory: the public article
  source and its JSON manifest. This guide is maintained separately.
- Only the sanitized article and the seven referenced PNG images belong in a
  public source bundle. Do **not** ZIP the original report folder, copy its
  original source/glossary, or distribute the custom document class.
- Student identifiers, account identifiers, street/location/postal metadata,
  the letter's recipient/address block, and the dynamic date are removed. The
  public metadata allowlist is title, author, program, and term. The substantive
  letter, acknowledgments, contributions and summary remain intact.
- The student work is **not public domain**. No license or broader reuse
  permission is asserted for the report or figures. The template supplies an
  author header, not a verified license. An absent confidentiality flag is not
  evidence of publication or redistribution permission. This technical edition
  is not a rights-clearance determination.
- Claims about simulation validation and scientific findings remain attributed
  to the historical report. Typographical, physical, and numerical claims have
  not been silently corrected or newly certified.

## Backend API

The implementation is in [site_content/work_report.py](../../site_content/work_report.py).

- `assemble_public_report(root: Path) -> tuple[str, dict]` reads the inspected
  originals and returns the public source and manifest **without writing**.
- `generate_public_report(root: Path) -> Path` explicitly writes the public
  source and manifest. Equal content is not rewritten, including file mtimes.
- `prepare_report(root: Path) -> Path` verifies the existing public source,
  manifest and original-input fingerprints. It raises for missing/stale output;
  it never regenerates anything.
- `report_result(root: Path, assets: Path, asset_url: str) -> dict` calls the
  existing converter on the public article only, with both `image_dir` and
  `source_root` set to the original report directory. It returns the usual
  `body`, `toc`, `headings`, `equation_count`, `image_count`, `warnings`, and
  `source_name`, plus `report_manifest` and `reader_repairs`.

Explicit regeneration uses `python -B -m site_content.work_report --write` in
the selected interpreter. The same command without `--write` is read-only
validation. `--root` allows isolated fixture roots; normal builds should call
`prepare_report`/`report_result`, not regenerate implicitly.

The parent owns page integration, compilation, browser validation, and archives.
After conversion, the parent may call
`source_zip(prepare_report(root), assets)`. The converter's image manifest maps
each of the seven PNGs to its simple filename at the ZIP root, alongside the
sanitized source. This also supplies the relative paths needed for compilation.
No original source ZIP is created by this backend.

## Source and reader adaptations

The source uses the standard `article` class, AMS math, `graphicx`, `braket`,
`geometry`, `titlesec`, and `hyperref`; it has no class-template, bibliography
database, glossary-index, shell-escape, or network dependency. Tectonic can build
the article from the public bundle with the images beside the source. Its TeX
package cache is a compiler prerequisite, not an additional report input.
PDF compilation and browser MathJax verification are the parent's next steps.

- All nine supplied glossary definitions become a description list. Each
  glossary use is replaced with its original display name.
- All eleven references remain manually written entries in their original
  order and position before the appendices. There is no invented bibliography
  database or dependency on the missing resource named by the old preamble.
- The original table's six-column/unsupported numeric-column specification is
  replaced by four standard columns; every header and data cell is unchanged.
- One hard line break inside inline math is removed; it is layout, not an
  expression change. Bibliographic author asterisk markers use standard text
  superscripts. Labels and LF line endings are the other math-byte exceptions.
- Duplicate original labels are distinct occurrence-qualified namespaced labels,
  not guessed equation identities. Missing/ambiguous reference targets become
  visible historical-reference notes and are recorded in `labelAudit`.
- Appendix headings explicitly say **Appendix A** through **Appendix H** and
  are unnumbered sections in both formats. Supplemental hyperlink anchors make
  appendix references valid independently of Pandoc's numeric section counter.
  A preamble-only wrapper includes starred headings in the PDF contents.
- Fourth-level headings remain fourth-level headings (`paragraph` in the
  article), and the reader retains their nested contents entries.
- The original class's float numbering uses the current main section and a
  global float counter: figures **1-1, 2-2, 2-3, 4-4, 4-5, 4-6, 4-7**, and
  table **4-1**. Standard article definitions reproduce this without the class.
- Actual Pandoc output represents the figures as labelled `Figure` nodes and
  the table as a labelled `Div` around `Table`. Report-only DOM processing
  verifies these anchors and unchanged captions, supplies matching caption
  numbers, and turns their references into links. Only the exact converter
  warnings for successfully resolved float references are consumed, with
  evidence recorded in `reader_repairs`. Unrelated warnings/unsupported TeX
  remain visible; arbitrary raw labels or scientific content are never dropped.
- Equation references still use the converter's normal MathJax label mechanism.
  The parent must initialize equation numbering afresh for this article.

## Audit and tests

The manifest contains complete-input hashes (not individual private-field
hashes), the public-output hash, byte hashes of the seven figures, glossary
definitions, label mappings, appendix anchors, float captions/numbers, measured
counts, and documented editorial/layout changes. It contains no removed values,
machine paths, build timestamps, or guessed completion date.

The source inventory is 1132 lines, 94 numbered equation environments and two
unnumbered multline displays (96 display blocks), 179 inline math blocks, seven
figures, one table, nine glossary definitions, eight appendices, and eleven
written references. The duplicate labels are `eq:10` (two), `eq:29` (three),
`eq:61` (two), and `eq:66` (two). The missing `eq:59` reference stays explicitly
marked rather than being assigned an inferred target.

Focused tests are in [site_content/tests/test_work_report.py](../../site_content/tests/test_work_report.py).
Run them with `python -B -m unittest site_content.tests.test_work_report -v`.
They derive private checks from the original metadata in ephemeral memory and
do not log or hardcode those values. Mutation fixtures and reader/ZIP outputs
are temporary. Preservation tests compare full scientific content and ordered
math payloads, not a handful of selected paragraphs or inaccurate prior counts.