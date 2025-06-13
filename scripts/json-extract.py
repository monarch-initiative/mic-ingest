import json
import csv
import os
from pydantic import BaseModel
from typing import List, Optional, Dict

input_dir = 'output/'
output_dir = 'output/tsv'
references_file = 'output/references.tsv'

os.makedirs(output_dir, exist_ok=True)

class Association(BaseModel):
    category: str
    subject: Optional[str]
    subject_label: Optional[str]
    predicate: str
    object: Optional[str]
    object_label: Optional[str]
    references: List[str] = []
    publications: List[str] = []
    source_url: str

    class Config:
        str_min_length = 1
        str_strip_whitespace = True

associations = {}

references = {}
with open(references_file, 'r') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if row['url'] not in references:
            references[row['url']] = {}
        if row['pubmed_id'].strip():
            references[row['url']][row['reference']] = row['pubmed_id']


manual_schema_map: Dict[str, dict] = {
              'nutrient_to_disease_relationships': {'subject':'nutrient', 'object':'disease'},
              'nutrient_to_phenotype_relationships':  {'subject':'nutrient', 'object':'phenotype'},
              'nutrient_to_biological_process_relationships': {'subject':'nutrient', 'object':'process'},
              'nutrient_to_health_status_relationships':  {'subject':'nutrient', 'object':'anatomy'},
              'nutrient_to_source_relationships':  {'subject':'nutrient', 'object':'source'},
              'nutrient_to_nutrient_relationships':  {'subject':'nutrient', 'object':'nutrient'}
              }

subject_label = None
object_label = None
subject_key = None
object_key = None
required = None


for root, _, files in os.walk(input_dir):
    for filename in files:
        if filename.endswith('.json'):
            input_file = os.path.join(root, filename)
            print(f'Processing {input_file}')
            with open(input_file, 'r') as f:
                data = json.load(f)
            source_url = data.get('source_url', '')
            entity_labels = {}
            if 'named_entities' in data:
                for entity in data["named_entities"]:
                    entity_labels[entity['id']] = entity.get('label', None)
            for key, relationships in data["extracted_object"].items():
                if key in manual_schema_map:
                    schema = manual_schema_map[key]
                    # here we check if e.g nutrient_to_disease_relationships and get the subject and object(which should be nutrient and object should be disease)
                    subject_key = schema['subject'] #nutrient
                    object_key = schema['object'] # disease
                    required = {'relationship', subject_key, object_key}
                if key.endswith('relationships'):
                    category = key.replace('_relationships', '')

                    for relationship in relationships:
                        # only process if SPO is complete
                        if not required.issubset(relationship):
                            continue

                        pubmed_ids = []
                        for reference in relationship.get('references', []):
                            if source_url in references and reference in references[source_url]:
                                pubmed_ids.append(references[source_url][reference])

                        if ':' not in relationship[subject_key] and subject_label is None:
                            subject_label = relationship[subject_key]
                            subject = None

                        if ':' not in relationship[object_key] and object_label is None:
                            object_label = relationship[object_key]
                            object = None

                        association = Association(
                            category=category,
                            subject=relationship[subject_key],
                            subject_label=subject_label,
                            predicate=relationship['relationship'],
                            object=relationship[object_key],
                            object_label=object_label,
                            publications=pubmed_ids,
                            references=relationship.get('references', []),
                            source_url=source_url
                        )

                        if category not in associations:
                            associations[category] = []

                        associations[category].append(association)

def write_tsv_file(output_file, associations_list):
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(Association.model_fields.keys())

        for association in associations_list:
            row = association.model_dump()
            row['publications'] = '|'.join(row['publications']) 
            row['references'] = '|'.join(row['references']) 
            writer.writerow(row.values())

for category, associations_list in associations.items():
    output_file = os.path.join(output_dir, f'{category}.tsv')
    write_tsv_file(output_file, associations_list)
    print(f"Output written to {output_file}")

all_associations = [association for associations_list in associations.values() for association in associations_list]
output_file = os.path.join(output_dir, 'raw_associations.tsv')
write_tsv_file(output_file, all_associations)
