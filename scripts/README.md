# Scripts Workspace

This workspace contains repository automation. Right now the most important script is `qa.sh`, which is the shared quality gate for the whole project.

## Current Scripts

- `qa.sh`: repository-wide formatting, linting, type checking, and test validation

## `qa.sh` Modes

From the repository root:

```bash
./scripts/qa.sh
```

Default mode is local fix mode. It applies safe autofixes where configured, then runs the full validation suite.

For CI parity:

```bash
./scripts/qa.sh --check
```

That mode does not modify files and matches the quality-gates GitHub Actions workflow more closely.

## Why This Workspace Matters

As the project grows, `scripts/` is where you should expect to find repeatable developer workflows, setup helpers, release tooling, and other automation that should not live in application code.

If a command needs to be run often and in a consistent way, consider whether it belongs here.