"""
KGX edge exporter for mic-ingest.

Transforms nutrient YAML files into KGX-format nodes and edges for the knowledge graph.
Each function extracts edges from a specific collection type within the nutrient record.
"""

import uuid
from typing import Any, Iterator

import koza
from koza import KozaTransform

from biolink_model.datamodel.pydanticmodel_v2 import (
    AgentTypeEnum,
    AnatomicalEntity,
    Association,
    BiologicalProcess,
    CellularComponent,
    ChemicalEntity,
    ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation,
    Disease,
    Food,
    Gene,
    KnowledgeLevelEnum,
    NamedThing,
    PhenotypicFeature,
)


# Knowledge source for all edges
KNOWLEDGE_SOURCE = "infores:mic"

# Frequency enum to HP term mapping
FREQUENCY_TO_HP = {
    "OBLIGATE": "HP:0040280",
    "VERY_FREQUENT": "HP:0040281",
    "FREQUENT": "HP:0040282",
    "OCCASIONAL": "HP:0040283",
    "VERY_RARE": "HP:0040284",
}

# Modifier enum to biolink direction qualifier
MODIFIER_TO_DIRECTION = {
    "INCREASED": "increased",
    "DECREASED": "decreased",
}


def _format_evidence(
    evidence_items: list[dict[str, Any]] | None, indirect: bool = False
) -> tuple[list[str], list[str]]:
    """
    Format evidence items for KGX export.

    Each evidence item is formatted as a concatenated string that preserves
    the PMID, support status, snippet, and explanation together.

    Args:
        evidence_items: List of evidence dicts from mic
        indirect: If True, flag as inherited from parent function

    Returns:
        Tuple of (publications list, supporting_text list)
    """
    publications = []
    supporting_text = []

    for e in evidence_items or []:
        ref = e.get("reference", "")
        if ref:
            publications.append(ref)

        supports = e.get("supports", "SUPPORT")
        snippet = e.get("snippet", "")
        explanation = e.get("explanation", "")

        if snippet:
            indirect_flag = "[INDIRECT EVIDENCE] " if indirect else ""
            text = f"[{ref}] {indirect_flag}[{supports}] {snippet}"
            if explanation:
                text += f" --- Explanation: {explanation}"
            supporting_text.append(text)

    return publications, supporting_text


def _make_edge_id() -> str:
    """Generate a unique edge ID."""
    return f"urn:uuid:{uuid.uuid4()}"


def _get_term_id(obj: dict[str, Any] | None, path: list[str]) -> str | None:
    """
    Safely navigate a nested dict to extract a term ID.

    Args:
        obj: The object to navigate
        path: List of keys to traverse (e.g., ["term", "id"])

    Returns:
        The term ID string if found, None otherwise
    """
    if obj is None:
        return None
    current = obj
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current if isinstance(current, str) else None


# =============================================================================
# Disease association edge converters
# =============================================================================

def therapeutic_to_edge(
    nutrient_id: str, disease_assoc: dict[str, Any]
) -> ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation | None:
    """
    Convert a THERAPEUTIC disease association to a KGX edge.

    Nutrient → Disease using treats_or_applied_or_studied_to_treat.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        disease_assoc: A disease association dict

    Returns:
        ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation or None
    """
    disease_id = _get_term_id(disease_assoc, ["disease_term", "term", "id"])
    if not disease_id:
        return None

    publications, supporting_text = _format_evidence(disease_assoc.get("evidence"))

    return ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:treats_or_applied_or_studied_to_treat",
        object=disease_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:Disease",
        publications=publications if publications else None,
        supporting_text=supporting_text if supporting_text else None,
        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


