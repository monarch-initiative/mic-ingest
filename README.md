# Micronutrient Information Center (MIC) Ingest

The [Micronutrient Information Center](https://lpi.oregonstate.edu/mic) (MIC) is a
resource of the [Linus Pauling Institute](https://lpi.oregonstate.edu/) at Oregon
State University that provides expert, referenced summaries of the health effects,
food sources, deficiency states, and disease associations of vitamins, minerals, and
other dietary factors.

Unlike most Monarch ingests, MIC is not distributed as a downloadable flat file.
The source of truth is the MIC website itself — prose articles with numbered
reference lists. This repository therefore has two layers:

1. **An agentic, schema-driven knowledge base** in `kb/nutrients/**/*.yaml`,
   produced by Claude Code using project skills that read MIC pages, resolve
   references to PubMed, ground entities to ontology terms, and attach verbatim
   evidence snippets.
2. **A Koza transform** in `src/mic_ingest/export/kgx_export.py` that converts the
   validated YAML knowledge base into [KGX](https://github.com/biolink/kgx)
   nodes and edges for the Monarch Knowledge Graph.

- [MIC website](https://lpi.oregonstate.edu/mic)
- [Schema](src/mic_ingest/schema/mic.yaml) (LinkML)
- [Documentation](https://monarch-initiative.github.io/mic-ingest)

## Data Source

Data originates from the MIC website:

- Base URL: `https://lpi.oregonstate.edu/mic`
- Organized by category: vitamins, minerals, dietary factors, food/beverages
- Each article contains an in-page numbered reference list linking to PubMed

Because the source is free-text HTML rather than a structured release, we rely on
an agentic extraction pipeline to produce structured YAML records that can then be
validated and transformed by conventional tooling.

## Agentic Extraction Pipeline

The `kb/nutrients/` knowledge base is produced by Claude Code using a set of
project skills defined in `.claude/skills/`. The goal is to produce records that
are schema-valid, ontology-grounded, and anti-hallucination checked against the
original PubMed abstracts.

### Skills

| Skill | Purpose |
| --- | --- |
| `mic-nutrient-creation` | Primary workflow for creating a new nutrient YAML from an MIC page. |
| `mic-section-extraction` | Slice long MIC HTML pages into logical sections (function, deficiency, disease, etc.) to fit in context. |
| `mic-terms` | Look up and bind ontology terms using OAK (CHEBI, HP, GO, MONDO, FOODON, HGNC, UBERON). |
| `mic-references` | Validate that every evidence snippet is a verbatim quote from the cited PubMed abstract. |
| `mic-compliance` | Weighted completeness scoring to surface gaps in existing files. |

### Workflow

For a given nutrient (e.g. `vitamins/biotin`):

1. **Fetch** the MIC page into `cache/mic-pages/` using
   `just fetch-mic-page vitamins/biotin`.
2. **Section** the HTML into manageable chunks with
   `just extract-sections cache/mic-pages/biotin.html` so each section can be
   processed without overflowing the model context.
3. **Extract references**: build the mapping between MIC reference numbers and
   PubMed IDs (`just extract-refs`, `just fetch-all-abstracts`). Abstracts are
   cached under `cache/references/`.
4. **Draft the YAML** conforming to the `Nutrient` class in
   `src/mic_ingest/schema/mic.yaml`. The schema models:
   - `nutrient_term` with a CHEBI binding
   - `functions`, each with biological processes, genes, cellular components,
     and anatomical locations
   - `deficiency` and `toxicity` modeled as two-hop causal phenotype chains
     (state phenotype → sequelae, with optional frequency and disease context)
   - `disease_associations` classified as `THERAPEUTIC`, `PROTECTIVE`,
     `RISK_FACTOR`, or `MARKER`
   - `food_sources`, `nutrient_interactions`, `drug_interactions`
5. **Ground terms** to ontologies via `mic-terms` / OAK; each descriptor carries
   both a `preferred_term` string and a validated `term: {id, label}` binding.
6. **Attach evidence** to every claim as one or more items containing a
   `reference` (PMID), a `supports` status
   (`SUPPORT` / `REFUTE` / `PARTIAL` / `NO_EVIDENCE` / `WRONG_STATEMENT`), a
   verbatim `snippet` from the PubMed abstract, and an `explanation`.
7. **Validate** the file end-to-end:

   ```bash
   just validate kb/nutrients/vitamins/biotin.yaml           # LinkML schema
   just validate-terms-file kb/nutrients/vitamins/biotin.yaml # ontology terms exist
   just validate-references kb/nutrients/vitamins/biotin.yaml # snippet ⊂ abstract
   ```

   `just qc` runs all three across the full KB.

A pre-edit hook (`.claude/hooks/validate_nutrient_hook.py`) blocks edits to
nutrient YAML files that would leave the file invalid, keeping the KB green as
curation proceeds. Detailed instructions for curators are in [CLAUDE.md](CLAUDE.md)
and [CONTRIBUTING.md](CONTRIBUTING.md).

### Anti-Hallucination Guarantees

Three independent validators guard the KB:

- **Schema validation** (`linkml-validate`) — every file conforms to the
  `Nutrient` class.
- **Term validation** (`linkml-term-validator`) — every ontology ID resolves via
  OAK and matches its declared label.
- **Reference validation** (`linkml-reference-validator`) — every evidence
  `snippet` appears verbatim in the PubMed abstract of its cited PMID.

Evidence that cannot be verified must either cite a different paper, be moved
to a free-text `notes` field, or be removed. Paraphrased quotes are not allowed.

## Koza Transform

The transform in `src/mic_ingest/export/kgx_export.py` is a standard Koza
transform over the YAML records in `kb/nutrients/`. It emits Biolink-compliant
nodes and edges in KGX format.

- Knowledge source: `infores:mic`
- Knowledge level: `knowledge_assertion`
- Agent type: `manual_validation_of_automated_agent`
- Every edge carries `publications` (PMIDs) and `supporting_text` assembled from
  the evidence blocks; edges without at least one evidence item are dropped.

### Nodes

Nodes are emitted for every unique CURIE referenced in a nutrient record:

- `biolink:ChemicalEntity` — the nutrient itself (CHEBI) and interacting
  nutrients/drugs
- `biolink:Disease` — disease associations and, where present, the disease
  context of a deficiency state (MONDO)
- `biolink:PhenotypicFeature` — deficiency and toxicity state phenotypes and
  their sequelae (HP)
- `biolink:BiologicalProcess` — processes a nutrient participates in (GO)
- `biolink:Gene` — genes affected by a nutrient (HGNC)
- `biolink:CellularComponent` — cellular components the nutrient acts within (GO)
- `biolink:AnatomicalEntity` — anatomical locations of nutrient activity (UBERON)
- `biolink:Food` — food sources of the nutrient (FOODON)

Every node is tagged with `provided_by: ["infores:mic"]`.

### Edges

**Disease associations** — dispatched by `relationship_type`:

| Relationship | Biolink class | Predicate |
| --- | --- | --- |
| `THERAPEUTIC` | `ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation` | `biolink:treats_or_applied_or_studied_to_treat` |
| `PROTECTIVE` | `ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation` | `biolink:preventative_for_condition` |
| `RISK_FACTOR` | `Association` | `biolink:affects_likelihood_of` |
| `MARKER` | `Association` | `biolink:biomarker_for` |

`PROTECTIVE` and `RISK_FACTOR` edges carry a `direction:increased` or
`direction:decreased` qualifier when the source asserts a direction.

**Deficiency and toxicity** — modeled as a two-hop causal phenotype chain:

1. `Nutrient → deficiency/toxicity state phenotype` via
   `ChemicalAffectsBiologicalEntityAssociation` with
   `predicate: biolink:affects`, `qualified_predicate: biolink:causes`,
   `subject_aspect_qualifier: abundance`, and
   `subject_direction_qualifier: decreased` (deficiency) or `increased`
   (toxicity).
2. `state phenotype → sequela phenotype` via
   `PhenotypicFeatureToPhenotypicFeatureAssociation` with
   `predicate: biolink:causes`. When available, a `frequency_qualifier` (HP
   frequency class) and a `disease_context_qualifier` (MONDO term) are attached.

**Function sub-entities** — children of a `functions[]` entry inherit the
parent's evidence (flagged `[INDIRECT EVIDENCE]` in `supporting_text`):

| Target | Biolink class | Predicate |
| --- | --- | --- |
| BiologicalProcess | `Association` | `biolink:participates_in` |
| Gene | `Association` | `biolink:affects` |
| CellularComponent | `Association` | `biolink:has_participant` |
| AnatomicalEntity | `Association` | `biolink:active_in` |

**Food sources, nutrient and drug interactions:**

| Edge | Subject → Object | Predicate |
| --- | --- | --- |
| Food source | `Food → ChemicalEntity` | `biolink:has_nutrient` |
| Nutrient interaction | `ChemicalEntity → ChemicalEntity` | `biolink:interacts_with` |
| Drug interaction | `ChemicalEntity → ChemicalEntity` | `biolink:interacts_with` |

### Frequency Mapping

The deficiency/toxicity frequency enum in the YAML maps to HP frequency terms
on the emitted edges:

| Enum | HP term |
| --- | --- |
| `OBLIGATE` | HP:0040280 |
| `VERY_FREQUENT` | HP:0040281 |
| `FREQUENT` | HP:0040282 |
| `OCCASIONAL` | HP:0040283 |
| `VERY_RARE` | HP:0040284 |

## Installation

```bash
cd mic-ingest
just install          # uv sync
# or
poetry install
```

## Usage

Common tasks are exposed through `just`. Run `just --list` to see everything.

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

## Requirements

- Python >= 3.10
- [uv](https://github.com/astral-sh/uv) or [Poetry](https://python-poetry.org/)
- [just](https://github.com/casey/just)
- [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) — only
  required for running the agentic extraction skills to add or enhance nutrient
  records. Consumers of the exported KGX do not need it.

## Repository Layout

```
kb/nutrients/              # Curated YAML knowledge base (one file per nutrient)
src/mic_ingest/schema/     # LinkML schema (mic.yaml)
src/mic_ingest/export/     # Koza transform → KGX nodes/edges
src/mic_ingest/cli.py      # Typer CLI (download, transform)
.claude/skills/            # Agentic extraction skills
.claude/hooks/             # Pre-edit validation hook
scripts/                   # MIC page / reference utility scripts
cache/                     # Cached MIC HTML and PubMed abstracts
conf/                      # OAK and QC configuration
justfile                   # All user-facing tasks
```

## GitHub Actions

Workflows live in `.github/workflows`:

- `test.yaml` — run the pytest suite
- `create-release.yaml` — weekly or manual release
- `deploy-docs.yaml` — deploy docs to GitHub Pages on push to `main`
- `update-docs.yaml` — refresh node/edge reports after a release

## Citation

Linus Pauling Institute, Oregon State University. Micronutrient Information
Center. https://lpi.oregonstate.edu/mic

## License

BSD-3-Clause

---

> This project was generated using [monarch-initiative/cookiecutter-monarch-ingest](https://github.com/monarch-initiative/cookiecutter-monarch-ingest).
> Keep it up to date with:
>
> ```bash
> cruft update
> ```
