"""Tests for KGX edge and node exporter."""

import pytest

pytest.importorskip("biolink_model", reason="biolink-model not installed (install with: uv sync --group export)")

from biolink_model.datamodel.pydanticmodel_v2 import (
    AnatomicalEntity,
    Association,
    BiologicalProcess,
    CellularComponent,
    ChemicalAffectsBiologicalEntityAssociation,
    ChemicalEntity,
    ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation,
    Disease,
    Food,
    Gene,
    PhenotypicFeature,
    PhenotypicFeatureToPhenotypicFeatureAssociation,
)

from mic_ingest.export.kgx_export import (
    KNOWLEDGE_SOURCE,
    biological_process_to_edge,
    cellular_component_to_edge,
    deficiency_sequela_to_edge,
    deficiency_state_to_edge,
    drug_interaction_to_edge,
    extract_nodes,
    food_source_to_edge,
    gene_to_edge,
    location_to_edge,
    marker_to_edge,
    nutrient_interaction_to_edge,
    protective_to_edge,
    risk_factor_to_edge,
    therapeutic_to_edge,
    toxicity_sequela_to_edge,
    toxicity_state_to_edge,
    transform,
)


NUTRIENT_ID = "CHEBI:15956"  # biotin


def _evidence(pmid: str = "PMID:12345678", snippet: str = "Test snippet."):
    """Build a minimal evidence list with a PMID and snippet."""
    return [{"reference": pmid, "supports": "SUPPORT", "snippet": snippet}]


