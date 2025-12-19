# MIC-Ingest Rewrite Plan: Dismech Pattern

## Executive Summary

Rewrite mic-ingest to follow the dismech architecture: schema-first design with nested LinkML models, one YAML file per nutrient, evidence-based claims with validation, and treating the MIC website as the authoritative "research" source (replacing AI deep research).

---

## Current State Analysis

### mic-ingest (Current)
- **Architecture**: OntoGPT-driven extraction with flat relationship schema
- **Schema**: `mic.yaml` - flat `NutrientTo*Relationship` classes extending `ScientificClaim`
- **Output**: TSV files with ~30k associations
- **Evidence**: Reference numbers only (e.g., "26", "45") mapped to PMIDs
- **Validation**: Minimal; relies on OntoGPT's entity grounding

### dismech (Target Pattern)
- **Architecture**: Schema-first with nested hierarchical data model
- **Schema**: `dismech.yaml` - `Disease` as tree root with nested Pathophysiology, Phenotypes, Treatments, etc.
- **Output**: One YAML file per disorder (`kb/disorders/*.yaml`)
- **Evidence**: Full `EvidenceItem` with PMID, support classification, verbatim snippet, explanation
- **Validation**: Multi-layer (schema → term → reference → compliance)

---

## Phase 1: Schema Design

### 1.1 Core Schema Structure

Create a new nested LinkML schema (`src/mic_ingest/schema/mic.yaml`) with `Nutrient` as the tree root:

```yaml
# Proposed top-level structure
Nutrient:
  tree_root: true
  slots:
    - name                    # e.g., "Biotin", "Riboflavin"
    - nutrient_term           # NutrientDescriptor -> CHEBI binding
    - alternate_names         # ["Vitamin B7", "Vitamin H"]
    - category                # "vitamin", "mineral", "dietary-factor"
    - description             # Overview text
    - source_url              # https://lpi.oregonstate.edu/mic/vitamins/biotin
    - functions               # List[Function] - biological roles
    - deficiency              # Deficiency - signs, symptoms, at-risk groups
    - toxicity                # Toxicity - upper limits, adverse effects
    - food_sources            # List[FoodSource]
    - drug_interactions       # List[DrugInteraction]
    - nutrient_interactions   # List[NutrientInteraction]
    - disease_associations    # List[DiseaseAssociation]
    - health_claims           # List[HealthClaim]
    - recommendations         # DietaryRecommendations - RDA, AI, UL
    - bioavailability         # Bioavailability info
    - metabolism              # Metabolism pathways
    - references              # List[PublicationReference] - top-level refs with findings
```

### 1.2 Descriptor Classes (following dismech pattern)

Create ontology-bindable descriptors:

```yaml
# Base Descriptor (abstract)
Descriptor:
  abstract: true
  slots:
    - preferred_term          # Human-readable name
    - description             # Optional elaboration
    - term                    # Optional ontology Term binding
    - modifier                # INCREASED|DECREASED|ABNORMAL|DYSREGULATED|ABSENT

# Specialized Descriptors
NutrientDescriptor:       # -> CHEBI
DiseaseDescriptor:        # -> MONDO
PhenotypeDescriptor:      # -> HP
BiologicalProcessDescriptor: # -> GO (biological_process)
AnatomicalEntityDescriptor:  # -> UBERON
FoodDescriptor:           # -> FOODON
DrugDescriptor:           # -> CHEBI (drug role) or DrugBank
GeneDescriptor:           # -> HGNC
```

### 1.3 Nested Complex Types

#### Function (biological roles)
```yaml
Function:
  slots:
    - name                    # "Cofactor for carboxylases"
    - description             # Detailed mechanism
    - biological_processes    # List[BiologicalProcessDescriptor]
    - cellular_components     # List[CellularComponentDescriptor]
    - genes                   # List[GeneDescriptor] - enzymes, transporters
    - downstream              # List[CausalEdge] - mechanistic links
    - evidence                # List[EvidenceItem]
```

#### Deficiency
```yaml
Deficiency:
  slots:
    - name                    # "Biotin Deficiency"
    - description
    - phenotypes              # List[Phenotype] - signs/symptoms with HP terms
    - at_risk_groups          # List[AtRiskGroup]
    - prevalence              # Prevalence info
    - causes                  # List[Cause] - why deficiency occurs
    - evidence
```

#### DiseaseAssociation
```yaml
DiseaseAssociation:
  slots:
    - name                    # "Biotin and Neural Tube Defects"
    - disease_term            # DiseaseDescriptor -> MONDO
    - relationship_type       # RISK_FACTOR|PROTECTIVE|THERAPEUTIC|MARKER
    - direction               # INCREASED|DECREASED|NULL
    - population_context      # e.g., "pregnant women"
    - mechanism               # List[Mechanism] - how nutrient affects disease
    - evidence
```

