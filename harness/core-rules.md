# Hermes AI-DLC Core Rules

Hermes is a deterministic harness around an AI model. The engine controls routing, permissions, state and gates; the model performs bounded reasoning inside the selected stage.

## Invariants

1. Separate observed evidence, inference, risk and recommendation.
2. Never claim that a file, test, dependency or behavior exists without evidence.
3. Never read or reproduce secrets. Environment files may be detected by name, not opened.
4. Analysis writes only to the Hermes state directory, never to the analyzed project.
5. Construction, command execution, network operations and deployment require an explicit gate scoped to one project and one plan.
6. A failed sensor or tool call is reported; it is never silently converted into success.
7. Every stage records its input, output, status, model and timestamp in the audit log.
8. Keep a single source of truth: stages decide what happens; skills decide how domain work is performed.

## Lifecycle

Hermes follows the five AI-DLC 2.0 phases: Initialization, Ideation, Inception, Construction and Operation. Scope selection runs only the stages that add value. Phase transitions verify required artifacts and traceability before proceeding.

The initial local profile is analysis-only. It may execute deterministic discovery and AI-assisted review stages, but it cannot alter software projects.

Based on AWS Labs AI-DLC Workflows: https://github.com/awslabs/aidlc-workflows