def protective_to_edge(
    nutrient_id: str, disease_assoc: dict[str, Any]
) -> ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation | None:
    """
    Convert a PROTECTIVE disease association to a KGX edge.

    Nutrient → Disease using preventative_for_condition.
    Uses direction field as direction qualifier when present.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        disease_assoc: A disease association dict

    Returns:
        ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation or None
    """
    disease_id = _get_term_id(disease_assoc, ["disease_term", "term", "id"])
    if not disease_id:
        return None

    publications, supporting_text = _format_evidence(disease_assoc.get("evidence"))

    direction = disease_assoc.get("direction")
    dir_qual = MODIFIER_TO_DIRECTION.get(direction) if direction else None
    qualifiers = []
    if dir_qual:
        qualifiers.append(f"direction:{dir_qual}")

    return ChemicalOrDrugOrTreatmentToDiseaseOrPhenotypicFeatureAssociation(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:preventative_for_condition",
        object=disease_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:Disease",
        qualifiers=qualifiers if qualifiers else None,
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


def risk_factor_to_edge(
    nutrient_id: str, disease_assoc: dict[str, Any]
) -> Association | None:
    """
    Convert a RISK_FACTOR disease association to a KGX edge.

    Nutrient → Disease using affects_likelihood_of.
    Uses direction field as direction qualifier when present.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        disease_assoc: A disease association dict

    Returns:
        Association or None
    """
    disease_id = _get_term_id(disease_assoc, ["disease_term", "term", "id"])
    if not disease_id:
        return None

    publications, supporting_text = _format_evidence(disease_assoc.get("evidence"))

    direction = disease_assoc.get("direction")
    dir_qual = MODIFIER_TO_DIRECTION.get(direction) if direction else None
    qualifiers = []
    if dir_qual:
        qualifiers.append(f"direction:{dir_qual}")

    return Association(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:affects_likelihood_of",
        object=disease_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:Disease",
        qualifiers=qualifiers if qualifiers else None,
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


def marker_to_edge(
    nutrient_id: str, disease_assoc: dict[str, Any]
) -> Association | None:
    """
    Convert a MARKER disease association to a KGX edge.

    Nutrient → Disease using biomarker_for.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        disease_assoc: A disease association dict

    Returns:
        Association or None
    """
    disease_id = _get_term_id(disease_assoc, ["disease_term", "term", "id"])
    if not disease_id:
        return None

    publications, supporting_text = _format_evidence(disease_assoc.get("evidence"))

    return Association(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:biomarker_for",
        object=disease_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:Disease",
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


def deficiency_causes_to_edge(
    nutrient_id: str, disease_assoc: dict[str, Any]
) -> Association | None:
    """
    Convert a DEFICIENCY_CAUSES disease association to a KGX edge.

    Nutrient → Disease using causes, with context:deficiency qualifier.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        disease_assoc: A disease association dict

    Returns:
        Association or None
    """
    disease_id = _get_term_id(disease_assoc, ["disease_term", "term", "id"])
    if not disease_id:
        return None

    publications, supporting_text = _format_evidence(disease_assoc.get("evidence"))

    return Association(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:causes",
        object=disease_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:Disease",
        qualifiers=["context:deficiency"],
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


# Dispatch table mapping relationship_type to converter function
_DISEASE_CONVERTERS = {
    "THERAPEUTIC": therapeutic_to_edge,
    "PROTECTIVE": protective_to_edge,
    "RISK_FACTOR": risk_factor_to_edge,
    "MARKER": marker_to_edge,
    "DEFICIENCY_CAUSES": deficiency_causes_to_edge,
}


# =============================================================================
# Deficiency phenotype edge converter
# =============================================================================


def deficiency_phenotype_to_edge(
    nutrient_id: str, phenotype: dict[str, Any]
) -> Association | None:
    """
    Convert a deficiency phenotype to a KGX edge.

    Nutrient → Phenotype using has_phenotype with context:deficiency qualifier.
    Includes frequency qualifier when present.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        phenotype: A phenotype dict from deficiency.phenotypes[]

    Returns:
        Association or None
    """
    term_id = _get_term_id(phenotype, ["phenotype_term", "term", "id"])
    if not term_id:
        return None

    frequency = phenotype.get("frequency")
    frequency_hp = FREQUENCY_TO_HP.get(frequency) if frequency else None

    publications, supporting_text = _format_evidence(phenotype.get("evidence"))

    qualifiers = ["context:deficiency"]
    if frequency_hp:
        qualifiers.append(f"frequency:{frequency_hp}")

    return Association(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:has_phenotype",
        object=term_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:PhenotypicFeature",
        qualifiers=qualifiers,
        publications=publications if publications else None,
        supporting_text=supporting_text if supporting_text else None,
        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


# =============================================================================
# Toxicity phenotype edge converter
# =============================================================================


def toxicity_phenotype_to_edge(
    nutrient_id: str, phenotype: dict[str, Any]
) -> Association | None:
    """
    Convert a toxicity phenotype to a KGX edge.

    Nutrient → Phenotype using has_phenotype with context:toxicity qualifier.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        phenotype: A phenotype dict from toxicity.phenotypes[]

    Returns:
        Association or None
    """
    term_id = _get_term_id(phenotype, ["phenotype_term", "term", "id"])
    if not term_id:
        return None

    publications, supporting_text = _format_evidence(phenotype.get("evidence"))

    return Association(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:has_phenotype",
        object=term_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:PhenotypicFeature",
        qualifiers=["context:toxicity"],
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


# =============================================================================
# Function sub-entity edge converters
# =============================================================================


def biological_process_to_edge(
    nutrient_id: str, process: dict[str, Any],
    parent_evidence: list[dict[str, Any]] | None = None,
) -> Association | None:
    """
    Convert a biological process entry to a KGX edge.

    Nutrient → BiologicalProcess using participates_in.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        process: A process dict from functions[].biological_processes[]
        parent_evidence: Evidence from parent function (indirect)

    Returns:
        Association or None
    """
    term_id = _get_term_id(process, ["term", "id"])
    if not term_id:
        return None

    publications, supporting_text = _format_evidence(parent_evidence, indirect=True)

    return Association(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:participates_in",
        object=term_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:BiologicalProcess",
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


def gene_to_edge(
    nutrient_id: str, gene: dict[str, Any],
    parent_evidence: list[dict[str, Any]] | None = None,
) -> Association | None:
    """
    Convert a gene entry to a KGX edge.

    Nutrient → Gene using affects.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        gene: A gene dict from functions[].genes[]
        parent_evidence: Evidence from parent function (indirect)

    Returns:
        Association or None
    """
    if not gene:
        return None

    term_id = _get_term_id(gene, ["term", "id"])
    if not term_id:
        return None

    publications, supporting_text = _format_evidence(parent_evidence, indirect=True)

    return Association(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:affects",
        object=term_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:Gene",
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


def cellular_component_to_edge(
    nutrient_id: str, component: dict[str, Any],
    parent_evidence: list[dict[str, Any]] | None = None,
) -> Association | None:
    """
    Convert a cellular component entry to a KGX edge.

    Nutrient → CellularComponent using has_participant.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        component: A component dict from functions[].cellular_components[]
        parent_evidence: Evidence from parent function (indirect)

    Returns:
        Association or None
    """
    term_id = _get_term_id(component, ["term", "id"])
    if not term_id:
        return None

    publications, supporting_text = _format_evidence(parent_evidence, indirect=True)

    return Association(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:has_participant",
        object=term_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:CellularComponent",
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


def location_to_edge(
    nutrient_id: str, location: dict[str, Any],
    parent_evidence: list[dict[str, Any]] | None = None,
) -> Association | None:
    """
    Convert a location entry to a KGX edge.

    Nutrient → AnatomicalEntity using active_in.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        location: A location dict from functions[].locations[]
        parent_evidence: Evidence from parent function (indirect)

    Returns:
        Association or None
    """
    term_id = _get_term_id(location, ["term", "id"])
    if not term_id:
        return None

    publications, supporting_text = _format_evidence(parent_evidence, indirect=True)

    return Association(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:active_in",
        object=term_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:AnatomicalEntity",
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


# =============================================================================
# Food source edge converter
# =============================================================================


def food_source_to_edge(
    nutrient_id: str, food_source: dict[str, Any]
) -> Association | None:
    """
    Convert a food source entry to a KGX edge.

    Food → Nutrient using has_nutrient. Subject is food (FOODON), object is nutrient (CHEBI).

    Args:
        nutrient_id: The nutrient CHEBI term ID
        food_source: A food source dict from food_sources[]

    Returns:
        Association or None
    """
    food_id = _get_term_id(food_source, ["food_term", "term", "id"])
    if not food_id:
        return None

    publications, supporting_text = _format_evidence(food_source.get("evidence"))

    return Association(
        id=_make_edge_id(),
        subject=food_id,
        predicate="biolink:has_nutrient",
        object=nutrient_id,
        subject_category="biolink:Food",
        object_category="biolink:ChemicalEntity",
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


# =============================================================================
# Interaction edge converters
# =============================================================================


def nutrient_interaction_to_edge(
    nutrient_id: str, interaction: dict[str, Any]
) -> Association | None:
    """
    Convert a nutrient interaction to a KGX edge.

    Nutrient → Nutrient using interacts_with.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        interaction: A nutrient interaction dict from nutrient_interactions[]

    Returns:
        Association or None
    """
    other_id = _get_term_id(interaction, ["nutrient_term", "term", "id"])
    if not other_id:
        return None

    publications, supporting_text = _format_evidence(interaction.get("evidence"))

    return Association(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:interacts_with",
        object=other_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:ChemicalEntity",
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


def drug_interaction_to_edge(
    nutrient_id: str, interaction: dict[str, Any]
) -> Association | None:
    """
    Convert a drug interaction to a KGX edge.

    Nutrient → Drug using interacts_with.

    Args:
        nutrient_id: The nutrient CHEBI term ID
        interaction: A drug interaction dict from drug_interactions[]

    Returns:
        Association or None
    """
    drug_id = _get_term_id(interaction, ["drug_term", "term", "id"])
    if not drug_id:
        return None

    publications, supporting_text = _format_evidence(interaction.get("evidence"))

    return Association(
        id=_make_edge_id(),
        subject=nutrient_id,
        predicate="biolink:interacts_with",
        object=drug_id,
        subject_category="biolink:ChemicalEntity",
        object_category="biolink:ChemicalEntity",
        publications=publications if publications else None,

        primary_knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_validation_of_automated_agent,
    )


# =============================================================================
# Node extraction
# =============================================================================

_CATEGORY_TO_NODE_CLASS: dict[str, type[NamedThing]] = {
    "biolink:ChemicalEntity": ChemicalEntity,
    "biolink:Disease": Disease,
    "biolink:PhenotypicFeature": PhenotypicFeature,
    "biolink:BiologicalProcess": BiologicalProcess,
    "biolink:Gene": Gene,
    "biolink:CellularComponent": CellularComponent,
    "biolink:AnatomicalEntity": AnatomicalEntity,
    "biolink:Food": Food,
}


def _make_node(node_id: str, name: str | None, category: str) -> NamedThing:
    """
    Create a biolink node of the appropriate type.

    Args:
        node_id: The CURIE identifier
        name: Human-readable label
        category: Biolink category string

    Returns:
        A NamedThing subclass instance
    """
    cls = _CATEGORY_TO_NODE_CLASS.get(category, NamedThing)
    return cls(id=node_id, name=name, provided_by=[KNOWLEDGE_SOURCE])


def extract_nodes(record: dict[str, Any]) -> Iterator[NamedThing]:
    """
    Extract all unique KGX nodes from a nutrient record.

    Walks the same record structure as transform() but yields node objects
    instead of edges. Each unique entity ID is emitted only once.

    Args:
        record: A nutrient dict loaded from YAML

    Yields:
        NamedThing subclass instances for all unique entities
    """
    seen: set[str] = set()

    def _emit(node_id: str | None, name: str | None, category: str) -> NamedThing | None:
        if not node_id or node_id in seen:
            return None
        seen.add(node_id)
        return _make_node(node_id, name, category)

    # Nutrient node (ChemicalEntity)
    nutrient_id = _get_term_id(record, ["nutrient_term", "term", "id"])
    if not nutrient_id:
        return
    node = _emit(nutrient_id, record.get("name"), "biolink:ChemicalEntity")
    if node:
        yield node

    # Disease association nodes
    for da in record.get("disease_associations") or []:
        term_id = _get_term_id(da, ["disease_term", "term", "id"])
        label = _get_term_id(da, ["disease_term", "term", "label"])
        node = _emit(term_id, da.get("name") or label, "biolink:Disease")
        if node:
            yield node

    # Deficiency phenotype nodes
    deficiency = record.get("deficiency") or {}
    for phenotype in deficiency.get("phenotypes") or []:
        term_id = _get_term_id(phenotype, ["phenotype_term", "term", "id"])
        label = _get_term_id(phenotype, ["phenotype_term", "term", "label"])
        node = _emit(term_id, phenotype.get("name") or label, "biolink:PhenotypicFeature")
        if node:
            yield node

    # Toxicity phenotype nodes
    toxicity = record.get("toxicity") or {}
    for phenotype in toxicity.get("phenotypes") or []:
        term_id = _get_term_id(phenotype, ["phenotype_term", "term", "id"])
        label = _get_term_id(phenotype, ["phenotype_term", "term", "label"])
        node = _emit(term_id, phenotype.get("name") or label, "biolink:PhenotypicFeature")
        if node:
            yield node

    # Function sub-entity nodes
    for func in record.get("functions") or []:
        for bp in func.get("biological_processes") or []:
            term_id = _get_term_id(bp, ["term", "id"])
            label = _get_term_id(bp, ["term", "label"])
            node = _emit(term_id, bp.get("preferred_term") or label, "biolink:BiologicalProcess")
            if node:
                yield node

        for gene in func.get("genes") or []:
            term_id = _get_term_id(gene, ["term", "id"])
            label = _get_term_id(gene, ["term", "label"])
            node = _emit(term_id, gene.get("preferred_term") or label, "biolink:Gene")
            if node:
                yield node

        for cc in func.get("cellular_components") or []:
            term_id = _get_term_id(cc, ["term", "id"])
            label = _get_term_id(cc, ["term", "label"])
            node = _emit(term_id, cc.get("preferred_term") or label, "biolink:CellularComponent")
            if node:
                yield node

        for loc in func.get("locations") or []:
            term_id = _get_term_id(loc, ["term", "id"])
            label = _get_term_id(loc, ["term", "label"])
            node = _emit(term_id, loc.get("preferred_term") or label, "biolink:AnatomicalEntity")
            if node:
                yield node

    # Food source nodes
    for food in record.get("food_sources") or []:
        term_id = _get_term_id(food, ["food_term", "term", "id"])
        label = _get_term_id(food, ["food_term", "term", "label"])
        node = _emit(term_id, food.get("name") or label, "biolink:Food")
        if node:
            yield node

    # Nutrient interaction nodes
    for interaction in record.get("nutrient_interactions") or []:
        term_id = _get_term_id(interaction, ["nutrient_term", "term", "id"])
        label = _get_term_id(interaction, ["nutrient_term", "term", "label"])
        node = _emit(term_id, interaction.get("name") or label, "biolink:ChemicalEntity")
        if node:
            yield node

    # Drug interaction nodes
    for interaction in record.get("drug_interactions") or []:
        term_id = _get_term_id(interaction, ["drug_term", "term", "id"])
        label = _get_term_id(interaction, ["drug_term", "term", "label"])
        node = _emit(term_id, interaction.get("name") or label, "biolink:ChemicalEntity")
        if node:
            yield node


# =============================================================================
# Main transform
# =============================================================================


def transform(record: dict[str, Any]) -> Iterator[Association]:
    """
    Extract all KGX edges from a nutrient record.

    This is the pure function for extracting edges. It can be called directly
    for testing without the Koza runner.

    Args:
        record: A nutrient dict loaded from YAML

    Yields:
        Association objects for all associations in the nutrient
    """
    # Get nutrient ID - required for all edges
    nutrient_id = _get_term_id(record, ["nutrient_term", "term", "id"])
    if not nutrient_id:
        return

    # Disease associations - dispatched by relationship_type
    for da in record.get("disease_associations") or []:
        rel_type = da.get("relationship_type")
        converter = _DISEASE_CONVERTERS.get(rel_type)
        if converter:
            edge = converter(nutrient_id, da)
            if edge:
                yield edge

    # Deficiency phenotypes
    deficiency = record.get("deficiency") or {}
    for phenotype in deficiency.get("phenotypes") or []:
        edge = deficiency_phenotype_to_edge(nutrient_id, phenotype)
        if edge:
            yield edge

    # Toxicity phenotypes
    toxicity = record.get("toxicity") or {}
    for phenotype in toxicity.get("phenotypes") or []:
        edge = toxicity_phenotype_to_edge(nutrient_id, phenotype)
        if edge:
            yield edge

    # Function sub-entities (children inherit evidence from parent function)
    for func in record.get("functions") or []:
        parent_evidence = func.get("evidence")

        for bp in func.get("biological_processes") or []:
            edge = biological_process_to_edge(nutrient_id, bp, parent_evidence)
            if edge:
                yield edge

        for gene in func.get("genes") or []:
            edge = gene_to_edge(nutrient_id, gene, parent_evidence)
            if edge:
                yield edge

        for cc in func.get("cellular_components") or []:
            edge = cellular_component_to_edge(nutrient_id, cc, parent_evidence)
            if edge:
                yield edge

        for loc in func.get("locations") or []:
            edge = location_to_edge(nutrient_id, loc, parent_evidence)
            if edge:
                yield edge

    # Food sources
    for food in record.get("food_sources") or []:
        edge = food_source_to_edge(nutrient_id, food)
        if edge:
            yield edge

    # Nutrient interactions
    for interaction in record.get("nutrient_interactions") or []:
        edge = nutrient_interaction_to_edge(nutrient_id, interaction)
        if edge:
            yield edge

    # Drug interactions
    for interaction in record.get("drug_interactions") or []:
        edge = drug_interaction_to_edge(nutrient_id, interaction)
        if edge:
            yield edge


@koza.transform_record()
def koza_transform(koza_ctx: KozaTransform, record: dict[str, Any]) -> None:
    """Koza-decorated transform that wraps the pure transform function."""
    for node in extract_nodes(record):
        koza_ctx.write(node)
    for edge in transform(record):
        koza_ctx.write(edge)
