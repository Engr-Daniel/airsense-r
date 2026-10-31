# Local PDF build and review

The submission manuscript is `main.tex`; the descriptive diagnostic supplement
is `supplement.tex`. Keep `references.bib` and `figures/` with both sources.

Install the portable [Tectonic compiler](https://tectonic-typesetting.github.io/book/latest/installation/),
or place its executable in `.tmp/tectonic/` at the repository root. The tested
Windows compiler is Tectonic 0.17.0. No global TeX installation is required.

From the repository root:

```sh
python paper/build_pdf.py
```

Alternatively pass `--compiler PATH_TO_TECTONIC`. The first build needs internet
access for TeX packages; later builds reuse `.tmp/tectonic-cache/`. The compiler
runs the bibliography and reference passes automatically. PDFs, logs, intermediate
files and a source/output checksum receipt are written to `.tmp/paper-build/`.
They do not clutter the tracked source or alter experiment dependencies.

After manuscript edits, compile both documents, inspect warnings and render the
PDF pages to check figure placement, margins, captions, author details and
bibliography. A source-only check does not replace this rendered review.

In Overleaf, select `main.tex` or `supplement.tex` as the main document. If old
bibliography entries persist, upload the current `references.bib` and recompile
from scratch. Local Tectonic and Overleaf may differ slightly in pagination.

Rendered review on 2026-10-31: main paper eight pages; supplement one page.
No overfull boxes or unresolved references remain. Tectonic reports nonfatal
font substitutions, a float-only page and underfull vertical spacing; visual
inspection found no clipped content. These are recorded in the build receipt.
The Windows Fontconfig startup message did not prevent PDF generation.
