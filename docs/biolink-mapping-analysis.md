# MIC Schema to Biolink Model Mapping Analysis

This document analyzes the mapping between the MIC (Micronutrient Information Center) schema and the Biolink model for KGX export.

## Executive Summary

The MIC schema captures nutrient information including functions, deficiency phenotypes, disease associations, drug/nutrient interactions, and food sources. While much of this maps to existing Biolink patterns, several gaps exist:

1. **No `Nutrient` class in Biolink** - nutrients must be modeled as `ChemicalEntity` or `SmallMolecule`
2. **Treatment predicates require nuanced mapping** - MIC's `THERAPEUTIC` should NOT uniformly map to `treats`; Biolink has a hierarchy (`treats` → `in clinical trials for` → `studied to treat` → `beneficial in models for`) that should be used based on evidence strength
3. **Limited dietary/nutritional predicates** - Biolink has `has nutrient` and `nutrient of` but lacks deficiency-related predicates
4. **No deficiency association pattern** - the concept of "X deficiency causes phenotype Y" requires a new pattern
5. **Interaction types need mapping** - MIC's `InteractionTypeEnum` needs alignment with Biolink's causal mechanism qualifiers

**Key Recommendation:** Split MIC's `THERAPEUTIC` relationship type into evidence-stratified values (`ESTABLISHED_TREATMENT`, `STUDIED_FOR_TREATMENT`, `PRECLINICAL_EVIDENCE`) to enable accurate predicate selection during KGX export.

---

## Entity Type Mapping

### MIC → Biolink Entity Mapping

| MIC Class/Concept | Biolink Class | Notes |
|-------------------|---------------|-------|
| `Nutrient` | `ChemicalEntity` or `SmallMolecule` | No `Nutrient` class exists; use CHEBI terms |
| `DiseaseDescriptor` | `Disease` | Direct mapping via MONDO |
| `PhenotypeDescriptor` | `PhenotypicFeature` | Direct mapping via HP |
| `BiologicalProcessDescriptor` | `BiologicalProcess` | Direct mapping via GO |
| `GeneDescriptor` | `Gene` or `GeneOrGeneProduct` | Direct mapping via HGNC |
| `FoodDescriptor` | `Food` | Biolink has `Food` class (parent: `ChemicalMixture`) |
| `DrugDescriptor` | `Drug` | Direct mapping |
| `AnatomicalEntityDescriptor` | `AnatomicalEntity` | Direct mapping via UBERON |
| `CellularComponentDescriptor` | `CellularComponent` | Direct mapping via GO |

### Missing Entity Types

| MIC Concept | Suggested Biolink Addition |
|-------------|---------------------------|
| Nutrient deficiency state | Could use `ChemicalExposure` with direction qualifier = "decreased" |
| At-risk population group | No direct equivalent; could use `PopulationOfIndividualOrganisms` |
| Dietary recommendation | No equivalent; not typically KG content |

---

## Association Mapping

### Mappable Associations

#### 1. Nutrient → Disease Associations

**MIC Pattern:** `DiseaseAssociation` with `relationship_type` enum
```yaml
disease_associations:
  - disease_term:
      term:
        id: MONDO:0005301
        label: multiple sclerosis
    relationship_type: THERAPEUTIC
```

**Biolink Treatment Predicate Hierarchy:**

```
treats or applied or studied to treat  (base grouping predicate)
├── treats                              (strong: approved, phase 3+, established)
│   └── ameliorates condition           (subset - ameliorates symptoms)
├── applied to treat                    (actually taken by patients)
├── studied to treat                    (scientifically studied)
│   ├── in clinical trials for          (human clinical trials)
│   └── in preclinical trials for       (pre-clinical studies)
│       └── beneficial in models for    (animal/cell models only)
```

**THERAPEUTIC Mapping (Nuanced by Evidence Strength):**

The MIC `THERAPEUTIC` relationship type should NOT uniformly map to `treats`. Based on analysis of curated MIC descriptions, use this mapping:

| Evidence Category | MIC Language Pattern | Biolink Predicate | knowledge_level |
|-------------------|---------------------|-------------------|-----------------|
| **Established treatment** | "treatment of choice", "established", "standard treatment" | `treats` | `knowledge_assertion` |
| **Strong clinical evidence** | "has been shown to", "significantly reduces", replicated RCTs | `treats` | `knowledge_assertion` |
| **Research evidence (any strength)** | "may be useful", "meta-analyses suggest", "evidence is mixed", "has been investigated", "preliminary", "results inconclusive" | `studied to treat` | `knowledge_assertion` |
| **Model systems only** | "animal studies show", "in vitro" | `beneficial in models for` | `knowledge_assertion` |
| **Refuted** | "not found effective", "did not reduce" | No positive edge | N/A |

