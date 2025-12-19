---
name: mic-compliance
description: >
  Skill for analyzing and improving compliance in the MIC knowledge base.
  Use this when checking nutrient file completeness, identifying missing
  fields (ontology terms, evidence, descriptions), understanding weighted
  priority scoring, and systematically improving knowledge base coverage.
---

# MIC Compliance Analysis Skill

## Overview

Analyze and improve the completeness of nutrient YAML files in the MIC knowledge base.
The compliance system checks for recommended fields (ontology terms, evidence items,
descriptions) and generates scores to identify priority curation targets.

## When to Use

- Running compliance checks on nutrient files
- Identifying missing recommended fields
- Understanding which files need the most curation work
- Improving overall knowledge base quality
- Generating compliance dashboards and reports
- Understanding field priority (weighted scoring)

## Key Commands

### Analyze Single File
```bash
just compliance kb/nutrients/vitamins/biotin.yaml
```

Output includes:
- **Global Compliance**: Percentage of recommended fields populated
- **Weighted Compliance**: Score adjusted by field importance
- **Summary by Slot**: Compliance grouped by field type (term, evidence, description)
- **Detailed Path Scores**: Individual field status (OK/MISSING)

### Analyze All Files
```bash
just compliance-all
```

Multi-file report showing:
- Overall knowledge base compliance
- Per-path compliance across all files
- Quick identification of systematically missing fields

### Weighted Analysis with Thresholds
```bash
just compliance-weighted
```

Uses `conf/qc_config.yaml` to:
- Apply importance weights to different fields
- Flag violations where compliance falls below minimum thresholds
- Prioritize critical fields

### Generate Reports
```bash
# CSV format for spreadsheet analysis
just compliance-csv

# JSON format for programmatic processing
just compliance-report
```

### Generate Visual Dashboard
```bash
just gen-dashboard
```

Creates `dashboard/index.html` with:
- Interactive charts showing compliance distribution
- Priority curation targets (10 lowest-scoring files)
- Field coverage analysis

## Understanding Compliance Scores

### Global vs Weighted Compliance

| Metric | Description |
|--------|-------------|
| Global Compliance | Simple percentage: populated fields / total recommended fields |
| Weighted Compliance | Adjusted by field importance from `conf/qc_config.yaml` |

### Field Weights

| Field | Weight | Min Threshold | Why |
|-------|--------|---------------|-----|
| `nutrient_term.term` | 5.0 | 95% | Core nutrient identity - always required |
| `disease_associations[].disease_term.term` | 3.0 | 85% | Disease connections are high value |
| `deficiency.phenotypes[].phenotype_term.term` | 3.0 | 85% | Deficiency phenotypes are clinical data |
| `functions[].biological_processes[].term` | 2.5 | 80% | Mechanistic understanding |
| `food_sources[].food_term.term` | 2.0 | 75% | Dietary guidance |
| `evidence` (general) | 2.0 | 75% | Scientific backing |
| `description` | 0.5 | - | Nice-to-have context |

### Compliance Status Values

| Status | Meaning |
|--------|---------|
| OK | Field is populated |
| MISSING | Recommended field is empty/absent |

## Priority Order for Improvement

Address fields in this priority order based on weights:

1. **nutrient_term.term** (weight 5.0)
   - Add CHEBI term for the nutrient
   - This is required for every nutrient file

2. **disease_associations[].disease_term.term** (weight 3.0)
   - Add MONDO terms to disease associations
   - Critical for knowledge graph integration

3. **deficiency.phenotypes[].phenotype_term.term** (weight 3.0)
   - Add HP terms to deficiency phenotypes
   - Important for clinical relevance

4. **functions[].biological_processes[].term** (weight 2.5)
   - Add GO terms to biological processes
   - Enables mechanistic queries

5. **food_sources[].food_term.term** (weight 2.0)
   - Add FOODON terms to food sources
   - Important for dietary guidance

6. **evidence items** (weight 2.0)
   - Add PMID-backed evidence to claims
   - Required for scientific validity

7. **descriptions** (weight 0.5)
   - Add explanatory text
   - Lower priority but improves readability

## Common Fixes

### Missing nutrient_term.term
```yaml
nutrient_term:
  preferred_term: Biotin
  term:
    id: CHEBI:15956
    label: biotin
```

Look up: `uv run runoak -i sqlite:obo:chebi info "biotin"`

