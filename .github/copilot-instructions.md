# Copilot Instructions for mdcl-menlo-middleware

## Project Overview

- This repository is a Python FastAPI service that implements the Menlo Security middleware integration.
- The main application entrypoint is `python3 -m metadefender_menlo`.
- Core application code lives under `metadefender_menlo/`.
- HTTP request handling is organized under `metadefender_menlo/api/handlers/`.
- Tests are split into `tests/unit/` and `tests/integration/`.

## Development Environment

- Use the existing virtual environment when available: `.venv`.
- Install development dependencies with `pip install -r requirements-dev.txt`.
- Prefer Python 3 and keep compatibility with the versions implied by the existing repo and dependencies.

## Coding Expectations

- Preserve the existing package layout and naming patterns inside `metadefender_menlo`.
- Prefer small, localized changes instead of broad refactors.
- Follow the established style in nearby files; do not reformat unrelated code.
- Keep public behavior and API contracts stable unless the task explicitly requires a change.
- Reuse existing helpers, models, response classes, and handler patterns before adding new abstractions.
- Keep configuration-driven behavior inside the existing config flow rather than hardcoding values.
- Maintain current logging patterns and avoid introducing noisy or duplicate logs.
- Keep async request paths non-blocking where possible and be careful not to break FastAPI lifecycle behavior.

## Handlers and API Changes

- When changing request handlers, inspect the corresponding base handler, response models, and related tests first.
- Keep request and response semantics aligned with the Menlo API expectations and the OpenAPI artifacts in `api/` when relevant.
- Prefer extending existing handler or response classes over duplicating similar logic.
- Preserve request context, request IDs, and existing logging/auditing flows.

## Tests and Validation

- Add or update the narrowest relevant tests in `tests/unit/` or `tests/integration/` for behavior changes.
- Prefer targeted pytest runs first, then broader runs only if needed.
- Typical commands:
  - `pytest tests/unit`
  - `pytest tests/integration`
  - `pytest <path-to-test-file>`

## Config, Security, and Operations

- Treat `config.yml`, certificate paths, API keys, and service endpoints as environment- or config-managed values.
- Do not hardcode secrets, tokens, or internal endpoints.
- Preserve Docker, Kubernetes, and CI files unless the task explicitly requires touching deployment behavior.
- Avoid changes that would silently alter logging, Sentry, SNS, Kafka, or external API integration behavior without tests.

## Preferred Workflow for Copilot

- Start from the specific handler, model, config object, or test closest to the requested change.
- Validate with the smallest relevant pytest command after edits.
- If behavior is unclear, inspect README, existing tests, and neighboring implementations before introducing new patterns.

## Agent PR requirements (AI-driven)

When opening pull requests as an agent:

- Include **#AIDriven** and **#AIGenerated** in the pull request description.
- Ensure the pull request has the **ai-driven** label (add it if it is missing).

## Commit Message Rules (AI-driven)

When generating commit messages as an agent:

- Include `#AIGenerated` in every AI-generated commit message.
