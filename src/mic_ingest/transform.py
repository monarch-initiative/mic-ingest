import uuid  # For generating UUIDs for associations

from biolink_model.datamodel.pydanticmodel_v2 import *  # Replace * with any necessary data classes from the Biolink Model
from koza.cli_utils import get_koza_app

koza_app = get_koza_app("lpi_chemical_to_pathway")

while (row := koza_app.get_row()) is not None:
    # Code to transform each row of data
    # For more information, see https://koza.monarchinitiative.org/Ingests/transform
    entity_a = Entity(
        id=f"XMPL:00000{row['example_column_1'].split('_')[-1]}",
        name=row["example_column_1"],
        category=["biolink:Entity"],
    )
    entity_b = Entity(
        id=f"XMPL:00000{row['example_column_2'].split('_')[-1]}",
        name=row["example_column_2"],
        category=["biolink:Entity"],
    )
    association = Association(
        id=str(uuid.uuid1()),
        subject=row["example_column_1"],
        predicate=row["example_column_3"],
        object=row["example_column_2"],
        subject_category="SUBJ",
        object_category="OBJ",
        category=["biolink:Association"],
        knowledge_level="not_provided",
        agent_type="not_provided",
    )
    koza_app.write(entity_a, entity_b, association)
