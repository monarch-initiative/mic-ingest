# CLAUDE.md

This file provides guidance to Claude Code when working with the MIC-Ingest knowledge base.

## Project Overview

This is the **Micronutrient Information Center (MIC) Knowledge Base** - a LinkML-based knowledge base
extracting nutrient information from the Linus Pauling Institute's MIC website (lpi.oregonstate.edu/mic).

The project follows the **dismech pattern**:
1. A LinkML schema defining the data model (`src/mic_ingest/schema/mic.yaml`)
2. A knowledge base of nutrient YAML files (`kb/nutrients/**/*.yaml`)
3. HTML rendering for browsable nutrient pages
4. KGX/Biolink export for knowledge graph integration

## Skills

Claude Code skills are available in `.claude/skills/`:

- **mic-nutrient-creation**: Primary workflow for extracting nutrients from MIC pages. Use when creating or enhancing nutrient YAML files.
- **mic-section-extraction**: Extract and process MIC HTML pages in logical sections to avoid context overflow. Use for section-by-section curation of large HTML files.
- **mic-terms**: Ontology term lookups (CHEBI, FOODON, HP, GO, MONDO, UBERON, HGNC). Use when adding term annotations.
- **mic-references**: Evidence validation, ensuring snippets match PubMed abstracts. Critical for anti-hallucination.
- **mic-compliance**: Completeness analysis and priority scoring. Use to identify gaps.

## Key Commands

```bash
# Install dependencies
just install

# Validate a single nutrient file
just validate kb/nutrients/vitamins/biotin.yaml

# Validate all files
just validate-all

# Validate ontology terms (anti-hallucination check)
just validate-terms

# Validate reference snippets against PubMed abstracts
just validate-references kb/nutrients/vitamins/biotin.yaml

# Run full QC (schema + terms + references)
just qc

# Check compliance/completeness
just compliance kb/nutrients/vitamins/biotin.yaml

# Generate compliance dashboard
just gen-dashboard

# Fetch a PubMed reference
just fetch-reference PMID:12345678

# OAK term lookup
just oak-lookup chebi biotin
just oak-search hp dermatitis

# Section extraction (for large HTML files)
just list-sections cache/mic-pages/vitamin-C.html
just sections-summary cache/mic-pages/vitamin-C.html
just extract-section cache/mic-pages/vitamin-C.html deficiency
just extract-sections cache/mic-pages/vitamin-C.html  # All sections to cache

# List available commands
just --list
```

## Architecture

### Schema (`src/mic_ingest/schema/mic.yaml`)
- LinkML schema defining Nutrient, Function, Deficiency, DiseaseAssociation, etc.
- Uses ontology term bindings (CHEBI, HP, GO, MONDO, FOODON, HGNC, UBERON)
- Descriptor classes with `preferred_term` + optional `term` binding
- Evidence items require PMID references with exact snippets

### Knowledge Base (`kb/nutrients/`)
- One YAML file per nutrient
- Organized by category: `vitamins/`, `minerals/`, `dietary-factors/`, `food-beverages/`
- Each file validates against the `Nutrient` class in the schema
- Evidence items require real PMID references

### Configuration
- `conf/oak_config.yaml`: Ontology adapter mappings
- `conf/qc_config.yaml`: Field weights and compliance thresholds

### Validation Stack
- **linkml-validate**: Schema conformance checking
- **linkml-term-validator**: Validates ontology terms against authoritative sources
- **linkml-reference-validator**: Validates that snippets appear in cited references

## Important Patterns

### Evidence Items
All evidence must have PMID references with exact quotes:
```yaml
evidence:
  - reference: PMID:12345678
    supports: SUPPORT  # SUPPORT, REFUTE, PARTIAL, NO_EVIDENCE, WRONG_STATEMENT
    snippet: "Exact quoted text from the abstract"
    explanation: "Why this evidence supports/refutes the claim"
```

### Ontology Term Structure
```yaml
# For nutrients:
nutrient_term:
  preferred_term: biotin
  term:
    id: CHEBI:15956
    label: biotin

# For phenotypes:
phenotype_term:
  preferred_term: Dermatitis
  term:
    id: HP:0000964
    label: Eczema
```

### OAK Lookups
Use OAK to find and verify ontology terms:
```bash
# Exact match
uv run runoak -i sqlite:obo:chebi info "biotin"

# Fuzzy search
uv run runoak -i sqlite:obo:hp info "l~dermatitis"

# Full details
uv run runoak -i sqlite:obo:chebi info CHEBI:15956 -O obo
```

## Standard Operating Procedure: Adding Evidence

When adding evidence items, follow this SOP to prevent hallucinations:

### 1. Never Fabricate Snippets
Evidence snippets MUST be exact quotes from the cited paper's abstract.

**Wrong:**
```yaml
evidence:
  - reference: PMID:12345678
    snippet: The study showed that biotin is important.  # Paraphrase
```

**Correct:**
```yaml
evidence:
  - reference: PMID:12345678
    snippet: "Biotin serves as a covalently bound coenzyme..."  # Exact quote
```

### 2. Verify PMIDs
Always check that a PMID exists and is relevant:
```bash
just fetch-reference PMID:12345678
cat cache/references/pmid_12345678.md
```

### 3. Validation Workflow
Before committing changes:
```bash
just validate kb/nutrients/vitamins/biotin.yaml
just validate-terms-file kb/nutrients/vitamins/biotin.yaml
just validate-references kb/nutrients/vitamins/biotin.yaml
```

### 4. When Evidence Cannot Be Verified
- **Option A**: Move claim to `notes` field (no evidence required)
- **Option B**: Find a different paper with quotable abstract
- **Option C**: Remove evidence block, keep description

**Do NOT** fabricate quotes or use incorrect PMIDs.

## MIC Website as Source

The MIC website (lpi.oregonstate.edu/mic) is the authoritative source. When extracting:

1. **Fetch the MIC page**: `just fetch-mic-page vitamins/biotin`
2. **Extract numbered references**: Map MIC reference numbers to PMIDs
3. **Quote from PubMed abstracts**: Not from MIC prose
4. **Validate against PubMed**: Snippets must appear in abstracts

## Pre-Edit Validation Hook

A hook in `.claude/hooks/validate_nutrient_hook.py` validates nutrient YAML files
BEFORE edits are applied. If validation fails, the edit is blocked.

## File Naming Convention

Use lowercase with hyphens:
- "Vitamin B12" → `vitamin-b12.yaml`
- "Alpha-Lipoic Acid" → `alpha-lipoic-acid.yaml`

## Integration with Dismech

This project follows patterns from [dismech](../dismech/):
- Same skill structure
- Same evidence requirements
- Same validation stack
- Compatible schema patterns

## Anti-Hallucination Checklist

Before finalizing a nutrient file:
- [ ] All PMIDs are real and from MIC references
- [ ] All snippets are exact quotes from PubMed abstracts
- [ ] CHEBI term exists and label matches
- [ ] HP terms exist and labels match
- [ ] GO terms exist and labels match
- [ ] MONDO terms exist and labels match
- [ ] `just validate` passes
- [ ] `just validate-terms-file` passes
- [ ] `just validate-references` passes