#### FoodSource
```yaml
FoodSource:
  slots:
    - name                    # "Egg yolk"
    - food_term               # FoodDescriptor -> FOODON
    - amount                  # Amount per serving
    - serving_size
    - bioavailability_notes
    - evidence
```

#### DrugInteraction
```yaml
DrugInteraction:
  slots:
    - name                    # "Anticonvulsants and Biotin"
    - drug_term               # DrugDescriptor
    - interaction_type        # REDUCES_ABSORPTION|INCREASES_EXCRETION|etc.
    - mechanism
    - clinical_significance   # HIGH|MODERATE|LOW
    - evidence
```

### 1.4 Evidence Structure (from dismech)

```yaml
EvidenceItem:
  slots:
    - reference               # PMID:12345678
    - supports                # SUPPORT|REFUTE|PARTIAL|NO_EVIDENCE|WRONG_STATEMENT
    - snippet                 # Exact verbatim quote from abstract
    - explanation             # Why this supports the claim

PublicationReference:
  slots:
    - reference               # PMID (identifier)
    - title                   # Paper title
    - findings                # List[Finding] - key claims from paper

Finding:
  slots:
    - statement               # Key claim
    - supporting_text         # Exact quote
```

### 1.5 Enums

```yaml
enums:
  RelationshipTypeEnum:
    permissible_values:
      RISK_FACTOR:
        description: Nutrient status affects disease risk
      PROTECTIVE:
        description: Higher nutrient status reduces risk
      THERAPEUTIC:
        description: Supplementation treats condition
      MARKER:
        description: Nutrient level indicates disease state
      COFACTOR:
        description: Required for enzyme function

  ModifierEnum:           # From dismech
    permissible_values:
      INCREASED: ...
      DECREASED: ...
      ABNORMAL: ...
      DYSREGULATED: ...
      ABSENT: ...

  InteractionTypeEnum:
    permissible_values:
      REDUCES_ABSORPTION: ...
      INCREASES_EXCRETION: ...
      COMPETES_FOR_TRANSPORT: ...
      SYNERGISTIC: ...
      ANTAGONISTIC: ...
```

---

## Phase 2: Content Extraction Pipeline

### 2.1 MIC Website as Research Source

Instead of AI deep research (like dismech), treat MIC pages as the authoritative research source:

```
MIC Page HTML
    ↓
Content Parser (BeautifulSoup)
    ↓
Structured Sections
    ↓
LLM Extraction (per section)
    ↓
YAML Output
```

### 2.2 Section-Based Extraction

The MIC website has consistent section structure:

| MIC Section | Schema Mapping |
|-------------|----------------|
| Summary | description |
| Function | functions |
| Deficiency | deficiency |
| Nutrient Interactions | nutrient_interactions |
| Drug Interactions | drug_interactions |
| Disease Prevention/Treatment | disease_associations, health_claims |
| Food Sources | food_sources |
| Safety | toxicity |
| Recommendations (RDA, AI) | recommendations |
| Authors and Reviewers | metadata |
| References | references |

### 2.3 Extraction Architecture

```python
# src/mic_ingest/extraction/
├── __init__.py
├── base.py              # BaseSectionExtractor
├── parser.py            # HTMLParser - section detection
├── sections/
│   ├── function.py      # FunctionExtractor
│   ├── deficiency.py    # DeficiencyExtractor
│   ├── disease.py       # DiseaseAssociationExtractor
│   ├── food.py          # FoodSourceExtractor
│   ├── interactions.py  # InteractionExtractor
│   ├── safety.py        # ToxicityExtractor
│   └── recommendations.py # RDAExtractor
├── grounding.py         # OntologyGrounder - entity linking
├── evidence.py          # EvidenceExtractor - PMID/snippet handling
└── pipeline.py          # Main orchestration
```

### 2.4 LLM Extraction Strategy

Use structured extraction prompts per section type:

```python
class FunctionExtractor(BaseSectionExtractor):
    """Extract biological functions from MIC Function section."""

    SYSTEM_PROMPT = """
    Extract biological functions of the nutrient from the provided text.
    For each function:
    1. Identify the function name and description
    2. List biological processes involved (for GO annotation)
    3. List genes/enzymes involved (for HGNC annotation)
    4. Note any downstream effects
    5. Include reference numbers for each claim

    Output as structured JSON matching the Function schema.
    """

    def extract(self, section_html: str, references: dict) -> List[Function]:
        # Parse section, call LLM, map references to PMIDs
        pass
```

### 2.5 Reference Handling

The MIC website uses numbered references that must be mapped to PMIDs:

```python
# Step 1: Extract reference list from HTML (existing fetch-references.py logic)
# Step 2: Map reference numbers to PMIDs
# Step 3: During extraction, resolve "ref 26" -> PMID:12345678
# Step 4: For snippets, prefer abstract text over MIC text (for validation)
```

---

## Phase 3: Ontology Grounding