**Note on `in clinical trials for`:** This predicate should ONLY be used when we have specific evidence that registered clinical trials exist (e.g., ClinicalTrials.gov IDs). Most MIC therapeutic claims describe published research studies, not necessarily formal clinical trials. Use `studied to treat` for general research evidence.

**Examples from MIC Data:**

| Nutrient | Disease | MIC Description | Appropriate Predicate |
|----------|---------|-----------------|----------------------|
| Biotin | Biotinidase deficiency | "Treatment involves supplemental biotin" | `treats` |
| Riboflavin | Migraine | "superior to placebo in reducing attack frequency" | `treats` |
| CoQ10 | Heart failure | "may be useful adjunct...though evidence is mixed" | `studied to treat` |
| Biotin | Multiple sclerosis | "investigated...Results remain inconclusive" | `studied to treat` |
| Biotin | Type 2 diabetes | "Evidence is mixed and inconclusive" | `studied to treat` |

**Other Relationship Types:**

| MIC `relationship_type` | Biolink Association | Biolink Predicate |
|-------------------------|---------------------|-------------------|
| `PROTECTIVE` | `ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation` | `preventative for condition` |
| `RISK_FACTOR` | `ChemicalEntityToDiseaseOrPhenotypicFeatureAssociation` | `affects likelihood of` |
| `MARKER` | `ChemicalEntityToDiseaseOrPhenotypicFeatureAssociation` | `biomarker for` |
| `DEFICIENCY_CAUSES` | **No direct mapping** | See "Gaps" section |

#### 2. Nutrient → Biological Process Associations

**MIC Pattern:** `Function` with `biological_processes`
```yaml
functions:
  - name: Cofactor for Carboxylases
    biological_processes:
      - term:
          id: GO:0006633
          label: fatty acid biosynthetic process
```

**Biolink Mapping:**
- Association: `ChemicalEntityToBiologicalProcessAssociation`
- Predicates: `participates in`, `enables`, `actively involved in`

#### 3. Nutrient → Gene Associations

**MIC Pattern:** `Function` with `genes`
```yaml
functions:
  - genes:
      - term:
          id: HGNC:93
          label: ACACA
```

**Biolink Mapping:**
- Association: `ChemicalAffectsGeneAssociation` or `ChemicalGeneInteractionAssociation`
- Predicates: `affects`, `regulates`, `physically interacts with`
- Qualifiers: `subject_aspect_qualifier`, `object_aspect_qualifier`, `causal_mechanism_qualifier`

#### 4. Drug Interactions

**MIC Pattern:** `DrugInteraction` with `interaction_type`
```yaml
drug_interactions:
  - drug_term:
      preferred_term: anticonvulsant
    interaction_type: REDUCES_ABSORPTION
```

**Biolink Mapping:**
- Association: `ChemicalGeneInteractionAssociation` (if gene-mediated) or `ChemicalToChemicalAssociation`
- Predicates: `affects`, `interacts with`
- Qualifiers: `causal_mechanism_qualifier` for mechanism

| MIC `interaction_type` | Biolink Mechanism Qualifier |
|------------------------|----------------------------|
| `REDUCES_ABSORPTION` | No direct equivalent |
| `INCREASES_ABSORPTION` | No direct equivalent |
| `AFFECTS_METABOLISM` | `catalytic_activity` or related |
| `SYNERGISTIC` | `potentiation` |
| `ANTAGONISTIC` | `antagonism` |

#### 5. Deficiency → Phenotype Associations

**MIC Pattern:** `Deficiency` with `phenotypes`
```yaml
deficiency:
  phenotypes:
    - phenotype_term:
        term:
          id: HP:0001596
          label: Alopecia
      frequency: FREQUENT
```

**Biolink Mapping Approach:**
- **Option A**: Model deficiency as a disease state (if MONDO term exists)
  - Use `DiseaseToPhenotypicFeatureAssociation`
  - Predicate: `has phenotype`
  - Qualifiers: `frequency_qualifier`, `onset_qualifier`

- **Option B**: Model as chemical exposure with decreased direction
  - Use `ExposureEventToPhenotypicFeatureAssociation`
  - Subject: nutrient with `subject_direction_qualifier: decreased`

#### 6. Food Source Associations

**MIC Pattern:** `FoodSource`
```yaml
food_sources:
  - food_term:
      preferred_term: liver
    amount: "27-35 mcg"
```

