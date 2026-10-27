# Academic Paper to PPT — v0.1.0

A local Codex Agent Skill for full-paper reading, source-bound evidence, academic storytelling, editable PowerPoint and actual Windows PowerPoint rendering. The first portable package derives from the internally validated V2.2 engine; it does not reset its capability level.

Official repository: [hee902/academic-paper-to-ppt](https://github.com/hee902/academic-paper-to-ppt). Get the first stable portable package from the [v0.1.0 Release](https://github.com/hee902/academic-paper-to-ppt/releases/tag/v0.1.0). Published public assets require no GitHub login. Download the Skill ZIP and SHA256SUMS.txt together; GitHub's automatic source archive has a different checksum. A stable package label does not expand the tested scientific or platform scope.

Defaults: Chinese, approximately 17 minutes/14 slides, 16:9, Modern Scientific Editorial. The agent reviews the complete paper and actual slide images; scripts enforce provenance and file/number/render gates. No standalone LLM API, paid image service or paper upload is configured.

Tested target: Windows 11 x64, Python3.12, Node24, desktop PowerPoint16.0 and local Codex Skills. Install these prerequisites yourself. Other platforms/Office versions and LibreOffice are unvalidated. Without PowerPoint, final PDF/PNG acceptance is blocked.

Download the repository or release ZIP, verify SHA-256, extract, and run `py -3.12 scripts/install_skill.py --project <work-project>`. In the installed Skill, run `py -3.12 scripts/setup.py --check`; after reviewing the installer, explicitly use `--install --allow-downloads` to create a local isolated runtime. No global pip/npm/PATH changes. Existing Skills are never overwritten. See [INSTALLATION.md](INSTALLATION.md).

In Codex: `$academic-paper-to-ppt Read the uploaded full paper and produce a source-verified academic presentation with editable PPTX, actual PowerPoint PDF/PNG, speaker notes and evidence/visual review reports.`

Give `$skill-installer` explicit arguments `--repo hee902/academic-paper-to-ppt --ref v0.1.0 --path . --name academic-paper-to-ppt --dest "<project>/.agents/skills" --method download`. The root is the Skill; omitting `--name` produces the invalid name `.`. Public download does not require creating a token. Use the published Release ZIP if network or request limits prevent the installer download. Existing authorized credentials are optional for authenticated limits or a separate private repository; never embed them in commands, source or remote URLs. Offline tests do not prove live public download; dated validation records distinguish these tests.

The default Docling native parser reads text-layer PDFs; it is not OCR or reliable complex-table reconstruction. Optional external OCR remains unvalidated in this package. macOS/Linux and fully automatic scientific verification are not claimed.

Text/shapes and suitable simple charts are editable. Original complex figures remain images; shape-based interval summaries are not linked Excel charts. Native OMML is unavailable. Statistical definitions, comparison directions and uncertainty must remain faithful to the source.

Two complete internal papers validated survey/regression/valuation and spatial species-distribution/scenario workflows. This does not validate all disciplines, SEM, meta-analysis or qualitative research. Portable-package tests are separately documented in [release-validation-report.md](release-validation-report.md); synthetic tests are not scientific validation. Timed rehearsal, venue projection and cross-machine fonts still need checking.

Own code: MIT. Vendored MIT components retain their licenses; dependencies and paper content have separate rights. No private paper/data/deck/notes, virtual environments, node_modules or credentials are shipped. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Maintainers follow [PUBLISHING.md](PUBLISHING.md); later versions or repository permission changes need separate owner authorization.
