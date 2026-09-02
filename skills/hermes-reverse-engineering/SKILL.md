---
name: hermes-reverse-engineering
description: Analyze an existing codebase to explain its architecture, runtime, entry points, data flow, integrations, conventions, risks, and undocumented behavior with file evidence.
---

# Reverse Engineering

Create a trustworthy brownfield system map.

1. Inspect manifests, entry points, configuration, source layout, tests, deployment files and recent Git state.
2. Trace representative flows from boundary to persistence or external integration.
3. Identify modules, responsibilities, coupling, generated code and operational dependencies.
4. Cite relative file paths for factual claims. Label architectural inference as inference.
5. Do not open secrets, dependency trees or large generated artifacts.
6. Report unknowns, inconsistent evidence and areas that require runtime verification.

Prefer a compact system overview, component map, data/integration map, risks and prioritized follow-up questions.