### Missing disease_term.term
```yaml
disease_associations:
  - name: Biotin and Neural Tube Defects
    disease_term:
      preferred_term: neural tube defect
      term:
        id: MONDO:0005343
        label: neural tube defect
```

Look up: `uv run runoak -i sqlite:obo:mondo info "l~neural tube defect"`

### Missing phenotype_term.term
```yaml
deficiency:
  phenotypes:
    - name: Dermatitis
      phenotype_term:
        preferred_term: Dermatitis
        term:
          id: HP:0000964
          label: Eczema
```

Look up: `uv run runoak -i sqlite:obo:hp info "l~dermatitis"`

### Missing food_term.term
```yaml
food_sources:
  - name: Egg yolk
    food_term:
      preferred_term: egg yolk
      term:
        id: FOODON:00002669
        label: egg yolk
```

Look up: `uv run runoak -i sqlite:obo:foodon info "l~egg yolk"`

### Missing evidence
```yaml
evidence:
  - reference: PMID:12345678
    supports: SUPPORT
    snippet: "Exact quote from abstract"
    explanation: "Why this supports the claim"
```

## Batch Improvement Workflow

### 1. Identify Lowest-Scoring Files
```bash
just gen-dashboard
# Check dashboard/index.html for "Priority Curation Targets"
```

Or:
```bash
just compliance-report | jq -r '.files | sort_by(.weighted_compliance) | .[:10] | .[].file'
```

### 2. Check Threshold Violations
```bash
just compliance-weighted 2>&1 | grep "VIOLATION"
```

### 3. Systematic Field Addition

For systematically missing fields across many files:

```python
import yaml
import glob

# Find files missing nutrient_term.term
for f in glob.glob("kb/nutrients/**/*.yaml", recursive=True):
    with open(f) as file:
        data = yaml.safe_load(file)
    nt = data.get('nutrient_term', {})
    if not nt.get('term'):
        print(f"{f}: missing nutrient_term.term")
```

### 4. Validate After Changes
```bash
# Schema validation
just validate kb/nutrients/vitamins/biotin.yaml

# Term validation
just validate-terms-file kb/nutrients/vitamins/biotin.yaml

# Reference validation
just validate-references kb/nutrients/vitamins/biotin.yaml

# Re-check compliance
just compliance kb/nutrients/vitamins/biotin.yaml
```

## Configuration

### qc_config.yaml Structure

```yaml
# Default for unconfigured fields
default_weight: 1.0
default_min_compliance: null

# Per-slot config (applies everywhere that slot appears)
slots:
  term:
    weight: 2.0
    min_compliance: 75.0

# Per-path config (overrides slot config for specific locations)
paths:
  "nutrient_term.term":
    weight: 5.0
    min_compliance: 95.0
  "disease_associations[].disease_term.term":
    weight: 3.0
    min_compliance: 85.0
```

### Customizing Weights

Edit `conf/qc_config.yaml` to:
- Increase weight for critical fields in your workflow
- Set min_compliance thresholds to enforce standards
- Add new paths for specific validation requirements

## MIC-Specific Compliance Targets

For the MIC knowledge base, prioritize:

| Category | Target | Rationale |
|----------|--------|-----------|
| Vitamins | 90%+ weighted compliance | Core content |
| Minerals | 90%+ weighted compliance | Core content |
| Dietary Factors | 80%+ weighted compliance | Secondary priority |
| Food/Beverages | 75%+ weighted compliance | Tertiary priority |

## Integration with Other Skills

- Use **mic-nutrient-creation** for the overall curation workflow
- Use **mic-terms** when adding ontology term bindings
- Use **mic-references** when adding evidence items
- Run `just qc` after improvements for full validation

## Troubleshooting

### "Weighted Compliance" differs significantly from "Global Compliance"
This indicates your important fields (high weight) have different coverage than
low-priority fields. Focus on improving high-weight fields first.

### Many MISSING descriptions
Descriptions have low weight (0.5) and no minimum threshold. Address these last,
or not at all if not needed.

### Threshold violations blocking CI
Check `conf/qc_config.yaml` for `min_compliance` settings. Either:
1. Improve the field coverage to meet the threshold
2. Lower the threshold if it's too aggressive

### Dashboard not generating
Ensure the dashboard directory exists and you have write permissions:
```bash
mkdir -p dashboard
just gen-dashboard
```
