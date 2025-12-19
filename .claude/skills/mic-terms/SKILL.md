---
name: mic-terms
description: >
  Skill for adding and validating ontology term annotations in the MIC knowledge base.
  Covers CHEBI, FOODON, HP, GO, MONDO, UBERON, HGNC lookups. Use when adding term
  bindings to nutrient YAML files.
---

# MIC Ontology Terms Skill

## Overview

Add and validate ontology term references in the MIC nutrient knowledge base. This ensures
nutrients, phenotypes, biological processes, diseases, foods, and genes are properly
linked to authoritative ontology terms with correct IDs and labels.

## When to Use

- Adding `nutrient_term` to nutrient entries (uses CHEBI)
- Adding `phenotype_term` to phenotype entries (uses HP)
- Adding `term` to `biological_processes` entries (uses GO)
- Adding `disease_term` to disease associations (uses MONDO)
- Adding `food_term` to food sources (uses FOODON)
- Adding `term` to `genes` entries (uses HGNC)
- Validating existing ontology term references
- Fixing label mismatches

## Ontology Mappings

| Entity Type | Ontology | OAK Adapter | Prefix |
|-------------|----------|-------------|--------|
| Nutrients | CHEBI | sqlite:obo:chebi | CHEBI: |
| Foods | FOODON | sqlite:obo:foodon | FOODON: |
| Phenotypes | HP | sqlite:obo:hp | HP: |
| Biological Processes | GO | sqlite:obo:go | GO: |
| Cellular Components | GO | sqlite:obo:go | GO: |
| Diseases | MONDO | sqlite:obo:mondo | MONDO: |
| Anatomy | UBERON | sqlite:obo:uberon | UBERON: |
| Genes | HGNC | sqlite:obo:hgnc | HGNC: |

## Term Object Structure

All term references follow this YAML structure:

```yaml
# For nutrients (CHEBI):
nutrient_term:
  preferred_term: biotin
  term:
    id: CHEBI:15956
    label: biotin

# For phenotypes (HP):
phenotype_term:
  preferred_term: Dermatitis
  term:
    id: HP:0000964
    label: Eczema

# For biological processes (GO):
biological_processes:
  - preferred_term: fatty acid biosynthesis
    term:
      id: GO:0006633
      label: fatty acid biosynthetic process

# For diseases (MONDO):
disease_term:
  preferred_term: neural tube defect
  term:
    id: MONDO:0005343
    label: neural tube defect

# For foods (FOODON):
food_term:
  preferred_term: egg yolk
  term:
    id: FOODON:00002669
    label: egg yolk

# For genes (HGNC):
genes:
  - preferred_term: PC
    description: Pyruvate carboxylase
    term:
      id: HGNC:8636
      label: PC
```

## OAK Lookup Commands

### Exact Match
```bash
uv run runoak -i sqlite:obo:chebi info "biotin"
# Returns: CHEBI:15956 ! biotin
```

### Fuzzy/Label Search
```bash
uv run runoak -i sqlite:obo:hp info "l~cognitive impairment"
# Returns multiple matches - select the most appropriate
```

### Starts-With Search
```bash
uv run runoak -i sqlite:obo:hp info "l^skin"
# Returns terms starting with "skin"
```

### Get Full Term Details
```bash
uv run runoak -i sqlite:obo:chebi info CHEBI:15956 -O obo
# Returns complete term information including definition
```

### Search by ID
```bash
uv run runoak -i sqlite:obo:go info GO:0006633
# Returns: GO:0006633 ! fatty acid biosynthetic process
```

### Hierarchical Relationships
```bash
uv run runoak -i sqlite:obo:go relationships --direction both GO:0006633
# Shows parent and child terms
```

## Common Nutrient Terms (CHEBI)

