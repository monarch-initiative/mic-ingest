# MIC Section Extraction Skill

## Overview

Extract and process MIC HTML pages in logical sections to avoid context overflow.
MIC pages are typically 200-300KB, too large for direct context. This skill enables
section-by-section extraction and curation.

## When to Use

- When curating a nutrient and the HTML is too large to process at once
- When you need to extract a specific section (e.g., just "Deficiency")
- When iteratively building a nutrient YAML file section by section

## Section Mapping

MIC HTML sections map to schema fields as follows:

| HTML Section ID(s) | Schema Field | Notes |
|-------------------|--------------|-------|
| `function`, `role-in-*` | `functions` | Biological roles and mechanisms |
| `deficiency` | `deficiency` | Symptoms, at-risk groups, causes |
| `RDA`, `AI`, `UL` | `recommendations` | Dietary intake recommendations |
| `disease-prevention`, `*-prevention` | `disease_associations` | Disease risk relationships |
| `disease-treatment`, `*-treatment` | `disease_associations` | Therapeutic relationships |
| `toxicity`, `safety`, `adverse-*` | `toxicity` | Safety and adverse effects |
| `sources`, `food-sources` | `food_sources` | Dietary sources |
| `drug-interactions` | `drug_interactions` | Drug-nutrient interactions |
| `nutrient-interactions` | `nutrient_interactions` | Nutrient-nutrient interactions |
| `bioavailability`, `absorption` | `bioavailability` | Absorption factors |
| `metabolism` | `metabolism` | Metabolic pathways |
| `references` | `references` | Numbered reference list with PMIDs |

## Commands

### Extract all sections to cache
```bash
just extract-sections cache/mic-pages/vitamin-c.html
# Creates: cache/sections/vitamin-c/
#   - summary.md (section overview)
#   - function.md
#   - deficiency.md
#   - disease-prevention.md
#   - recommendations.md
#   - food-sources.md
#   - toxicity.md
#   - drug-interactions.md
#   - references.md
```

### Extract a specific section
```bash
just extract-section cache/mic-pages/vitamin-c.html deficiency
# Outputs just the deficiency section content
```

### List available sections
```bash
just list-sections cache/mic-pages/vitamin-c.html
# Lists all section IDs found in the HTML
```

## Workflow: Section-by-Section Curation

### Step 1: Prepare the HTML
```bash
just fetch-mic-page vitamins/vitamin-C
just extract-sections cache/mic-pages/vitamin-C.html
```

### Step 2: Extract references first
Always start with references to get the PMID mapping:
```bash
just extract-refs cache/mic-pages/vitamin-C.html
cat cache/mic-refs/vitamin-C-refs.tsv
```

### Step 3: Process sections iteratively

For each section, read the extracted content and populate the YAML:

```bash
# Read a section (fits in context)
cat cache/sections/vitamin-c/function.md

# Or use the extraction script directly
uv run python scripts/extract-sections.py cache/mic-pages/vitamin-C.html --section function
```

### Step 4: Curate each section

For each extracted section:
1. Read the section content
2. Identify entities to ground (diseases, phenotypes, processes)
3. Use OAK to find ontology terms
4. Extract claims and find supporting PMIDs from the reference mapping
5. Add to the nutrient YAML with proper evidence

## Python Script Usage

The `scripts/extract-sections.py` script provides programmatic access:

```python
from scripts.extract_sections import MICSectionExtractor

extractor = MICSectionExtractor("cache/mic-pages/vitamin-C.html")

# Get section overview
print(extractor.list_sections())

# Extract specific section as markdown
deficiency_md = extractor.extract_section("deficiency")

# Extract all sections
sections = extractor.extract_all()
for name, content in sections.items():
    print(f"=== {name} ===")
    print(content[:500])
```

## Section Processing Order

Recommended order for processing sections:

1. **references** - Get PMID mapping first
2. **summary/intro** - Basic nutrient info, alternate names
3. **function** - Biological roles, enzymes, processes
4. **deficiency** - Symptoms, at-risk groups
5. **recommendations** - RDA/AI/UL values
6. **food_sources** - Dietary sources
7. **disease_associations** - Disease prevention/treatment
8. **toxicity** - Safety, adverse effects
9. **drug_interactions** - Drug interactions
10. **nutrient_interactions** - Nutrient interactions

## Handling Large Sections

Some sections (e.g., disease-prevention) may have many subsections. Process iteratively:

```bash
# List subsections
uv run python scripts/extract-sections.py cache/mic-pages/vitamin-C.html --section disease-prevention --list-subsections

# Extract specific subsection
uv run python scripts/extract-sections.py cache/mic-pages/vitamin-C.html --section cardiovascular-disease-prevention
```

## Integration with Other Skills

- After extracting sections, use **mic-terms** for ontology lookups
- Use **mic-references** to validate evidence snippets
- Use **mic-nutrient-creation** for the overall YAML structure
- Use **mic-compliance** to check completeness

## Anti-Hallucination Notes

- Section extraction preserves MIC reference numbers (e.g., "(1)", "(23)")
- Use the extracted references TSV to map numbers to PMIDs
- Always verify snippets come from actual PubMed abstracts
- Don't invent content - only extract what's in the HTML