**Biolink Mapping:**
- Association: No specific association class
- Predicates: `has nutrient` (Food → ChemicalEntity) or `food component of` (ChemicalEntity → Food)

---

## Gaps Requiring Schema Changes

### MIC Schema Changes Needed

#### 1. Add explicit predicate slots

Current MIC schema uses `relationship_type` enum but should map to explicit Biolink predicates:

```yaml
# Suggested addition to DiseaseAssociation
slots:
  predicate:
    description: The Biolink predicate for this association
    range: uriorcurie
    slot_uri: rdf:predicate
```

#### 2. Align direction qualifiers

MIC `ModifierEnum` should align with Biolink `DirectionQualifierEnum`:

| MIC `ModifierEnum` | Biolink `DirectionQualifierEnum` |
|-------------------|----------------------------------|
| `INCREASED` | `increased` / `upregulated` |
| `DECREASED` | `decreased` / `downregulated` |
| `ABNORMAL` | No equivalent |
| `DYSREGULATED` | No equivalent |
| `ABSENT` | No equivalent |

#### 3. Add knowledge level tracking

Biolink uses `knowledge_level` slot with enum values:
- `knowledge_assertion`
- `prediction`
- `statistical_association`
- `observation`

MIC should add this to track evidence strength:

```yaml
slots:
  knowledge_level:
    range: KnowledgeLevelEnum
    description: Level of knowledge for this association
```

#### 4. Restructure for edge-centric model

Current MIC is nutrient-centric (document model). For KGX, we need edge-centric:

```yaml
# Current (nested in Nutrient)
disease_associations:
  - disease_term: ...
    relationship_type: THERAPEUTIC

# For KGX export, need to generate:
# subject: CHEBI:15956 (biotin)
# predicate: biolink:treats
# object: MONDO:0005301 (multiple sclerosis)
# qualifiers: {...}
```

### Biolink Model Additions Suggested

#### 1. Nutrient class

```yaml
classes:
  nutrient:
    is_a: small molecule
    description: >-
      A chemical entity that provides nourishment essential for growth
      and maintenance of life. Includes vitamins, minerals, and other
      essential dietary compounds.
    id_prefixes:
      - CHEBI
```

#### 2. Nutrient deficiency exposure

```yaml
classes:
  dietary exposure:
    is_a: chemical exposure
    description: >-
      A chemical exposure specifically related to dietary intake,
      including both adequate and deficient nutritional states.

  nutrient deficiency exposure:
    is_a: dietary exposure
    description: >-
      A dietary exposure representing insufficient intake or absorption
      of a nutrient, leading to physiological consequences.
```

#### 3. Deficiency-related predicates

```yaml
slots:
  deficiency causes:
    is_a: causes
    description: >-
      Holds between a nutrient and a phenotype/disease where insufficient
      levels of the nutrient cause the phenotype/disease.
    domain: chemical entity
    range: disease or phenotypic feature

  deficiency associated with:
    is_a: associated with
    description: >-
      Holds between a nutrient and a phenotype where insufficient levels
      are statistically associated with the phenotype.
```

#### 4. Nutritional interaction predicates

```yaml
slots:
  reduces absorption of:
    is_a: affects
    description: >-
      Holds between two chemical entities where the presence of one
      reduces the intestinal absorption of the other.

  increases absorption of:
    is_a: affects
    description: >-
      Holds between two chemical entities where the presence of one
      increases the intestinal absorption of the other.

  competes for transport with:
    is_a: interacts with
    description: >-
      Holds between two chemical entities that compete for the same
      membrane transport mechanism.
```

#### 5. Dietary recommendation association (optional)

```yaml
classes:
  nutrient to population recommendation association:
    is_a: association
    description: >-
      An association stating recommended intake levels of a nutrient
      for a specific population group.
    slots:
      - subject  # nutrient
      - object   # population group
      - recommended daily amount
      - upper intake level
      - source authority
```

---

## Proposed Mapping Implementation

### Phase 1: Direct Mappings

These can be implemented now with existing Biolink:

1. **Nutrient → Disease (therapeutic)**
   - `ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation`
   - Predicate selection based on evidence strength (see detailed mapping above):
     - `treats` - only for established treatments with strong clinical evidence
     - `studied to treat` - for research evidence of any strength (most MIC claims)
     - `beneficial in models for` - for preclinical/animal model evidence only
     - `in clinical trials for` - ONLY if we have specific trial registry evidence
   - Always include `knowledge_level` qualifier

2. **Nutrient → Biological Process**
   - `ChemicalEntityToBiologicalProcessAssociation`
   - predicate: `participates in` or `enables`

