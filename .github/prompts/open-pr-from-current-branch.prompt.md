---
agent: agent
description: Open a pull request from the current branch to the base branch with required labels and AI disclosure tags
---

# Open PR From Current Branch

Open a pull request for the current git branch toward the base branch.

## Required behavior

1. Detect the current branch and ensure it is pushed to origin.
2. Detect the base branch from repository defaults (prefer default branch from remote), unless I explicitly provide another base branch.
3. Summarize the commit range and changed files to build a clear PR title and description.
4. Create the PR using GitHub Copilot MCP pull request tools (do not use manual browser steps).
5. Add the `ai-driven` label.
6. Include both `#AIDriven` and `#AIGenerated` in the PR description body.
7. Return the PR URL and a short summary of title, base branch, and head branch.

## PR content format

- Title: concise, imperative, and scoped.
- Description sections:
  - Summary
  - What changed
  - Validation
  - Risk
  - Tags (`#AIDriven` and `#AIGenerated`)

## Inputs (optional)

- Base branch override
- PR title override
- Extra reviewers
- Extra context for description

If I provide no overrides, infer sensible defaults from git state.