### 3.1 Entity Linking Pipeline

```python
# src/mic_ingest/grounding/
├── __init__.py
├── base.py              # BaseGrounder
├── chebi.py             # NutrientGrounder -> CHEBI
├── mondo.py             # DiseaseGrounder -> MONDO
├── hp.py                # PhenotypeGrounder -> HP
├── go.py                # ProcessGrounder -> GO
├── foodon.py            # FoodGrounder -> FOODON
├── uberon.py            # AnatomyGrounder -> UBERON
├── hgnc.py              # GeneGrounder -> HGNC
└── composite.py         # CompositeGrounder - auto-dispatch
```

### 3.2 Grounding Strategy

Use OAK (Ontology Access Kit) for consistent grounding:

```python
from oaklib import get_adapter

class NutrientGrounder(BaseGrounder):
    def __init__(self):
        self.adapter = get_adapter("sqlite:obo:chebi")

    def ground(self, term: str) -> Optional[NutrientDescriptor]:
        # Search CHEBI for term
        # Return descriptor with CURIE and canonical label
        results = list(self.adapter.basic_search(term))
        if results:
            curie = results[0]
            label = self.adapter.label(curie)
            return NutrientDescriptor(
                preferred_term=term,
                term=Term(id=curie, label=label)
            )
        return NutrientDescriptor(preferred_term=term)  # Ungrounded
```

### 3.3 Caching

Cache ontology lookups to avoid repeated queries:

```python
# cache/ontology/
├── chebi_cache.json
├── mondo_cache.json
├── hp_cache.json
└── ...
```

---

## Phase 4: Validation Stack

### 4.1 Multi-Layer Validation (following dismech)

```
Layer 1: Schema Validation
├── linkml-validate: Structure, types, required fields
└── Config: src/mic_ingest/schema/mic.yaml

Layer 2: Ontology Term Validation
├── linkml-term-validator: Verify CURIEs exist
├── Check labels match canonical ontology labels
└── Config: conf/oak_config.yaml

Layer 3: Reference Validation
├── linkml-reference-validator: Verify snippets in abstracts
└── Config: conf/reference_validator.yaml

Layer 4: Compliance Analysis
├── linkml-data-qc: Measure field coverage
├── Weighted scoring for priority curation
└── Dashboard generation
```

### 4.2 OAK Configuration

```yaml
# conf/oak_config.yaml
adapters:
  CHEBI: sqlite:obo:chebi
  MONDO: sqlite:obo:mondo
  HP: sqlite:obo:hp
  GO: sqlite:obo:go
  UBERON: sqlite:obo:uberon
  FOODON: sqlite:obo:foodon
  HGNC: sqlite:obo:hgnc
```

### 4.3 Validation Commands

```bash
# Schema validation
just validate kb/nutrients/biotin.yaml

# Term validation (anti-hallucination)
just validate-terms

# Reference validation
just validate-references kb/nutrients/biotin.yaml

# Full QC pipeline
just qc

# Compliance dashboard
just compliance
```

---

## Phase 5: Output Structure

### 5.1 Knowledge Base Organization

```
kb/
├── nutrients/
│   ├── vitamins/
│   │   ├── biotin.yaml
│   │   ├── folate.yaml
│   │   ├── niacin.yaml
│   │   ├── pantothenic-acid.yaml
│   │   ├── riboflavin.yaml
│   │   ├── thiamin.yaml
│   │   ├── vitamin-a.yaml
│   │   ├── vitamin-b6.yaml
│   │   ├── vitamin-b12.yaml
│   │   ├── vitamin-c.yaml
│   │   ├── vitamin-d.yaml
│   │   ├── vitamin-e.yaml
│   │   └── vitamin-k.yaml
│   ├── minerals/
│   │   ├── calcium.yaml
│   │   ├── chromium.yaml
│   │   ├── copper.yaml
│   │   ├── fluoride.yaml
│   │   ├── iodine.yaml
│   │   ├── iron.yaml
│   │   ├── magnesium.yaml
│   │   ├── manganese.yaml
│   │   ├── molybdenum.yaml
│   │   ├── phosphorus.yaml
│   │   ├── potassium.yaml
│   │   ├── selenium.yaml
│   │   ├── sodium.yaml
│   │   └── zinc.yaml
│   ├── dietary-factors/
│   │   ├── alpha-lipoic-acid.yaml
│   │   ├── choline.yaml
│   │   ├── coenzyme-q10.yaml
│   │   ├── essential-fatty-acids.yaml
│   │   ├── fiber.yaml
│   │   ├── flavonoids.yaml
│   │   ├── indole-3-carbinol.yaml
│   │   ├── l-carnitine.yaml
│   │   └── ...
│   └── food-beverages/
│       ├── coffee.yaml
│       ├── cruciferous-vegetables.yaml
│       ├── garlic.yaml
│       ├── legumes.yaml
│       ├── nuts.yaml
│       ├── soy.yaml
│       ├── tea.yaml
│       └── ...
```

