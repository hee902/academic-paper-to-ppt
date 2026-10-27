# Third-party licenses and provenance

The repository LICENSE applies only to original project code/documentation. We reviewed the local pinned upstream license files before selecting MIT for the original release work. No software binary, paper, dataset, scientific figure or font is distributed with this package. Third-party ownership is retained below.

| Included source/text | Upstream/pinned commit | License and included notice |
|---|---|---|
| third_party/baoyu-design: deck-stage.js and selected design instructions | JimLiu/baoyu-design @ 6530033592bf7fa58bc1a5a2a2ad278da45213a9 | MIT, copyright 2026 Jim Liu 宝玉; full LICENSE retained |
| third_party/scientific-critical-thinking: guide/references | K-Dense-AI/scientific-agent-skills @ 593377bb048752abb0152deab9fbb1083a6087df | MIT, copyright 2025 K-Dense Inc.; full LICENSE retained |
| third_party/scientific-slides: selected guide/reference/timing text | Same K-Dense pinned commit | MIT; full LICENSE retained; no paid generator scripts distributed |
| third_party/scientific-visualization: palette_audit.py, _common.py, color_palettes.py | Same K-Dense pinned commit | MIT; full LICENSE and original palette-source comments retained |

Only file layout/resource lookup and CLI orchestration are adapted in original code. Vendored resource content is retained with hashes in the package manifest. Guides are local references, not separately registered Skills and not authority to upload data or use paid services. External images/remote fonts and executable generators are excluded.

Software installed separately by the explicit installer includes Docling-slim (MIT project), PptxGenJS4.0.1 (MIT), Playwright1.61.0 (Apache-2.0), JSZip3.10.1 (MIT or GPL-3.0-or-later option; MIT use), python-pptx (MIT), pypdf (BSD-3-Clause), Pillow (HPND), pypdfium2/PDFium (Apache/BSD notices), pywin32 (PSF-based), psutil (BSD), reportlab (BSD), and their pinned transitive dependencies. Their own installed distribution metadata/license files govern; they are not bundled or made MIT by this repository. The full Python hash lock and npm package-lock identify the actual resolved versions. Chromium and npm distributions retain their upstream licenses in the installed runtime.

Not distributed: MinerU/model weights, Guizang/AGPL assets, academic-pptx (historical root-MIT/frontmatter-Proprietary conflict), JetBrains helper assets, Microsoft Office, system fonts, venvs/node_modules, private papers/data and prior produced decks/notes. Optional tools require separate lawful installation and validation. Do not interpret their absence as a license resolution.

The independent real-paper validation uses Waskom (2021), *seaborn: statistical data visualization*, JOSS6(60):3021, https://doi.org/10.21105/joss.03021 (paper CC BY4.0). Only citation and sanitized test status may appear publicly; the downloaded PDF, source crops and generated test deck remain in private validation storage and are not included in this ZIP.

Original scientific-visualization palette-source links are attribution references, not included copies of those external documents. Public release review does not certify dependency legal compliance in every downstream use; retain notices and verify rights for any newly added material.
