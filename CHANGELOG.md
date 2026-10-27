# Changelog

## 0.1.0 — portable release candidate

- Private preparation authorization (2026-10-27): document the intended hee902 repository, authenticated private-install options, and the mandatory stop before making the repository public or publishing a Release. Runtime code, platform scope and scientific gates are unchanged.

- Extract the existing V2.2 A–F engine without altering the frozen internal baseline.
- Bundle self-owned runtime code/configuration and selected MIT design/science resources with notices.
- Resolve resources relative to the Skill; place output in a configurable workspace and dependencies in an isolated runtime.
- Add explicit local installation, hash-pinned Python/npm dependencies, environment checks and safe manifest-based Skill copying.
- Keep provenance, scientific semantics, source images, editable-object inspection and actual PowerPoint/paired-image review gates.
- Exclude prior papers, data, production decks/notes, local credentials/audits, caches and restricted third-party components.
- Validate fresh ZIP installation separately from historical internal acceptance; see release-validation-report.md for actual scope and limits.
- Final publication review: explicitly document root installation with --path . and --name academic-paper-to-ppt; test the official installer's root/validate/copy logic offline, including missing-name and overwrite rejection.
- Complete a fresh 12-slide, Chinese production run of a CC BY software paper with actual PowerPoint PDF/PNG, all paired-image reviews, and text/shape edit-save-reopen checks. Timing is a 16m30s plan, not a measured rehearsal.

Version0.1.0 labels the first portable package, not a downgrade of the V2.2 engine. No public repository or Release was created during local packaging.
