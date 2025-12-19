---
name: mic-nutrient-creation
description: >
  Skill for creating new nutrient YAML files from MIC website content.
  Use this when extracting a nutrient from lpi.oregonstate.edu/mic.
  Also useful for enhancing existing nutrient entries.
---

# MIC Nutrient Extraction Skill

## Overview

Guide the creation of new nutrient YAML files in the MIC knowledge base. The MIC website
(lpi.oregonstate.edu/mic) serves as the authoritative research source. This skill
emphasizes evidence-based extraction with proper ontology grounding.

## When to Use

- User asks to create a new nutrient entry
- User asks to curate a vitamin, mineral, or dietary factor
- User names a nutrient that doesn't exist in `kb/nutrients/`

This skill can also be consulted for ongoing curation of existing nutrients.

## Workflow

### Step 1: Identify Nutrient and Category

Determine the nutrient and its category:
- `vitamins/` - Water-soluble and fat-soluble vitamins
- `minerals/` - Essential mineral elements
- `dietary-factors/` - Other dietary factors (fiber, flavonoids, etc.)
- `food-beverages/` - Specific foods or beverages

Check if it already exists:
```bash
ls kb/nutrients/**/*.yaml
```

### Step 2: Mark as In Progress

Update `CURATION-PROGRESS.md` to mark the nutrient as in progress:

1. Find the nutrient's line in the file
2. Change `[ ]` to `[~]` to indicate work has started
3. Optionally add a note about what's being worked on

Example: Change this line:
```markdown
- [ ] Folate (`kb/nutrients/vitamins/folate.yaml`)
```

To:
```markdown
- [~] Folate (`kb/nutrients/vitamins/folate.yaml`) - in progress
```

This helps track curation status and prevents duplicate work.

### Step 3: Fetch MIC Page Content

Download the MIC page using the `just fetch-mic-page` command:

```bash
# Format: just fetch-mic-page {category}/{nutrient}
just fetch-mic-page vitamins/biotin
just fetch-mic-page minerals/calcium
just fetch-mic-page dietary-factors/lipoic-acid
```

This downloads the HTML to `cache/mic-pages/{nutrient}.html`.

**Verify the download:**
```bash
ls -la cache/mic-pages/biotin.html
```

### Step 4: Extract Reference Mapping

**IMPORTANT**: Before adding evidence, extract the MIC reference number → PMID mapping:

```bash
# Get TSV mapping of ref# to PMID
just extract-refs cache/mic-pages/biotin.html
```

This outputs a TSV with columns: `source`, `reference_number`, `pubmed_id`, `citation`

Example output:
```
source          reference_number  pubmed_id       citation
biotin.html     1                               Zempleni J, Wijeratne SSK...
biotin.html     2                 PMID:10357733  Mock DM. Biotin...
biotin.html     3                 PMID:15992684  Zempleni J, Hassan YI...
```

**Key points:**
- Empty `pubmed_id` = book chapter or non-PMID source (use `mic_references` only)
- Has `pubmed_id` = can fetch abstract and add PMID evidence
- The `reference_number` corresponds to `mic_references` values in the YAML

Save the mapping for reference during curation:
```bash
just extract-refs cache/mic-pages/biotin.html > cache/refs/biotin-refs.tsv
```

### Step 5: Create Initial YAML File

Create `kb/nutrients/{category}/{nutrient}.yaml` with the basic structure:

```yaml
name: Biotin
nutrient_term:
  preferred_term: biotin
  term:
    id: CHEBI:15956
    label: biotin
category: vitamin
source_url: https://lpi.oregonstate.edu/mic/vitamins/biotin
alternate_names:
  - Vitamin B7
  - Vitamin H
description: |
  Biotin is a water-soluble B vitamin...

functions: []
deficiency: null
toxicity: null
food_sources: []
drug_interactions: []
nutrient_interactions: []
disease_associations: []
recommendations: null
references: []
```

Validate the structure:
```bash
just validate kb/nutrients/vitamins/biotin.yaml
```

