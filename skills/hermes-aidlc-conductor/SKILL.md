---
name: hermes-aidlc-conductor
description: Orchestrate evidence-based software analysis through an AI-DLC-inspired lifecycle, selecting the smallest useful scope, delegating stages to Hermes skills, enforcing read-only boundaries and human approval gates, and maintaining auditable traceability.
version: 0.1.0
author: Hermes Local
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: autonomous-ai-agents
    tags: [aidlc, orchestration, software-analysis, governance]
    related_skills:
      - hermes-project-discovery
      - hermes-reverse-engineering
      - hermes-architecture
      - hermes-quality
      - hermes-security
      - hermes-delivery
      - hermes-operations
---

# Hermes AI-DLC Conductor

Use this skill when the user asks to analyze, organize, assess, plan, improve, or govern a software project.

## Route the work

1. Read `harness/core-rules.md`, `harness/scopes.json`, and `harness/aidlc-stage-catalog.json` from the rules-pack repository.
2. Discover the exact target. A directory with nested repositories may be a container; analyze each real project separately.
3. Select the smallest sufficient scope:
   - `quick`: discovery, reverse engineering, architecture, and quality overview.
   - `analysis`: quick plus practices, security/NFR, and operational readiness.
   - `full`: only after explicit approval for every construction or operation gate.
4. Load only the specialized skills required for the selected stages.
5. Gather evidence with read-only tools. Never inspect secret contents.
6. Record each finding as observation, inference, risk, or recommendation and cite its source path.
7. Save artifacts and audit state under the rules pack's `.hermes/harness/` directory, never inside the analyzed project.
8. Present the result and request approval before any write, command execution, dependency installation, Git mutation, network operation, or deployment.

## Non-negotiable gates

Analysis permission does not imply modification permission. Construction and operation remain disabled until the user approves a concrete plan naming the target project, intended files or commands, expected effect, and rollback approach.

Never silently skip a failed sensor, unreadable path, missing artifact, or uncertain conclusion.