**Note**: No separate `conditions/` directory. Diseases are referenced via `disease_associations` in nutrient files (nutrient-centric approach).

### 5.2 Example YAML Output

```yaml
# kb/nutrients/vitamins/biotin.yaml
name: Biotin
nutrient_term:
  preferred_term: biotin
  term:
    id: CHEBI:15956
    label: biotin
alternate_names:
  - Vitamin B7
  - Vitamin H
  - Coenzyme R
category: vitamin
description: |
  Biotin is a water-soluble B vitamin that serves as a coenzyme for
  carboxylase enzymes involved in fatty acid synthesis, gluconeogenesis,
  and amino acid metabolism.
source_url: https://lpi.oregonstate.edu/mic/vitamins/biotin

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
      - preferred_term: gluconeogenesis
        term:
          id: GO:0006094
          label: gluconeogenesis
    genes:
      - preferred_term: PC
        description: Pyruvate carboxylase
        term:
          id: HGNC:8636
          label: PC
      - preferred_term: ACC1
        description: Acetyl-CoA carboxylase 1
        term:
          id: HGNC:84
          label: ACACA
    downstream:
      - target: Glucose Homeostasis
        description: Via gluconeogenesis regulation
    evidence:
      - reference: PMID:10357733
        supports: SUPPORT
        snippet: "Biotin serves as a covalently bound coenzyme for five mammalian carboxylases"
        explanation: Directly supports biotin's role as carboxylase cofactor

deficiency:
  name: Biotin Deficiency
  description: |
    Biotin deficiency is rare in healthy individuals consuming a varied diet.
    When it occurs, symptoms include dermatitis, alopecia, and neurological manifestations.
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
    - name: Alopecia
      phenotype_term:
        preferred_term: alopecia
        term:
          id: HP:0001596
          label: Alopecia
      frequency: FREQUENT
  at_risk_groups:
    - name: Pregnant women
      description: Marginal biotin deficiency common during pregnancy
      evidence:
        - reference: PMID:12117355
          supports: SUPPORT
          snippet: "marginal biotin deficiency may be relatively common during pregnancy"

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
    mechanism:
      - name: Biotin-dependent carboxylases in embryonic development
        description: |
          Biotin-dependent carboxylases are essential for normal embryonic
          development; deficiency may impair neural tube closure.
    evidence:
      - reference: PMID:16549401
        supports: SUPPORT
        snippet: "low biotin status during early pregnancy increases the risk of neural tube defects"

food_sources:
  - name: Egg yolk
    food_term:
      preferred_term: egg yolk
      term:
        id: FOODON:00002669
        label: egg yolk
    amount: "10 mcg"
    serving_size: "1 large egg"
  - name: Liver
    food_term:
      preferred_term: liver
      term:
        id: FOODON:00001082
        label: liver
    amount: "27-35 mcg"
    serving_size: "3 oz cooked"

drug_interactions:
  - name: Anticonvulsants and Biotin
    drug_term:
      preferred_term: anticonvulsant
      description: Including phenytoin, carbamazepine, primidone
    interaction_type: REDUCES_ABSORPTION
    mechanism:
      - name: Impaired intestinal absorption
        description: Anticonvulsants may inhibit biotin uptake in the intestine
    clinical_significance: MODERATE
    evidence:
      - reference: PMID:8157857
        supports: SUPPORT
        snippet: "long-term anticonvulsant therapy has been associated with reduced biotin status"

recommendations:
  rda:
    - population: adults
      amount: "30 mcg/day"
      source: Institute of Medicine
  ai:
    - population: infants
      amount: "5-6 mcg/day"
  ul:
    - population: adults
      amount: null  # No UL established
      notes: Insufficient data to establish UL

references:
  - reference: PMID:10357733
    title: "Biotin"
    findings:
      - statement: Biotin is a water-soluble B vitamin essential for carboxylase function
        supporting_text: "biotin serves as a covalently bound coenzyme for five mammalian carboxylases"
  - reference: PMID:12117355
    title: "Marginal biotin deficiency during normal pregnancy"
    findings:
      - statement: Marginal biotin deficiency is common during pregnancy
        supporting_text: "marginal biotin deficiency may be relatively common during pregnancy"
```

---

## Phase 6: Export & Rendering

### 6.1 HTML Rendering (following dismech)

```python
# src/mic_ingest/render.py
class NutrientRenderer:
    """Render nutrient YAML to browsable HTML."""

    def render(self, yaml_path: Path) -> Path:
        # Load YAML
        # Generate Jinja2 template
        # Create clickable ontology links
        # Include raw YAML display
        pass
```

### 6.2 Knowledge Graph Export

```python
# src/mic_ingest/export/
├── biolink.py           # Export to Biolink-compliant TSV/JSON
├── rdf.py               # Export to RDF/OWL
└── browser.py           # Export to faceted search JSON
```