### Step 6: Extract Section by Section

For each MIC page section, read the content and extract structured data:

#### Functions Section
Extract biological roles, enzymes, and processes:
```yaml
functions:
  - name: Cofactor for Carboxylases
    description: |
      Biotin serves as a covalently bound cofactor for five mammalian
      carboxylases that catalyze carbon dioxide transfer reactions.
    biological_processes:
      - preferred_term: fatty acid biosynthesis
        term:
          id: GO:0006633
          label: fatty acid biosynthetic process
    genes:
      - preferred_term: PC
        description: Pyruvate carboxylase
        term:
          id: HGNC:8636
          label: PC
    evidence:
      - reference: PMID:10357733
        supports: SUPPORT
        snippet: "Biotin serves as a covalently bound coenzyme for five mammalian carboxylases"
        explanation: Directly supports biotin's role as carboxylase cofactor
```

#### Deficiency Section
Extract symptoms, at-risk groups, and causes:
```yaml
deficiency:
  name: Biotin Deficiency
  description: |
    Biotin deficiency is rare in healthy individuals...
  phenotypes:
    - name: Dermatitis
      phenotype_term:
        preferred_term: dermatitis
        term:
          id: HP:0000964
          label: Eczema
      frequency: FREQUENT
      evidence:
        - reference: PMID:10357733
          supports: SUPPORT
          snippet: "dermatitis, conjunctivitis, and alopecia"
  at_risk_groups:
    - name: Pregnant women
      description: Marginal biotin deficiency common during pregnancy
```

#### Disease Prevention Section
Extract disease associations:
```yaml
disease_associations:
  - name: Biotin and Neural Tube Defects
    disease_term:
      preferred_term: neural tube defect
      term:
        id: MONDO:0005343
        label: neural tube defect
    relationship_type: RISK_FACTOR
    direction: DECREASED
    population_context: pregnant women with marginal biotin status
    evidence:
      - reference: PMID:16549401
        supports: SUPPORT
        snippet: "low biotin status during early pregnancy..."
```

#### Food Sources Section
Extract dietary sources:
```yaml
food_sources:
  - name: Egg yolk
    food_term:
      preferred_term: egg yolk
      term:
        id: FOODON:00002669
        label: egg yolk
    amount: "10 mcg"
    serving_size: "1 large egg"
```

#### Drug Interactions Section
Extract interactions with medications:
```yaml
drug_interactions:
  - name: Anticonvulsants and Biotin
    drug_term:
      preferred_term: anticonvulsant
    interaction_type: REDUCES_ABSORPTION
    clinical_significance: MODERATE
    evidence:
      - reference: PMID:8157857
        supports: SUPPORT
        snippet: "long-term anticonvulsant therapy..."
```

### Step 7: Ground Entities to Ontologies

Use OAK to find correct ontology terms:

#### CHEBI (nutrients)
```bash
uv run runoak -i sqlite:obo:chebi info "biotin"
uv run runoak -i sqlite:obo:chebi info "l~ascorbic acid"
```

#### HP (phenotypes)
```bash
uv run runoak -i sqlite:obo:hp info "l~dermatitis"
uv run runoak -i sqlite:obo:hp info HP:0000964
```

#### GO (biological processes)
```bash
uv run runoak -i sqlite:obo:go info "l~fatty acid biosynthesis"
```

#### MONDO (diseases)
```bash
uv run runoak -i sqlite:obo:mondo info "l~neural tube defect"
```

#### FOODON (foods)
```bash
uv run runoak -i sqlite:obo:foodon info "l~egg yolk"
```

#### HGNC (genes)
```bash
uv run runoak -i sqlite:obo:hgnc info "l~pyruvate carboxylase"
```

### Step 8: Add Evidence

Use the reference mapping from Step 4 to add evidence. For each `mic_references` number:

1. **Check if PMID exists** in your ref mapping TSV
2. **If PMID exists**: Fetch abstract and add evidence with exact quote
3. **If no PMID** (book/database): Keep `mic_references` only, no PMID evidence

