---
name: hermes-project-discovery
description: Discover and classify software projects, nested repositories, containers, collections, technologies, and basic health without reading secrets or changing files.
---

# Project Discovery

Build an evidence-based workspace map before deeper analysis.

- Treat a folder as a project only when manifests, source conventions, Git metadata, or framework markers support that conclusion.
- Search for nested projects while pruning dependencies, builds, caches and generated output.
- Classify other folders as containers, collections, empty or unreadable; do not assign project health scores to them.
- Detect secret files only by name. Never open `.env`, credentials, private keys or token stores.
- Record absolute path, relative path, technologies, Git presence, documentation, tests and CI evidence.
- Report access failures and uncertainty explicitly.