| Nutrient | CHEBI ID | Label |
|----------|----------|-------|
| Biotin | CHEBI:15956 | biotin |
| Folate | CHEBI:27470 | folate |
| Vitamin C | CHEBI:29073 | ascorbic acid |
| Vitamin D | CHEBI:27300 | vitamin D |
| Vitamin E | CHEBI:18145 | vitamin E |
| Vitamin K | CHEBI:28384 | vitamin K |
| Thiamin | CHEBI:18385 | thiamine |
| Riboflavin | CHEBI:17015 | riboflavin |
| Niacin | CHEBI:15940 | nicotinic acid |
| Calcium | CHEBI:22984 | calcium(2+) |
| Iron | CHEBI:24875 | iron(2+) |
| Zinc | CHEBI:27363 | zinc(2+) |
| Magnesium | CHEBI:18420 | magnesium(2+) |
| Selenium | CHEBI:27568 | selenium atom |

## Specificity Guidelines

**Critical**: Always use the most specific term that accurately describes the entity.

| Incorrect (too general) | Correct (specific) |
|------------------------|-------------------|
| HP:0000001 All | HP:0000964 Eczema |
| GO:0008150 biological_process | GO:0006633 fatty acid biosynthetic process |
| CHEBI:24431 chemical entity | CHEBI:15956 biotin |

When a fuzzy search returns multiple results:
1. Review all candidates
2. Check term definitions with `-O obo` flag
3. Select the term that most precisely matches the biological context
4. If no specific term exists, use the closest parent but note the limitation

## Validation

### Validate Term Structure
```bash
just validate kb/nutrients/vitamins/biotin.yaml
```

### Validate Term IDs and Labels
```bash
just validate-terms-file kb/nutrients/vitamins/biotin.yaml
```

This checks:
- Term IDs exist in the ontology
- Labels match the canonical ontology labels exactly
- Required fields are present

### Fixing Label Mismatches

If validation reports a label mismatch:
```
LABEL MISMATCH: biotin.yaml
  Term: HP:0000964
  Expected: Eczema
  Actual: Dermatitis
```

Update the `label` field to match the ontology's canonical label exactly.

## Batch Term Population

To find entries missing term annotations:

```python
import yaml
import glob

for f in glob.glob("kb/nutrients/**/*.yaml", recursive=True):
    with open(f) as file:
        data = yaml.safe_load(file)

    # Check nutrient_term
    nt = data.get('nutrient_term', {})
    if not nt.get('term'):
        print(f"{f}: missing nutrient_term.term")

    # Check phenotypes
    deficiency = data.get('deficiency', {})
    for pheno in deficiency.get('phenotypes', []):
        pt = pheno.get('phenotype_term', {})
        if not pt.get('term'):
            print(f"{f}: {pheno.get('name')} - missing phenotype_term.term")
```

## Common Patterns

### Adding CHEBI to a Nutrient
1. Look up term: `uv run runoak -i sqlite:obo:chebi info "l~<nutrient name>"`
2. Verify: `uv run runoak -i sqlite:obo:chebi info <CHEBI:ID> -O obo`
3. Add to YAML:
   ```yaml
   nutrient_term:
     preferred_term: <Original Name>
     term:
       id: <CHEBI:ID>
       label: <Exact label from OAK>
   ```
4. Validate: `just validate-terms-file kb/nutrients/...`

### Adding HP to a Phenotype
1. Look up term: `uv run runoak -i sqlite:obo:hp info "l~<phenotype>"`
2. Verify specificity
3. Add `phenotype_term:` block
4. Validate

### Adding GO to Biological Processes
1. Look up: `uv run runoak -i sqlite:obo:go info "l~<process>"`
2. Check it's under GO:0008150 (biological_process)
3. Add `term:` block to the process
4. Validate

## Troubleshooting

### "No results found"
- Try broader search terms
- Check spelling
- Try synonyms
- Use fuzzy search: `info "l~<term>"`

### "Multiple results"
- Check definitions with `-O obo`
- Choose the most specific term
- Verify the term is from the correct branch (e.g., biological_process vs molecular_function)

### "Term exists but label doesn't match"
The ontology canonical label must be used. Common issues:
- Case sensitivity: "Biotin" vs "biotin"
- Synonyms: "Vitamin B7" vs "biotin" (CHEBI uses "biotin")
- Outdated labels: Always fetch the current label from OAK