```yaml
evidence:
  - reference: PMID:12345678
    supports: SUPPORT
    snippet: "Exact quote from abstract"
    explanation: "Why this supports the claim"
```

Fetch and verify abstracts:
```bash
# Look up PMID for MIC reference number (from Step 3 mapping)
# e.g., ref 55 → PMID:15585762

just fetch-reference PMID:15585762
cat cache/references/pmid_15585762.md
```

#### Evidence Rules

1. **NEVER fabricate PMIDs** - Only use PMIDs from the MIC page references (Step 3 mapping)
2. **NEVER paraphrase snippets** - Use exact quotes from abstracts
3. **Always verify** - Fetch and check abstracts before using
4. **Book references are OK** - If MIC ref has no PMID, use `mic_references` without evidence block

### Step 9: Validate

Run all validation checks:

```bash
# Schema validation
just validate kb/nutrients/vitamins/biotin.yaml

# Term validation (ontology IDs and labels)
just validate-terms-file kb/nutrients/vitamins/biotin.yaml

# Reference validation (snippets match abstracts)
just validate-references kb/nutrients/vitamins/biotin.yaml

# Full QC
just qc
```

### Step 10: Compliance Check and Mark Complete

Check completeness:
```bash
just compliance kb/nutrients/vitamins/biotin.yaml
```

Address high-priority missing fields first:
1. `nutrient_term.term` (weight 5.0)
2. `disease_associations[].disease_term.term` (weight 3.0)
3. `deficiency.phenotypes[].phenotype_term.term` (weight 3.0)
4. Evidence items (weight 2.0)

**When all validation passes**, update `CURATION-PROGRESS.md` to mark the nutrient as completed:

1. Find the nutrient's line in the file
2. Change `[~]` to `[x]` to indicate completion
3. Remove any "in progress" note

Example: Change this line:
```markdown
- [~] Folate (`kb/nutrients/vitamins/folate.yaml`) - in progress
```

To:
```markdown
- [x] Folate (`kb/nutrients/vitamins/folate.yaml`)
```

## File Naming Convention

Use lowercase with hyphens:
- "Vitamin B12" -> `vitamin-b12.yaml`
- "Alpha-Lipoic Acid" -> `alpha-lipoic-acid.yaml`
- "Coenzyme Q10" -> `coenzyme-q10.yaml`

## Minimum Required Fields

A new nutrient file MUST include at minimum:

| Field | Source | Notes |
|-------|--------|-------|
| `name` | MIC page | Human-readable nutrient name |
| `nutrient_term` | OAK lookup | CHEBI term binding |
| `category` | MIC category | vitamin, mineral, etc. |
| `source_url` | MIC URL | Full URL to MIC page |
| `functions` (1+) | MIC content | At least one function |
| `evidence` (1+) | MIC references | At least one PMID reference |

## Common Validation Errors

### "Term not found in ontology"
Re-run OAK lookup with fuzzy search:
```bash
uv run runoak -i sqlite:obo:chebi info "l~<term>"
```

### "Snippet not found in reference"
The quoted text must be from the PMID's abstract. Fetch and verify:
```bash
just fetch-reference PMID:12345678
```

### "Required field missing"
Check the schema for required fields. `nutrient_term` is always required.

## Integration with Other Skills

- Use **mic-terms** for detailed ontology term lookups
- Use **mic-references** to validate/repair evidence items
- Use **mic-compliance** to check completeness

## Anti-Hallucination Checklist

Before finalizing a nutrient file, verify:

- [ ] All PMIDs are from the MIC page references
- [ ] All snippets are exact quotes from PubMed abstracts
- [ ] CHEBI term exists and label matches exactly
- [ ] HP terms exist and labels match exactly
- [ ] GO terms exist and labels match exactly
- [ ] MONDO terms exist and labels match exactly
- [ ] FOODON terms exist and labels match exactly
- [ ] `just validate` passes
- [ ] `just validate-terms-file` passes
- [ ] `just validate-references` passes
