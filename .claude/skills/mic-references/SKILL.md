---
name: mic-references
description: >
  Skill for validating and repairing evidence references in the MIC knowledge base.
  Use this when working with evidence items in nutrient YAML files, validating
  that snippet text matches PubMed abstracts, and repairing misquoted evidence.
  Critical for ensuring scientific accuracy and preventing AI hallucinations.
---

# MIC Reference Validation Skill

## Overview

Validate and repair evidence references in the MIC nutrient knowledge base. This ensures
that quoted snippets actually appear in the cited PubMed abstracts, preventing fabricated
or misquoted evidence from entering the knowledge base.

## When to Use

- Validating evidence items after adding new nutrient content
- Checking that snippets match their cited PMID abstracts
- Repairing evidence items with minor text mismatches
- Removing fabricated evidence (AI hallucinations)
- QC checks before committing changes

## Evidence Item Structure

All evidence items follow this YAML structure:

```yaml
evidence:
  - reference: PMID:12345678
    supports: SUPPORT  # SUPPORT, REFUTE, PARTIAL, NO_EVIDENCE, WRONG_STATEMENT
    snippet: "Exact quoted text from the abstract"
    explanation: "Why this evidence supports/refutes the claim"
```

### Support Classifications

| Value | Meaning |
|-------|---------|
| SUPPORT | Evidence directly supports the statement |
| REFUTE | Evidence contradicts the statement |
| PARTIAL | Evidence partially supports with caveats |
| NO_EVIDENCE | Citation exists but doesn't address the claim |
| WRONG_STATEMENT | The statement itself is incorrect |

## MIC-Specific Considerations

The MIC website uses numbered references (e.g., "(1)", "(26)"). The MIC HTML pages include
PubMed links directly in the reference list, making automated extraction possible.

### Automated PMID Extraction Workflow

1. **Fetch and cache the MIC page**:
```bash
just fetch-mic-page vitamins/vitamin-C
# Saves to cache/mic-pages/vitamin-C.html
```

2. **Extract reference number → PMID mappings**:
```bash
just extract-refs cache/mic-pages/vitamin-C.html
# Outputs TSV: source, reference_number, pubmed_id, citation
```

3. **Save mappings for later use**:
```bash
just extract-refs-save cache/mic-pages/vitamin-C.html
# Saves to cache/mic-refs/vitamin-C-refs.tsv
```

4. **Fetch all abstracts at once**:
```bash
just fetch-all-abstracts cache/mic-refs/vitamin-C-refs.tsv
# Downloads all PubMed abstracts to cache/references/
```

### Example Output
```
source          reference_number  pubmed_id       citation
vitamin-C.html  2                 PMID:3015170    Englard S, Seifter S. The biochemical functions...
vitamin-C.html  18                PMID:29099763   Carr AC, Maggini S. Vitamin C and immune function...
vitamin-C.html  5                                 Jariwalla RJ... (book - no PMID)
```

Note: Some references (books, chapters) don't have PMIDs. These will have empty `pubmed_id` fields.

## Fetching References

### Fetch a Single Reference
```bash
just fetch-reference PMID:10357733
```

This downloads the PubMed abstract and caches it in `cache/references/`.

### View Cached Abstract
```bash
cat cache/references/pmid_10357733.md
```

### Manual PubMed Lookup
If PMID is unknown, search PubMed:
1. Go to https://pubmed.ncbi.nlm.nih.gov/
2. Search for the paper title/author
3. Get the PMID from the URL

## Validation Commands

### Validate a Single File
```bash
uv run linkml-reference-validator validate data kb/nutrients/vitamins/biotin.yaml \
  --schema src/mic_ingest/schema/mic.yaml \
  --target-class Nutrient
```

### Using Just Commands
```bash
# Validate single file
just validate-references kb/nutrients/vitamins/biotin.yaml

# Validate all files
just validate-references-all

# Full QC (includes reference validation)
just qc
```

## Repair Commands

### Dry Run (Preview Changes)
```bash
uv run linkml-reference-validator repair data kb/nutrients/vitamins/biotin.yaml \
  --schema src/mic_ingest/schema/mic.yaml \
  --target-class Nutrient
```

### Auto-Repair with Threshold
```bash
uv run linkml-reference-validator repair data kb/nutrients/vitamins/biotin.yaml \
  --schema src/mic_ingest/schema/mic.yaml \
  --target-class Nutrient \
  --no-dry-run \
  --fix-threshold 0.80
```