3. **Nutrient → Gene**
   - `ChemicalAffectsGeneAssociation`
   - predicate: `affects`
   - Use qualifiers for specificity

4. **Food → Nutrient**
   - Use `has nutrient` predicate
   - Subject: Food (FOODON), Object: ChemicalEntity (CHEBI)

### Phase 2: Approximations

These require creative use of existing Biolink:

1. **Deficiency → Phenotype**
   - Model as `ExposureEventToPhenotypicFeatureAssociation`
   - Create a "deficiency" node (could use MONDO if exists, or create custom ID)
   - predicate: `causes` or `has phenotype`

2. **Drug-Nutrient Interactions**
   - `ChemicalToChemicalAssociation`
   - predicate: `affects` with qualifiers
   - Add mechanism via `causal_mechanism_qualifier`

### Phase 3: Biolink Extensions (propose to community)

1. Submit PR for `Nutrient` class (subclass of `SmallMolecule`)
2. Submit PR for `NutrientDeficiencyExposure` class
3. Submit PR for deficiency-related predicates
4. Submit PR for nutritional interaction predicates

---

## Evidence and Provenance Mapping

### Current MIC Evidence Model

```yaml
evidence:
  - reference: PMID:12345678
    supports: SUPPORT
    snippet: "Exact quoted text"
    explanation: "Why this supports the claim"
```

### Biolink Evidence Slots

- `has evidence`: connects to `EvidenceType` (ECO terms)
- `publications`: list of `Publication` entities
- `primary knowledge source`: information resource
- `knowledge level`: assertion, prediction, etc.

### Recommended Mapping

```yaml
# For each evidence item:
has_evidence: ECO:0000033  # traceable author statement
publications:
  - PMID:12345678
primary_knowledge_source: infores:mic
knowledge_level: knowledge_assertion
```

---

## Summary of Changes Needed

### MIC Schema Changes (Required for KGX)

| Change | Priority | Effort |
|--------|----------|--------|
| **Split `THERAPEUTIC` into granular evidence levels** | High | Medium |
| Add `predicate` slot to associations | High | Low |
| Align `ModifierEnum` with Biolink `DirectionQualifierEnum` | High | Low |
| Add `knowledge_level` slot | Medium | Low |
| Create KGX export transform | High | Medium |
| Map `relationship_type` to Biolink predicates | High | Low |

#### Recommended: Split THERAPEUTIC Relationship Type

The current `THERAPEUTIC` enum value is too coarse. Replace with evidence-stratified values:

```yaml
RelationshipTypeEnum:
  permissible_values:
    # Replace THERAPEUTIC with these:
    ESTABLISHED_TREATMENT:
      description: >-
        Established/approved treatment with strong clinical evidence.
        Maps to biolink:treats.
    STUDIED_FOR_TREATMENT:
      description: >-
        Has been studied for treatment in human research (RCTs, meta-analyses, etc.).
        Evidence may be strong, mixed, or inconclusive.
        Maps to biolink:studied_to_treat.
    PRECLINICAL_EVIDENCE:
      description: >-
        Evidence from animal models or in vitro studies only.
        Maps to biolink:beneficial_in_models_for.

    # Keep existing:
    RISK_FACTOR:
      description: Nutrient status affects disease risk
    PROTECTIVE:
      description: Higher nutrient status reduces risk
    MARKER:
      description: Nutrient level indicates disease state
    DEFICIENCY_CAUSES:
      description: Deficiency of nutrient causes the condition
```

Note: We removed `CLINICAL_EVIDENCE` because `in clinical trials for` should only be used when we have specific evidence of registered clinical trials (e.g., ClinicalTrials.gov IDs). Most MIC content describes published research, which maps to `studied to treat`.

This allows curators to capture evidence strength at curation time rather than requiring text analysis during export.

### Biolink Model Proposals (Nice to have)

| Proposal | Priority | Likelihood of Acceptance |
|----------|----------|-------------------------|
| `Nutrient` class | Medium | High - straightforward |
| `NutrientDeficiencyExposure` class | Medium | Medium |
| `deficiency causes` predicate | High | Medium |
| Absorption-related predicates | Low | Low - very specific |

---

## Next Steps

1. **Immediate**: Create a KGX export script that transforms MIC YAML to edge TSV using existing Biolink patterns
2. **Short-term**: Add predicate and qualifier slots to MIC schema
3. **Medium-term**: Submit Biolink PRs for `Nutrient` class and deficiency predicates
4. **Ongoing**: Document mapping decisions and edge cases
