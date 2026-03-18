# Contributing

Thanks for your interest. This is a portfolio repository — external contributions are welcome via PR, but the cadence is set by the maintainer.

## Development setup

```bash
git clone https://github.com/ArashM0z/transit-lakehouse-azure.git
cd transit-lakehouse-azure

# 1. install uv (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. install dev dependencies into a managed venv
uv sync --extra dev

# 3. install the pre-commit hooks
uv run pre-commit install --install-hooks
uv run pre-commit install --hook-type commit-msg

# 4. bring up the local stack
make up
```

## Branch and commit policy

- Work on a feature branch off `main`; never push to `main` directly.
- Use [Conventional Commits](https://www.conventionalcommits.org/) for every commit. The commit-msg hook enforces this.
- Sign commits with `git commit -s` (DCO sign-off required).
- Squash on merge; the PR title becomes the merge commit subject.

### Commit type cheat sheet

| Type | Use when |
|------|----------|
| `feat` | A new capability for users or downstream consumers |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `chore` | Build, tooling, repo hygiene |
| `refactor` | Behaviour-preserving code change |
| `perf` | Performance improvement |
| `test` | Tests added or improved |
| `ci` | CI configuration changes |
| `build` | Build system or dependency changes |

## Pull-request checklist

- [ ] Branch rebased onto latest `main`.
- [ ] `make lint test` passes locally.
- [ ] `terraform fmt -recursive` is a no-op.
- [ ] If schema or data contracts changed: `docs/data_contracts/` updated.
- [ ] If user-facing behaviour changed: `CHANGELOG.md` updated.
- [ ] If a new public API surface: docstring + `docs/` updated.

## Architectural decisions

Substantive design decisions are captured in [docs/adr/](docs/adr/) using the ADR template. Open a PR adding `0NNN-short-title.md` for any new decision.