The `--fix-threshold 0.80` means snippets with 80%+ similarity to actual abstract
text will be automatically corrected.

## Common Error Patterns

### 1. Snippet Not Found in Abstract
```
ERROR: Snippet not found in reference PMID:12345678
  Snippet: "The patient showed symptoms..."
  Abstract: [actual abstract text]
```

**Solutions:**
- Check if snippet is from full text (not abstract) - may need different quote
- Check for minor typos - use repair with threshold
- If fabricated, remove the evidence item entirely

### 2. Reference Cannot Be Fetched
```
ERROR: Could not fetch reference PMID:99999999
```

**Solutions:**
- Verify PMID exists on PubMed
- Check for typos in PMID
- If PMID is invalid, find the correct one from MIC reference list
- Remove the evidence item if reference can't be verified

### 3. Fabricated Evidence Patterns

Watch for these red flags indicating fabricated evidence:

- Snippet says "N/A" or "No abstract available"
- Snippet is suspiciously perfect match to the claim (paraphrase)
- PMID doesn't exist or is for unrelated topic
- Generic statements without specific data
- Snippet contains information not in the abstract

**Solution:** Remove the entire evidence item.

## Best Practices

### Adding New Evidence

1. **Use real PMIDs**: Always verify the PMID exists on PubMed
2. **Quote exactly**: Copy snippet text directly from the abstract
3. **Keep snippets focused**: 1-2 sentences that directly support the claim
4. **Validate immediately**: Run validation after adding evidence

### MIC Reference Extraction Workflow

1. Find the numbered reference on the MIC page
2. Search PubMed for the paper (title/author)
3. Get the PMID from PubMed
4. Fetch the abstract: `just fetch-reference PMID:XXXXXXXX`
5. Find a relevant quote from the abstract
6. Add the evidence item with exact quote
7. Validate: `just validate-references`

### Reviewing Evidence

When reviewing nutrient files:

1. Run validation first to catch obvious issues
2. Spot-check PMIDs on PubMed
3. Look for suspiciously perfect or generic snippets
4. Remove any evidence that cannot be verified

## Cache Management

Reference validator caches PubMed abstracts in `cache/references/`.

### Clear Cache
```bash
rm -rf cache/references/
```

### Cache File Format
```markdown
# PMID:12345678

## Title
Paper Title Here

## Abstract
Full abstract text here...

## Authors
Author 1, Author 2, ...

## Journal
Journal Name. 2020;123(4):567-890.
```

## Evidence Writing Guidelines

### Good Example
```yaml
evidence:
  - reference: PMID:10357733
    supports: SUPPORT
    snippet: "Biotin serves as a covalently bound coenzyme for five mammalian carboxylases"
    explanation: This directly states biotin's role as a carboxylase cofactor, supporting the function described.
```

### Bad Example (Fabricated)
```yaml
evidence:
  - reference: PMID:10357733
    supports: SUPPORT
    snippet: "Biotin is essential for carboxylase function and deficiency causes symptoms."
    # This is a paraphrase, not a real quote - will fail validation
    explanation: Supports biotin function.
```

### When Evidence Cannot Be Verified

If a claim is well-established but you cannot find a quotable snippet:

- **Option A**: Move the claim to the `notes` field (no evidence required)
- **Option B**: Find a different paper with a quotable abstract
- **Option C**: Remove the evidence block entirely, keep the description

**Do NOT** fabricate quotes or use incorrect PMIDs.

## Batch Processing Workflow

### 1. Get Error Count
```bash
for f in kb/nutrients/**/*.yaml; do
  errors=$(just validate-references "$f" 2>&1 | grep -c "ERROR" || echo 0)
  if [ "$errors" -gt 0 ]; then
    echo "$f: $errors errors"
  fi
done
```

### 2. Auto-Repair All
```bash
for f in kb/nutrients/**/*.yaml; do
  uv run linkml-reference-validator repair data "$f" \
    --schema src/mic_ingest/schema/mic.yaml \
    --target-class Nutrient \
    --no-dry-run \
    --fix-threshold 0.80
done
```

## Integration with Other Skills

- Use **mic-nutrient-creation** for the overall curation workflow
- Use **mic-terms** when adding ontology bindings
- Use **mic-compliance** to check overall completeness
