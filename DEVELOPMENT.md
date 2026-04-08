# Development

Operational notes for working on `mic-ingest`: installing dependencies,
curating nutrient YAML files, running the Koza KGX export, and executing the
test suite.

For an overview of what this repository does, see [README.md](README.md).
For the curation conventions Claude Code follows, see [CLAUDE.md](CLAUDE.md).

## Requirements

- Python >= 3.10
- [uv](https://github.com/astral-sh/uv) or [Poetry](https://python-poetry.org/)
- [just](https://github.com/casey/just)
- [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) — only
  required for running the agentic extraction skills to add or enhance nutrient
  records. Consumers of the exported KGX do not need it.

## Installation

```bash
cd mic-ingest
just install          # uv sync
# or
poetry install
```

## Common Tasks

All tasks are exposed through `just`. Run `just --list` to see everything.

### Knowledge base curation

```bash
just fetch-mic-page vitamins/biotin     # Fetch and cache an MIC page
just extract-sections cache/mic-pages/biotin.html
just validate kb/nutrients/vitamins/biotin.yaml
just validate-terms-file kb/nutrients/vitamins/biotin.yaml
just validate-references kb/nutrients/vitamins/biotin.yaml
just qc                                  # schema + terms + references
just compliance kb/nutrients/vitamins/biotin.yaml
just gen-dashboard                       # HTML compliance dashboard
```

### KGX export

```bash
just export-kgx
# Writes output/kgx/mic_nodes.jsonl and output/kgx/mic_edges.jsonl
```

The legacy Koza CLI wrappers are also available:

```bash
poetry run mic_ingest download   # kghub-downloader (legacy, for CI wiring)
poetry run mic_ingest transform  # Koza transform runner
```

### Testing

```bash
just test     # pytest suite
```

## GitHub Actions

Workflows live in `.github/workflows`:

- `test.yaml` — run the pytest suite
- `create-release.yaml` — weekly or manual release
- `deploy-docs.yaml` — deploy docs to GitHub Pages on push to `main`
- `update-docs.yaml` — refresh node/edge reports after a release

## Cookiecutter / cruft

This project was generated using
[monarch-initiative/cookiecutter-monarch-ingest](https://github.com/monarch-initiative/cookiecutter-monarch-ingest).
Keep it up to date with:

```bash
cruft update
```
