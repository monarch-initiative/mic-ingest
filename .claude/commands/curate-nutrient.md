---
description: Curate a nutrient from the MIC website. Creates or enhances a nutrient YAML file.
argument-hint: [NUTRIENT_NAME] [CATEGORY]
---

Curate the nutrient specified in $ARGUMENTS.

**IMPORTANT**: You MUST consult the **mic-nutrient-creation** skill for detailed workflow instructions.

## Arguments

- **NUTRIENT_NAME**: Name of the nutrient (e.g., biotin, folate, vitamin-c, calcium)
- **CATEGORY**: One of: vitamins, minerals, dietary-factors, food-beverages

## Workflow Summary

1. Check if nutrient already exists in `kb/nutrients/{CATEGORY}/`
2. Fetch MIC page content if needed
3. Create or update the nutrient YAML file
4. Extract all sections (functions, deficiency, disease associations, etc.)
5. Ground entities to ontologies using OAK
6. Add evidence with real PMIDs from MIC references
7. Validate before committing

## Example Usage

```
/curate-nutrient biotin vitamins
/curate-nutrient calcium minerals
/curate-nutrient alpha-lipoic-acid dietary-factors
```

## Integration

- Use **mic-terms** skill for ontology lookups
- Use **mic-references** skill for evidence validation
- Use **mic-compliance** skill to check completeness