### 6.3 Output Formats

| Format | Use Case |
|--------|----------|
| YAML | Primary storage, human-readable |
| HTML | Browsable website |
| TSV | Backward compatibility, KG integration |
| JSON | API, browser search |
| RDF | Semantic web integration |

---

## Phase 7: Implementation Roadmap

### Step 1: Schema Definition (Week 1)
- [ ] Design full LinkML schema
- [ ] Define all descriptor classes
- [ ] Define all nested complex types
- [ ] Create enums for controlled vocabularies
- [ ] Generate Python dataclasses

### Step 2: Content Parser (Week 2)
- [ ] HTML section parser for MIC pages
- [ ] Reference extractor (build on existing `fetch-references.py`)
- [ ] Section detection and isolation

### Step 3: Extraction Pipeline (Weeks 3-4)
- [ ] Base extractor class
- [ ] Section-specific extractors (function, deficiency, disease, etc.)
- [ ] LLM prompt templates per section
- [ ] Reference number to PMID mapping
- [ ] Evidence snippet extraction

### Step 4: Ontology Grounding (Week 5)
- [ ] OAK-based grounders per ontology
- [ ] Caching layer
- [ ] Confidence scoring for grounding

### Step 5: Validation Stack (Week 6)
- [ ] Schema validation setup
- [ ] Term validation configuration
- [ ] Reference validation integration
- [ ] Compliance analysis

### Step 6: Initial Extraction (Weeks 7-8)
- [ ] Extract 2-3 nutrients as proof of concept
- [ ] Refine prompts based on output quality
- [ ] Iterate on schema as needed

### Step 7: Full Extraction (Weeks 9-10)
- [ ] Extract all vitamins
- [ ] Extract all minerals
- [ ] Extract dietary factors
- [ ] Extract food/beverages

### Step 8: Export & Rendering (Week 11)
- [ ] HTML renderer with templates
- [ ] TSV/JSON exporters
- [ ] Static site generation

### Step 9: Quality Assurance (Week 12)
- [ ] Full validation pass
- [ ] Manual curation review
- [ ] Documentation

---

## Phase 8: Project Structure

```
mic-ingest/
├── src/mic_ingest/
│   ├── __init__.py
│   ├── cli.py                    # CLI entry points
│   ├── schema/
│   │   ├── mic.yaml              # LinkML schema
│   │   └── mic.py                # Generated dataclasses
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── parser.py
│   │   ├── pipeline.py
│   │   └── sections/
│   │       ├── __init__.py
│   │       ├── function.py
│   │       ├── deficiency.py
│   │       ├── disease.py
│   │       ├── food.py
│   │       ├── interactions.py
│   │       └── recommendations.py
│   ├── grounding/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── adapters/
│   │       ├── chebi.py
│   │       ├── mondo.py
│   │       └── ...
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── schema.py
│   │   ├── terms.py
│   │   └── references.py
│   ├── export/
│   │   ├── __init__.py
│   │   ├── biolink.py
│   │   ├── rdf.py
│   │   └── browser.py
│   ├── render/
│   │   ├── __init__.py
│   │   ├── renderer.py
│   │   └── templates/
│   │       └── nutrient.html.j2
│   └── utils/
│       ├── __init__.py
│       └── cache.py
├── conf/
│   ├── oak_config.yaml           # Ontology adapter config
│   └── extraction_config.yaml    # LLM/extraction settings
├── kb/
│   └── nutrients/
│       ├── vitamins/
│       ├── minerals/
│       ├── dietary-factors/
│       └── food-beverages/
├── pages/                        # Generated HTML
│   └── nutrients/
├── cache/
│   ├── ontology/                 # Cached ontology lookups
│   └── references/               # Cached PubMed abstracts
├── tests/
│   ├── test_schema.py
│   ├── test_extraction.py
│   ├── test_grounding.py
│   └── test_validation.py
├── scripts/
│   ├── extract_nutrient.py       # Single nutrient extraction
│   ├── extract_all.py            # Batch extraction
│   └── validate_all.py           # Batch validation
├── justfile                      # Task runner
├── pyproject.toml
└── README.md
```

---

## Phase 9: Dependencies

```toml
# pyproject.toml additions
[tool.poetry.dependencies]
python = ">=3.10,<3.13"

# LinkML ecosystem
linkml = ">=1.9.3"
linkml-runtime = ">=1.9.4"
linkml-data-qc = "*"              # Compliance analysis
linkml-term-validator = "*"        # Ontology term validation
linkml-reference-validator = "*"   # Reference snippet validation

# Ontology access
oaklib = ">=0.6.0"                # Ontology Access Kit

# LLM extraction
openai = ">=1.0.0"                # Or anthropic, litellm
instructor = "*"                  # Structured output extraction

# Web/parsing
beautifulsoup4 = ">=4.12.0"
requests = ">=2.31.0"
lxml = "*"

# Data handling
pyyaml = ">=6.0"
pydantic = ">=2.0"

# Rendering
jinja2 = ">=3.0"

# Existing (keep)
koza = ">=0.6.0"
biolink-model = "^4.2.0"
```