class TestTherapeuticToEdge:
    """Tests for therapeutic_to_edge function."""

    def test_valid_therapeutic(self):
        """Test with a complete THERAPEUTIC disease association."""
        da = {
            "name": "Biotinidase Deficiency",
            "disease_term": {
                "preferred_term": "biotinidase deficiency",
                "term": {"id": "MONDO:0009665", "label": "biotinidase deficiency"},
            },
            "relationship_type": "THERAPEUTIC",
            "evidence": _evidence(),
        }
        edge = therapeutic_to_edge(NUTRIENT_ID, da)
        assert isinstance(edge, ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:treats_or_applied_or_studied_to_treat"
        assert edge.object == "MONDO:0009665"
        assert edge.subject_category == "biolink:ChemicalEntity"
        assert edge.object_category == "biolink:Disease"
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_evidence(self):
        """Test that an edge without evidence is not produced."""
        da = {
            "disease_term": {
                "term": {"id": "MONDO:0009665", "label": "biotinidase deficiency"},
            },
            "relationship_type": "THERAPEUTIC",
        }
        assert therapeutic_to_edge(NUTRIENT_ID, da) is None

    def test_missing_term_id(self):
        """Test with disease_term but no term.id."""
        da = {
            "disease_term": {"preferred_term": "some disease"},
        }
        assert therapeutic_to_edge(NUTRIENT_ID, da) is None

    def test_none_input(self):
        """Test with None disease_term."""
        da = {"name": "No term"}
        assert therapeutic_to_edge(NUTRIENT_ID, da) is None


class TestProtectiveToEdge:
    """Tests for protective_to_edge function."""

    def test_valid_protective(self):
        """Test with a complete PROTECTIVE disease association."""
        da = {
            "disease_term": {
                "preferred_term": "type 2 diabetes",
                "term": {"id": "MONDO:0005148", "label": "type 2 diabetes mellitus"},
            },
            "relationship_type": "PROTECTIVE",
            "direction": "DECREASED",
            "evidence": _evidence(),
        }
        edge = protective_to_edge(NUTRIENT_ID, da)
        assert isinstance(edge, ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:preventative_for_condition"
        assert edge.object == "MONDO:0005148"
        assert "direction:decreased" in edge.qualifiers
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_term_id(self):
        """Test with missing term.id."""
        da = {"disease_term": {"preferred_term": "some disease"}}
        assert protective_to_edge(NUTRIENT_ID, da) is None

    def test_none_input(self):
        """Test with no disease_term."""
        assert protective_to_edge(NUTRIENT_ID, {}) is None


class TestRiskFactorToEdge:
    """Tests for risk_factor_to_edge function."""

    def test_valid_risk_factor(self):
        """Test with a complete RISK_FACTOR disease association."""
        da = {
            "disease_term": {
                "preferred_term": "congenital anomaly",
                "term": {"id": "MONDO:0000839", "label": "congenital anomaly"},
            },
            "relationship_type": "RISK_FACTOR",
            "direction": "DECREASED",
            "evidence": _evidence(),
        }
        edge = risk_factor_to_edge(NUTRIENT_ID, da)
        assert isinstance(edge, Association)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:affects_likelihood_of"
        assert edge.object == "MONDO:0000839"
        assert "direction:decreased" in edge.qualifiers
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_term_id(self):
        """Test with missing term.id."""
        da = {"disease_term": {"preferred_term": "some disease"}}
        assert risk_factor_to_edge(NUTRIENT_ID, da) is None

    def test_none_input(self):
        """Test with no disease_term."""
        assert risk_factor_to_edge(NUTRIENT_ID, {}) is None


class TestMarkerToEdge:
    """Tests for marker_to_edge function."""

    def test_valid_marker(self):
        """Test with a complete MARKER disease association."""
        da = {
            "disease_term": {
                "preferred_term": "some disease",
                "term": {"id": "MONDO:0000001", "label": "some disease"},
            },
            "relationship_type": "MARKER",
            "evidence": _evidence(),
        }
        edge = marker_to_edge(NUTRIENT_ID, da)
        assert isinstance(edge, Association)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:biomarker_for"
        assert edge.object == "MONDO:0000001"
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_term_id(self):
        """Test with missing term.id."""
        da = {"disease_term": {"preferred_term": "some disease"}}
        assert marker_to_edge(NUTRIENT_ID, da) is None

    def test_none_input(self):
        """Test with no disease_term."""
        assert marker_to_edge(NUTRIENT_ID, {}) is None


class TestDeficiencyStateToEdge:
    """Tests for deficiency_state_to_edge function."""

    def test_valid_deficiency_state(self):
        """Test chemical → deficiency phenotype edge."""
        deficiency = {
            "phenotype_term": {
                "preferred_term": "Decreased circulating biotin concentration",
                "term": {"id": "HP:0034599", "label": "Decreased circulating biotin concentration"},
            },
            "evidence": _evidence(),
        }
        edge = deficiency_state_to_edge(NUTRIENT_ID, deficiency)
        assert isinstance(edge, ChemicalAffectsBiologicalEntityAssociation)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:affects"
        assert edge.qualified_predicate == "biolink:causes"
        assert edge.object == "HP:0034599"
        assert edge.subject_category == "biolink:ChemicalEntity"
        assert edge.object_category == "biolink:PhenotypicFeature"
        assert edge.subject_aspect_qualifier == "abundance"
        assert edge.subject_direction_qualifier == "decreased"
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_phenotype_term(self):
        """Test with no phenotype_term returns None."""
        deficiency = {"name": "Biotin Deficiency"}
        assert deficiency_state_to_edge(NUTRIENT_ID, deficiency) is None

    def test_missing_term_id(self):
        """Test with phenotype_term but no term.id."""
        deficiency = {"phenotype_term": {"preferred_term": "some deficiency"}}
        assert deficiency_state_to_edge(NUTRIENT_ID, deficiency) is None


class TestDeficiencySequelaToEdge:
    """Tests for deficiency_sequela_to_edge function."""

    def test_valid_with_disease_context(self):
        """Test deficiency phenotype → consequence phenotype with disease context."""
        sequela = {
            "name": "Alopecia",
            "phenotype_term": {
                "preferred_term": "alopecia",
                "term": {"id": "HP:0001596", "label": "Alopecia"},
            },
            "frequency": "FREQUENT",
            "evidence": _evidence(),
        }
        edge = deficiency_sequela_to_edge("HP:0034599", sequela, "MONDO:0000461")
        assert isinstance(edge, PhenotypicFeatureToPhenotypicFeatureAssociation)
        assert edge.subject == "HP:0034599"
        assert edge.predicate == "biolink:causes"
        assert edge.object == "HP:0001596"
        assert edge.subject_category == "biolink:PhenotypicFeature"
        assert edge.object_category == "biolink:PhenotypicFeature"
        assert edge.disease_context_qualifier == "MONDO:0000461"
        assert edge.frequency_qualifier == "HP:0040282"
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_valid_without_disease_context(self):
        """Test deficiency phenotype → consequence phenotype without disease context."""
        sequela = {
            "name": "Alopecia",
            "phenotype_term": {
                "term": {"id": "HP:0001596", "label": "Alopecia"},
            },
            "evidence": _evidence(),
        }
        edge = deficiency_sequela_to_edge("HP:0034599", sequela)
        assert isinstance(edge, PhenotypicFeatureToPhenotypicFeatureAssociation)
        assert edge.subject == "HP:0034599"
        assert edge.predicate == "biolink:causes"
        assert edge.object == "HP:0001596"
        assert edge.disease_context_qualifier is None
        assert edge.frequency_qualifier is None

    def test_missing_term_id(self):
        """Test with phenotype_term but no term.id."""
        sequela = {"phenotype_term": {"preferred_term": "alopecia"}}
        assert deficiency_sequela_to_edge("HP:0034599", sequela) is None

    def test_no_phenotype_term(self):
        """Test with no phenotype_term."""
        sequela = {"name": "Alopecia"}
        assert deficiency_sequela_to_edge("HP:0034599", sequela) is None


class TestToxicityStateToEdge:
    """Tests for toxicity_state_to_edge function."""

    def test_valid_toxicity_state(self):
        """Test chemical → toxicity phenotype edge."""
        toxicity = {
            "phenotype_term": {
                "preferred_term": "Increased circulating selenium concentration",
                "term": {"id": "HP:0032348", "label": "Increased circulating selenium concentration"},
            },
            "evidence": _evidence(),
        }
        edge = toxicity_state_to_edge(NUTRIENT_ID, toxicity)
        assert isinstance(edge, ChemicalAffectsBiologicalEntityAssociation)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:affects"
        assert edge.qualified_predicate == "biolink:causes"
        assert edge.object == "HP:0032348"
        assert edge.subject_aspect_qualifier == "abundance"
        assert edge.subject_direction_qualifier == "increased"
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_phenotype_term(self):
        """Test with no phenotype_term returns None."""
        toxicity = {"name": "Some Toxicity"}
        assert toxicity_state_to_edge(NUTRIENT_ID, toxicity) is None


class TestToxicitySequelaToEdge:
    """Tests for toxicity_sequela_to_edge function."""

    def test_valid_sequela(self):
        """Test toxicity phenotype → consequence phenotype edge."""
        sequela = {
            "name": "Nausea",
            "phenotype_term": {
                "preferred_term": "nausea",
                "term": {"id": "HP:0002018", "label": "Nausea"},
            },
            "frequency": "FREQUENT",
            "evidence": _evidence(),
        }
        edge = toxicity_sequela_to_edge("HP:0032348", sequela)
        assert isinstance(edge, PhenotypicFeatureToPhenotypicFeatureAssociation)
        assert edge.subject == "HP:0032348"
        assert edge.predicate == "biolink:causes"
        assert edge.object == "HP:0002018"
        assert edge.frequency_qualifier == "HP:0040282"
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_term_id(self):
        """Test with missing term.id."""
        sequela = {"phenotype_term": {"preferred_term": "nausea"}}
        assert toxicity_sequela_to_edge("HP:0032348", sequela) is None

    def test_no_phenotype_term(self):
        """Test with no phenotype_term."""
        sequela = {"name": "Nausea"}
        assert toxicity_sequela_to_edge("HP:0032348", sequela) is None


class TestBiologicalProcessToEdge:
    """Tests for biological_process_to_edge function."""

    def test_valid_process(self):
        """Test with a complete biological process entry."""
        process = {
            "preferred_term": "fatty acid biosynthetic process",
            "term": {"id": "GO:0006633", "label": "fatty acid biosynthetic process"},
        }
        edge = biological_process_to_edge(NUTRIENT_ID, process, _evidence())
        assert isinstance(edge, Association)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:participates_in"
        assert edge.object == "GO:0006633"
        assert edge.subject_category == "biolink:ChemicalEntity"
        assert edge.object_category == "biolink:BiologicalProcess"
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_term_id(self):
        """Test with missing term.id."""
        process = {"preferred_term": "fatty acid biosynthetic process"}
        assert biological_process_to_edge(NUTRIENT_ID, process) is None


class TestGeneToEdge:
    """Tests for gene_to_edge function."""

    def test_valid_gene(self):
        """Test with a complete gene entry."""
        gene = {
            "preferred_term": "ACACA",
            "term": {"id": "HGNC:93", "label": "ACACA"},
        }
        edge = gene_to_edge(NUTRIENT_ID, gene, _evidence())
        assert isinstance(edge, Association)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:affects"
        assert edge.object == "HGNC:93"
        assert edge.subject_category == "biolink:ChemicalEntity"
        assert edge.object_category == "biolink:Gene"
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_term_id(self):
        """Test with missing term.id."""
        gene = {"preferred_term": "ACACA"}
        assert gene_to_edge(NUTRIENT_ID, gene) is None

    def test_none_gene(self):
        """Test with None gene."""
        assert gene_to_edge(NUTRIENT_ID, None) is None


class TestCellularComponentToEdge:
    """Tests for cellular_component_to_edge function."""

    def test_valid_component(self):
        """Test with a complete cellular component entry."""
        component = {
            "preferred_term": "mitochondrion",
            "term": {"id": "GO:0005739", "label": "mitochondrion"},
        }
        edge = cellular_component_to_edge(NUTRIENT_ID, component, _evidence())
        assert isinstance(edge, Association)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:has_participant"
        assert edge.object == "GO:0005739"
        assert edge.object_category == "biolink:CellularComponent"

    def test_missing_term_id(self):
        """Test with missing term.id."""
        component = {"preferred_term": "mitochondrion"}
        assert cellular_component_to_edge(NUTRIENT_ID, component) is None


class TestLocationToEdge:
    """Tests for location_to_edge function."""

    def test_valid_location(self):
        """Test with a complete location entry."""
        location = {
            "preferred_term": "liver",
            "term": {"id": "UBERON:0002107", "label": "liver"},
        }
        edge = location_to_edge(NUTRIENT_ID, location, _evidence())
        assert isinstance(edge, Association)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:active_in"
        assert edge.object == "UBERON:0002107"
        assert edge.object_category == "biolink:AnatomicalEntity"

    def test_missing_term_id(self):
        """Test with missing term.id."""
        location = {"preferred_term": "liver"}
        assert location_to_edge(NUTRIENT_ID, location) is None


class TestFoodSourceToEdge:
    """Tests for food_source_to_edge function."""

    def test_valid_food_source(self):
        """Test with a complete food source entry."""
        food = {
            "name": "Liver, cooked",
            "food_term": {
                "preferred_term": "liver",
                "term": {"id": "FOODON:03301296", "label": "cooked liver"},
            },
            "evidence": _evidence(),
        }
        edge = food_source_to_edge(NUTRIENT_ID, food)
        assert isinstance(edge, Association)
        # Food is subject, nutrient is object
        assert edge.subject == "FOODON:03301296"
        assert edge.predicate == "biolink:has_nutrient"
        assert edge.object == NUTRIENT_ID
        assert edge.subject_category == "biolink:Food"
        assert edge.object_category == "biolink:ChemicalEntity"
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_food_term_id(self):
        """Test with food_term but no term.id (common case)."""
        food = {
            "name": "Liver, cooked",
            "food_term": {"preferred_term": "liver"},
        }
        assert food_source_to_edge(NUTRIENT_ID, food) is None

    def test_none_input(self):
        """Test with no food_term."""
        food = {"name": "Liver, cooked"}
        assert food_source_to_edge(NUTRIENT_ID, food) is None


class TestNutrientInteractionToEdge:
    """Tests for nutrient_interaction_to_edge function."""

    def test_valid_interaction(self):
        """Test with a complete nutrient interaction entry."""
        interaction = {
            "name": "Pantothenic Acid Competition",
            "nutrient_term": {
                "preferred_term": "pantothenic acid",
                "term": {"id": "CHEBI:7916", "label": "pantothenic acid"},
            },
            "evidence": _evidence(),
        }
        edge = nutrient_interaction_to_edge(NUTRIENT_ID, interaction)
        assert isinstance(edge, Association)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:interacts_with"
        assert edge.object == "CHEBI:7916"
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_term_id(self):
        """Test with missing term.id."""
        interaction = {
            "nutrient_term": {"preferred_term": "pantothenic acid"},
        }
        assert nutrient_interaction_to_edge(NUTRIENT_ID, interaction) is None

    def test_none_input(self):
        """Test with no nutrient_term."""
        interaction = {"name": "Some Interaction"}
        assert nutrient_interaction_to_edge(NUTRIENT_ID, interaction) is None


class TestDrugInteractionToEdge:
    """Tests for drug_interaction_to_edge function."""

    def test_valid_interaction(self):
        """Test with a complete drug interaction entry."""
        interaction = {
            "name": "Anticonvulsants and Biotin",
            "drug_term": {
                "preferred_term": "anticonvulsant",
                "term": {"id": "CHEBI:35623", "label": "anticonvulsant"},
            },
            "evidence": _evidence(),
        }
        edge = drug_interaction_to_edge(NUTRIENT_ID, interaction)
        assert isinstance(edge, Association)
        assert edge.subject == NUTRIENT_ID
        assert edge.predicate == "biolink:interacts_with"
        assert edge.object == "CHEBI:35623"
        assert edge.primary_knowledge_source == KNOWLEDGE_SOURCE

    def test_missing_term_id(self):
        """Test with missing term.id."""
        interaction = {
            "drug_term": {"preferred_term": "anticonvulsant"},
        }
        assert drug_interaction_to_edge(NUTRIENT_ID, interaction) is None

    def test_none_input(self):
        """Test with no drug_term."""
        interaction = {"name": "Some Drug"}
        assert drug_interaction_to_edge(NUTRIENT_ID, interaction) is None


class TestTransform:
    """Tests for the full transform function."""

    @pytest.fixture
    def sample_nutrient(self):
        """Create a sample nutrient with all edge types."""
        return {
            "name": "Test Nutrient",
            "nutrient_term": {
                "preferred_term": "test nutrient",
                "term": {"id": "CHEBI:00001", "label": "test nutrient"},
            },
            "disease_associations": [
                {
                    "name": "Disease A",
                    "disease_term": {
                        "term": {"id": "MONDO:0000001", "label": "Disease A"},
                    },
                    "relationship_type": "THERAPEUTIC",
                    "evidence": _evidence(),
                },
                {
                    "name": "Disease B",
                    "disease_term": {
                        "term": {"id": "MONDO:0000002", "label": "Disease B"},
                    },
                    "relationship_type": "PROTECTIVE",
                    "evidence": _evidence(),
                },
                {
                    "name": "Disease C",
                    "disease_term": {
                        "term": {"id": "MONDO:0000003", "label": "Disease C"},
                    },
                    "relationship_type": "RISK_FACTOR",
                    "direction": "DECREASED",
                    "evidence": _evidence(),
                },
                {
                    "name": "Disease D",
                    "disease_term": {
                        "term": {"id": "MONDO:0000004", "label": "Disease D"},
                    },
                    "relationship_type": "MARKER",
                    "evidence": _evidence(),
                },
            ],
            "deficiency": {
                "phenotype_term": {
                    "preferred_term": "Decreased circulating test concentration",
                    "term": {"id": "HP:0099999", "label": "Decreased circulating test concentration"},
                },
                "disease_term": {
                    "preferred_term": "test deficiency",
                    "term": {"id": "MONDO:0099999", "label": "test deficiency"},
                },
                "evidence": _evidence(),
                "sequelae": [
                    {
                        "name": "Phenotype A",
                        "phenotype_term": {
                            "term": {"id": "HP:0000001", "label": "Phenotype A"},
                        },
                        "frequency": "FREQUENT",
                        "evidence": _evidence(),
                    },
                ],
            },
            "toxicity": {
                "phenotype_term": {
                    "preferred_term": "Increased circulating test concentration",
                    "term": {"id": "HP:0088888", "label": "Increased circulating test concentration"},
                },
                "evidence": _evidence(),
                "sequelae": [
                    {
                        "name": "Phenotype B",
                        "phenotype_term": {
                            "term": {"id": "HP:0000002", "label": "Phenotype B"},
                        },
                        "evidence": _evidence(),
                    },
                ],
            },
            "functions": [
                {
                    "name": "Function A",
                    "evidence": _evidence(),
                    "biological_processes": [
                        {"term": {"id": "GO:0000001", "label": "Process A"}},
                    ],
                    "genes": [
                        {"term": {"id": "HGNC:1", "label": "Gene A"}},
                    ],
                    "cellular_components": [
                        {"term": {"id": "GO:0000002", "label": "Component A"}},
                    ],
                    "locations": [
                        {"term": {"id": "UBERON:0000001", "label": "Location A"}},
                    ],
                },
            ],
            "food_sources": [
                {
                    "name": "Food A",
                    "food_term": {
                        "term": {"id": "FOODON:00001", "label": "Food A"},
                    },
                    "evidence": _evidence(),
                },
                {
                    "name": "Food B (no FOODON)",
                    "food_term": {"preferred_term": "food b"},
                    "evidence": _evidence(),
                },
            ],
            "nutrient_interactions": [
                {
                    "name": "Interaction A",
                    "nutrient_term": {
                        "term": {"id": "CHEBI:00002", "label": "Other Nutrient"},
                    },
                    "evidence": _evidence(),
                },
            ],
            "drug_interactions": [
                {
                    "name": "Drug A",
                    "drug_term": {
                        "term": {"id": "CHEBI:00003", "label": "Drug A"},
                    },
                    "evidence": _evidence(),
                },
            ],
        }

    def test_transform_extracts_all_edges(self, sample_nutrient):
        """Test that transform extracts all edge types."""
        edges = list(transform(sample_nutrient))

        # 4 disease assocs +
        # 1 deficiency state + 1 deficiency sequela +
        # 1 toxicity state + 1 toxicity sequela +
        # 1 BP + 1 gene + 1 CC + 1 location +
        # 1 food source (second skipped, no FOODON ID) +
        # 1 nutrient interaction + 1 drug interaction = 15
        assert len(edges) == 15

        # All edges should be Association instances (all biolink assocs inherit from it)
        for edge in edges:
            assert isinstance(edge, Association)

        predicates = [e.predicate for e in edges]
        assert predicates.count("biolink:treats_or_applied_or_studied_to_treat") == 1
        assert predicates.count("biolink:preventative_for_condition") == 1
        assert predicates.count("biolink:affects_likelihood_of") == 1
        assert predicates.count("biolink:biomarker_for") == 1
        # 1 deficiency sequela + 1 toxicity sequela = 2
        assert predicates.count("biolink:causes") == 2
        # 2 state edges (deficiency + toxicity) + 1 gene = 3
        assert predicates.count("biolink:affects") == 3
        assert predicates.count("biolink:participates_in") == 1
        assert predicates.count("biolink:has_participant") == 1
        assert predicates.count("biolink:active_in") == 1
        assert predicates.count("biolink:has_nutrient") == 1
        assert predicates.count("biolink:interacts_with") == 2

    def test_transform_missing_nutrient_term(self):
        """Test that transform returns nothing if nutrient_term is missing."""
        record = {"name": "Test Nutrient"}
        edges = list(transform(record))
        assert len(edges) == 0

    def test_transform_empty_collections(self):
        """Test transform with empty/None collections."""
        record = {
            "name": "Test Nutrient",
            "nutrient_term": {"term": {"id": "CHEBI:00001"}},
            "disease_associations": None,
            "functions": [],
            "deficiency": None,
            "toxicity": None,
            "food_sources": None,
        }
        edges = list(transform(record))
        assert len(edges) == 0

    def test_transform_deficiency_without_phenotype_term(self):
        """Test that deficiency without phenotype_term produces no state/sequelae edges."""
        record = {
            "name": "Test Nutrient",
            "nutrient_term": {"term": {"id": "CHEBI:00001"}},
            "deficiency": {
                "sequelae": [
                    {"phenotype_term": {"term": {"id": "HP:0000001"}}},
                ],
            },
        }
        edges = list(transform(record))
        # No deficiency phenotype_term → no state edge and no sequelae edges
        assert len(edges) == 0

    def test_transform_skips_incomplete_entries(self):
        """Test that transform skips entries without term IDs."""
        record = {
            "name": "Test Nutrient",
            "nutrient_term": {"term": {"id": "CHEBI:00001"}},
            "disease_associations": [
                {
                    "disease_term": {"term": {"id": "MONDO:0000001"}},
                    "relationship_type": "THERAPEUTIC",
                    "evidence": _evidence(),
                },
                {
                    "disease_term": {"preferred_term": "No ID"},
                    "relationship_type": "THERAPEUTIC",
                    "evidence": _evidence(),
                },
            ],
            "deficiency": {
                "phenotype_term": {
                    "term": {"id": "HP:0099999"},
                },
                "evidence": _evidence(),
                "sequelae": [
                    {"phenotype_term": {"term": {"id": "HP:0000001"}}, "evidence": _evidence()},
                    {"name": "Incomplete"},
                ],
            },
        }
        edges = list(transform(record))
        # 1 disease + 1 deficiency state + 1 deficiency sequela = 3
        assert len(edges) == 3

    def test_transform_skips_entries_without_evidence(self):
        """Test that transform skips entries that have term IDs but no evidence."""
        record = {
            "name": "Test Nutrient",
            "nutrient_term": {"term": {"id": "CHEBI:00001"}},
            "disease_associations": [
                {
                    "disease_term": {"term": {"id": "MONDO:0000001"}},
                    "relationship_type": "THERAPEUTIC",
                },
            ],
            "deficiency": {
                "phenotype_term": {"term": {"id": "HP:0099999"}},
                "sequelae": [
                    {"phenotype_term": {"term": {"id": "HP:0000001"}}},
                ],
            },
        }
        edges = list(transform(record))
        assert len(edges) == 0


class TestExtractNodes:
    """Tests for the extract_nodes function."""

    @pytest.fixture
    def sample_nutrient(self):
        """Create a sample nutrient with all entity types."""
        return {
            "name": "Test Nutrient",
            "nutrient_term": {
                "preferred_term": "test nutrient",
                "term": {"id": "CHEBI:00001", "label": "test nutrient"},
            },
            "disease_associations": [
                {
                    "name": "Disease A",
                    "disease_term": {
                        "term": {"id": "MONDO:0000001", "label": "Disease A"},
                    },
                    "relationship_type": "THERAPEUTIC",
                },
            ],
            "deficiency": {
                "phenotype_term": {
                    "preferred_term": "Decreased circulating test concentration",
                    "term": {"id": "HP:0099999", "label": "Decreased circulating test concentration"},
                },
                "disease_term": {
                    "preferred_term": "test deficiency",
                    "term": {"id": "MONDO:0099999", "label": "test deficiency"},
                },
                "sequelae": [
                    {
                        "name": "Phenotype A",
                        "phenotype_term": {
                            "term": {"id": "HP:0000001", "label": "Phenotype A"},
                        },
                    },
                ],
            },
            "toxicity": {
                "phenotype_term": {
                    "preferred_term": "Increased circulating test concentration",
                    "term": {"id": "HP:0088888", "label": "Increased circulating test concentration"},
                },
                "sequelae": [
                    {
                        "name": "Phenotype B",
                        "phenotype_term": {
                            "term": {"id": "HP:0000002", "label": "Phenotype B"},
                        },
                    },
                ],
            },
            "functions": [
                {
                    "name": "Function A",
                    "biological_processes": [
                        {"preferred_term": "Process A", "term": {"id": "GO:0000001", "label": "process a"}},
                    ],
                    "genes": [
                        {"preferred_term": "Gene A", "term": {"id": "HGNC:1", "label": "gene a"}},
                    ],
                    "cellular_components": [
                        {"preferred_term": "Component A", "term": {"id": "GO:0000002", "label": "component a"}},
                    ],
                    "locations": [
                        {"preferred_term": "Location A", "term": {"id": "UBERON:0000001", "label": "location a"}},
                    ],
                },
            ],
            "food_sources": [
                {
                    "name": "Food A",
                    "food_term": {
                        "preferred_term": "food a",
                        "term": {"id": "FOODON:00001", "label": "food a"},
                    },
                },
            ],
            "nutrient_interactions": [
                {
                    "name": "Nutrient B",
                    "nutrient_term": {
                        "term": {"id": "CHEBI:00002", "label": "nutrient b"},
                    },
                },
            ],
            "drug_interactions": [
                {
                    "name": "Drug A",
                    "drug_term": {
                        "term": {"id": "CHEBI:00003", "label": "drug a"},
                    },
                },
            ],
        }

    def test_extracts_all_nodes(self, sample_nutrient):
        """Test that extract_nodes yields all unique entity nodes."""
        nodes = list(extract_nodes(sample_nutrient))

        # 1 nutrient + 1 disease assoc +
        # 1 deficiency state phenotype + 1 deficiency disease + 1 deficiency sequela +
        # 1 toxicity state phenotype + 1 toxicity sequela +
        # 1 BP + 1 gene + 1 CC + 1 location +
        # 1 food + 1 nutrient interaction + 1 drug interaction = 14
        assert len(nodes) == 14

    def test_node_types(self, sample_nutrient):
        """Test that nodes have correct biolink types."""
        nodes = list(extract_nodes(sample_nutrient))
        node_by_id = {n.id: n for n in nodes}

        assert isinstance(node_by_id["CHEBI:00001"], ChemicalEntity)
        assert isinstance(node_by_id["MONDO:0000001"], Disease)
        # Deficiency state phenotype + disease
        assert isinstance(node_by_id["HP:0099999"], PhenotypicFeature)
        assert isinstance(node_by_id["MONDO:0099999"], Disease)
        # Sequelae phenotypes
        assert isinstance(node_by_id["HP:0000001"], PhenotypicFeature)
        assert isinstance(node_by_id["HP:0000002"], PhenotypicFeature)
        # Toxicity state phenotype
        assert isinstance(node_by_id["HP:0088888"], PhenotypicFeature)
        assert isinstance(node_by_id["GO:0000001"], BiologicalProcess)
        assert isinstance(node_by_id["HGNC:1"], Gene)
        assert isinstance(node_by_id["GO:0000002"], CellularComponent)
        assert isinstance(node_by_id["UBERON:0000001"], AnatomicalEntity)
        assert isinstance(node_by_id["FOODON:00001"], Food)
        assert isinstance(node_by_id["CHEBI:00002"], ChemicalEntity)
        assert isinstance(node_by_id["CHEBI:00003"], ChemicalEntity)

    def test_node_names(self, sample_nutrient):
        """Test that nodes have correct names."""
        nodes = list(extract_nodes(sample_nutrient))
        node_by_id = {n.id: n for n in nodes}

        assert node_by_id["CHEBI:00001"].name == "Test Nutrient"
        assert node_by_id["HP:0000001"].name == "Phenotype A"
        assert node_by_id["GO:0000001"].name == "Process A"
        assert node_by_id["FOODON:00001"].name == "Food A"

    def test_node_provided_by(self, sample_nutrient):
        """Test that all nodes have provided_by set."""
        nodes = list(extract_nodes(sample_nutrient))
        for node in nodes:
            assert node.provided_by == [KNOWLEDGE_SOURCE]

    def test_node_categories(self, sample_nutrient):
        """Test that node categories are auto-populated by biolink model."""
        nodes = list(extract_nodes(sample_nutrient))
        node_by_id = {n.id: n for n in nodes}

        assert "biolink:ChemicalEntity" in node_by_id["CHEBI:00001"].category
        assert "biolink:Disease" in node_by_id["MONDO:0000001"].category
        assert "biolink:PhenotypicFeature" in node_by_id["HP:0000001"].category
        assert "biolink:Gene" in node_by_id["HGNC:1"].category

    def test_deduplicates_nodes(self):
        """Test that duplicate term IDs only produce one node."""
        record = {
            "name": "Test Nutrient",
            "nutrient_term": {"term": {"id": "CHEBI:00001"}},
            "deficiency": {
                "sequelae": [
                    {"name": "Pheno A", "phenotype_term": {"term": {"id": "HP:0000001"}}},
                ],
            },
            "toxicity": {
                "sequelae": [
                    # Same HP term in toxicity - should not duplicate
                    {"name": "Pheno A", "phenotype_term": {"term": {"id": "HP:0000001"}}},
                ],
            },
        }
        nodes = list(extract_nodes(record))
        ids = [n.id for n in nodes]
        assert ids.count("HP:0000001") == 1

    def test_missing_nutrient_term(self):
        """Test that extract_nodes returns nothing if nutrient_term is missing."""
        record = {"name": "Test Nutrient"}
        nodes = list(extract_nodes(record))
        assert len(nodes) == 0

    def test_skips_entries_without_term_ids(self):
        """Test that entries without term IDs are skipped."""
        record = {
            "name": "Test Nutrient",
            "nutrient_term": {"term": {"id": "CHEBI:00001"}},
            "deficiency": {
                "sequelae": [
                    {"name": "Complete", "phenotype_term": {"term": {"id": "HP:0000001"}}},
                    {"name": "Incomplete"},
                ],
            },
        }
        nodes = list(extract_nodes(record))
        ids = [n.id for n in nodes]
        assert "CHEBI:00001" in ids
        assert "HP:0000001" in ids
        assert len(nodes) == 2  # nutrient + 1 valid phenotype
