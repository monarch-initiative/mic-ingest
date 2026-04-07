---
description: Run validation on nutrient files. Validates schema, terms, and references.
argument-hint: [FILE_PATH or 'all']
---

Run validation on the specified nutrient file(s).

## Arguments

- **FILE_PATH**: Path to a specific nutrient YAML file, or 'all' for all files

## What Gets Validated

1. **Schema Validation**: Structure matches LinkML schema
2. **Term Validation**: Ontology IDs exist and labels match
3. **Reference Validation**: Snippets appear in PubMed abstracts

## Commands

```bash
# Validate a single file (all checks)
just validate kb/nutrients/vitamins/biotin.yaml

# Validate all files
just validate-all

# Full QC (validation + compliance)
just qc
```

## Example Usage

```
/validate kb/nutrients/vitamins/biotin.yaml
/validate all
```