---

## Key Design Decisions

### 1. Schema-First Approach
The LinkML schema is the single source of truth. Python dataclasses are generated from it, ensuring type safety and validation.

### 2. Nested vs Flat Structure
Moving from flat relationships (`NutrientToDiseaseRelationship`) to nested structures (`Nutrient.disease_associations[]`) provides:
- Better organization per nutrient
- Richer context capture
- Easier human review
- More natural YAML representation

### 3. Evidence Requirements
Every claim must have evidence with:
- PMID reference
- Support classification
- Verbatim snippet (validated against PubMed)
- Explanation

This prevents hallucination and ensures traceability.

### 4. MIC as Research Source
The MIC website is treated as the curated research source (analogous to dismech's deep research output). This is appropriate because:
- MIC is already expert-curated
- Contains structured sections
- Includes references to primary literature
- Updated periodically by domain experts

### 5. Section-Based Extraction
Extracting per MIC section (rather than whole page) provides:
- Better extraction quality
- Easier debugging
- Natural mapping to schema sections
- Ability to use specialized prompts

### 6. Backward Compatibility
TSV export maintains compatibility with existing KG integration pipelines while the primary storage moves to YAML.

---

## Success Metrics

1. **Schema Coverage**: All MIC content types representable in schema
2. **Extraction Quality**: >90% of claims properly grounded to ontologies
3. **Evidence Validity**: 100% of snippets pass reference validation
4. **Compliance Score**: >80% field coverage per nutrient
5. **Human Review**: Curators can easily verify and correct entries

---

## Phase 10: Claude-Centric Workflow

### 10.1 Design Philosophy

The curation workflow is **Claude-centric**: Claude Code is the primary interface for creating,
editing, and validating nutrient YAML files. This follows the dismech pattern where Claude skills
guide the workflow and hooks enforce validation.

Key principles:
- **Claude as curator**: Claude extracts from MIC pages, grounds to ontologies, adds evidence
- **Skills as workflows**: Detailed step-by-step instructions for specific tasks
- **Hooks as guardrails**: Pre-edit validation prevents invalid YAML from being written
- **Agent-API for batch**: Use Claude agent-api to loop through all nutrients programmatically

### 10.2 Claude Skills

Create skills in `.claude/skills/` modeled after dismech:

#### mic-ingest-nutrient-creation (Primary Skill)
```markdown
---
name: mic-ingest-nutrient-creation
description: >
  Skill for creating new nutrient YAML files from MIC website content.
  Use this when extracting a nutrient from lpi.oregonstate.edu/mic.
---

# MIC Nutrient Extraction Skill

## Workflow

### Step 1: Fetch MIC Page
Fetch the MIC page for the nutrient:
```bash
just fetch-mic-page vitamins/biotin
```

This downloads the HTML and extracts references with PMIDs.

### Step 2: Create Initial YAML
Create kb/nutrients/{category}/{nutrient}.yaml with basic structure:

```yaml
name: Biotin
nutrient_term:
  preferred_term: biotin
  term:
    id: CHEBI:15956
    label: biotin
category: vitamin
source_url: https://lpi.oregonstate.edu/mic/vitamins/biotin
# ... sections to populate
```

### Step 3: Extract Section by Section
For each MIC section, read the cached HTML and extract structured data:
- functions: Biological roles, GO processes, genes
- deficiency: Phenotypes with HP terms, at-risk groups
- disease_associations: MONDO terms, relationship types
- food_sources: FOODON terms, amounts
- drug_interactions: Clinical significance
- recommendations: RDA, AI, UL values

### Step 4: Ground to Ontologies
Use OAK to find correct ontology terms:
```bash
uv run runoak -i sqlite:obo:chebi info "biotin"
uv run runoak -i sqlite:obo:hp info "l~dermatitis"
uv run runoak -i sqlite:obo:go info "l~fatty acid biosynthesis"
```

### Step 5: Add Evidence
For each claim, add evidence with real PMIDs:
```yaml
evidence:
  - reference: PMID:12345678
    supports: SUPPORT
    snippet: "Exact quote from abstract"
    explanation: "Why this supports the claim"
```

Fetch abstracts for validation:
```bash
just fetch-reference PMID:12345678
```

### Step 6: Validate
```bash
just validate kb/nutrients/vitamins/biotin.yaml
just validate-terms-file kb/nutrients/vitamins/biotin.yaml
just validate-references kb/nutrients/vitamins/biotin.yaml
```
```

#### mic-terms (Ontology Term Skill)
```markdown
---
name: mic-terms
description: >
  Skill for adding ontology term annotations to nutrient YAML files.
  Covers CHEBI, FOODON, HP, GO, MONDO, UBERON, HGNC lookups.
---

# MIC Ontology Terms Skill

## Ontology Mappings

| Entity Type | Ontology | Adapter |
|-------------|----------|---------|
| Nutrients | CHEBI | sqlite:obo:chebi |
| Foods | FOODON | sqlite:obo:foodon |
| Phenotypes | HP | sqlite:obo:hp |
| Biological Processes | GO | sqlite:obo:go |
| Diseases | MONDO | sqlite:obo:mondo |
| Anatomy | UBERON | sqlite:obo:uberon |
| Genes | HGNC | sqlite:obo:hgnc |

## OAK Commands

### Fuzzy Search
```bash
uv run runoak -i sqlite:obo:hp info "l~cognitive impairment"
```

### Exact Lookup
```bash
uv run runoak -i sqlite:obo:chebi info CHEBI:15956
```

### Validate Labels Match
The label in YAML must exactly match the ontology's canonical label.
```

#### mic-references (Evidence Skill)
```markdown
---
name: mic-references
description: >
  Skill for validating evidence references. Ensures snippets
  match PubMed abstracts and catches hallucinations.
---

# MIC Reference Validation Skill

## Evidence Structure
All evidence items require:
- reference: PMID:12345678
- supports: SUPPORT | REFUTE | PARTIAL | NO_EVIDENCE | WRONG_STATEMENT
- snippet: "Exact verbatim quote from abstract"
- explanation: "Why this evidence supports the claim"

## Validation Commands
```bash
just validate-references kb/nutrients/vitamins/biotin.yaml
```

## Anti-Hallucination Rules
- NEVER fabricate PMIDs
- NEVER paraphrase snippets
- Always fetch and verify abstracts before adding evidence
```

#### mic-compliance (Compliance Skill)
```markdown
---
name: mic-compliance
description: >
  Skill for analyzing completeness of nutrient YAML files.
---

# MIC Compliance Analysis Skill

## Commands
```bash
just compliance kb/nutrients/vitamins/biotin.yaml
just compliance-all
just gen-dashboard
```

## Priority Fields (by weight)
1. nutrient_term.term (5.0) - Always required
2. disease_associations[].disease_term.term (3.0)
3. deficiency.phenotypes[].phenotype_term.term (3.0)
4. functions[].biological_processes[].term (2.5)
5. evidence items (2.0)
```

### 10.3 Claude Commands

Create commands in `.claude/commands/`:

#### /curate-nutrient
```markdown
---
description: Curate a nutrient from the MIC website
argument-hint: [NUTRIENT_NAME] [CATEGORY]
---

Curate the nutrient specified in $ARGUMENTS.

IMPORTANT: Consult the mic-ingest-nutrient-creation skill for detailed workflow.

Steps:
1. Fetch MIC page content
2. Create or update the nutrient YAML file
3. Extract all sections
4. Ground entities to ontologies
5. Add evidence with real PMIDs
6. Validate before committing
```

#### /validate-all
```markdown
---
description: Run full QC on all nutrient files
---

Run the complete validation pipeline:
```bash
just qc
```
```

### 10.4 Pre-Edit Validation Hook

Create `.claude/hooks/validate_nutrient_hook.py` (adapted from dismech):

```python
#!/usr/bin/env python3
"""
PreToolUse hook to validate kb/nutrients/**/*.yaml files BEFORE edits.

Intercepts Edit/Write calls, simulates the edit, runs validation,
and blocks (exit 2) if validation fails.
"""

import sys
import json
import subprocess
import tempfile
from pathlib import Path

def main():
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        sys.exit(0)

    file_path = Path(tool_input.get("file_path", ""))

    # Only validate kb/nutrients/**/*.yaml
    if "kb/nutrients" not in str(file_path) or file_path.suffix != ".yaml":
        sys.exit(0)

    # Simulate edit and validate...
    # (Same pattern as dismech)

if __name__ == "__main__":
    main()
```

### 10.5 Agent-API Batch Processing

For processing all nutrients, use Claude agent-api to loop:

```python
#!/usr/bin/env python3
"""
Batch process all MIC nutrients using Claude agent-api.
"""

from anthropic import Anthropic
import yaml

# List of nutrients to process
NUTRIENTS = [
    ("vitamins", "biotin"),
    ("vitamins", "folate"),
    ("vitamins", "vitamin-c"),
    # ... all nutrients
]

client = Anthropic()

for category, nutrient in NUTRIENTS:
    print(f"Processing {category}/{nutrient}...")

    # Create a conversation to curate this nutrient
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system="You are curating nutrients for the MIC knowledge base. Use the mic-ingest-nutrient-creation skill.",
        messages=[
            {"role": "user", "content": f"/curate-nutrient {nutrient} {category}"}
        ],
        # Enable tool use for file operations, bash, etc.
    )

    # Continue conversation until nutrient is complete
    # ...
```

This enables:
- Automated processing of all ~50 nutrients
- Consistent application of the workflow
- Human review of outputs afterward

### 10.6 Claude Settings

`.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validate_nutrient_hook.py"
          }
        ]
      }
    ]
  }
}
```

---

## Phase 11: KGX/Biolink Edge Export (Deferred)

### 11.1 Design

After YAML files exist, export flat Biolink/KGX edges:

```python
# src/mic_ingest/export/kgx.py
from biolink_model.datamodel.pydanticmodel_v2 import (
    ChemicalEntity,
    Disease,
    PhenotypicFeature,
    ChemicalToDiseaseOrPhenotypicFeatureAssociation,
)

def export_to_kgx(nutrient_yaml: Path) -> Tuple[List[Entity], List[Association]]:
    """
    Export nutrient YAML to Biolink Pydantic objects, then serialize to KGX.

    Uses biolink-model Pydantic classes for type-safe edge generation.

    Produces edges like:
    - CHEBI:15956 (biotin) --biolink:participates_in--> GO:0006633 (fatty acid biosynthesis)
    - CHEBI:15956 (biotin) --biolink:treats--> MONDO:0005343 (neural tube defect)
    - CHEBI:15956 (biotin) --biolink:causes--> HP:0001596 (Alopecia) [deficiency context]
    """
    pass
```

### 11.2 Biolink Pydantic Classes

Use the official `biolink-model` Pydantic classes for type-safe KGX generation:

```python
from biolink_model.datamodel.pydanticmodel_v2 import (
    # Nodes
    ChemicalEntity,           # For nutrients (CHEBI)
    Food,                     # For food sources (FOODON)
    Disease,                  # For disease associations (MONDO)
    PhenotypicFeature,        # For deficiency phenotypes (HP)
    BiologicalProcess,        # For functions (GO)
    Gene,                     # For genes/enzymes (HGNC)
    Drug,                     # For drug interactions

    # Edges
    ChemicalToDiseaseOrPhenotypicFeatureAssociation,
    ChemicalToGeneAssociation,
    ChemicalToPathwayAssociation,
    # etc.
)
```

This ensures:
- Type-safe edge construction
- Correct Biolink categories and predicates
- Consistent with Monarch KG standards

### 11.3 Koza Enhancement (Potential)

Currently Koza expects TSV input. For this use case (and dismech), we may want to
extend Koza to support **YAML file collections** as input:

```yaml
# Proposed: koza transform config for YAML input
source:
  type: yaml_collection
  path: kb/nutrients/**/*.yaml
  schema: src/mic_ingest/schema/mic.yaml
  target_class: Nutrient

transform:
  - nutrient_to_disease_edges.py
  - nutrient_to_phenotype_edges.py
  - nutrient_to_process_edges.py
```

Benefits:
- Direct transformation from nested YAML to KGX
- Reusable for dismech (disorders → KGX)
- No intermediate TSV step needed
- Schema-aware traversal of nested structures

This would be a contribution back to Koza that benefits both projects.

### 11.4 Output Format

Standard KGX TSV:
```
nodes.tsv: id, category, name, ...
edges.tsv: subject, predicate, object, primary_knowledge_source, ...
```

### 11.5 Timeline

This is **deferred** until YAML files exist. The priority order is:
1. Schema design
2. Claude skills/hooks setup
3. Extract one nutrient as proof of concept
4. Refine and extract all nutrients
5. Then implement KGX export (with Biolink Pydantic + potential Koza enhancement)

---

## Resolved Design Decisions

Based on discussion:

| Question | Decision |
|----------|----------|
| **LLM Choice** | Claude-specific. Use Claude Code for interactive curation, agent-api for batch. |
| **Health-Disease** | Nutrient-centric only. No separate condition files; diseases referenced via `disease_associations` in nutrient files. |
| **Curation Workflow** | Claude-centric with skills, commands, and hooks. Agent-api for batch processing. |
| **Update Strategy** | Deferred. May use git releases for diffing. Initial focus is one-time annotation. |
| **KGX Export** | Deferred until YAML files exist. Will produce flat Biolink edges from nested YAML. |

---

## Implementation Priority

### Phase A: Foundation (First)
1. Create LinkML schema
2. Set up project structure
3. Create Claude skills and hooks
4. Add justfile commands

### Phase B: Proof of Concept
1. Extract one nutrient (e.g., Biotin) manually with Claude
2. Validate full workflow
3. Refine schema based on real data
4. Refine skills based on experience

### Phase C: Batch Extraction
1. Set up agent-api loop
2. Process all vitamins
3. Process all minerals
4. Process dietary factors
5. Process food/beverages

### Phase D: Export & Polish
1. Implement KGX export
2. Generate HTML pages
3. Run full QC
4. Documentation
