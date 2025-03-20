import json
import csv
import os
from pydantic import BaseModel
from typing import List, Optional

input_dir = 'output/'
output_dir = 'output/tsv'
references_file = 'output/references.tsv'

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# A pydantic model for category, subject, predicate, object, references (list), source_url
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

# A dictionary to hold a map from category to a list of associations matching that category
associations = {}

# load references.tsv as a dict[dict[str,List[str]]] of page_url to page_reference to pubmed id
references = {}
with open(references_file, 'r') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if row['url'] not in references:
            references[row['url']] = {}
        if row['pubmed_id'].strip():
            references[row['url']][row['reference']] = row['pubmed_id']

# Process each JSON file in the input directory and its subdirectories
for root, _, files in os.walk(input_dir):
    for filename in files:
        if filename.endswith('.json'):
            input_file = os.path.join(root, filename)
            print(f'Processing {input_file}')
            # Read the JSON file
            with open(input_file, 'r') as f:
                data = json.load(f)

            # Extract the source_url
            source_url = data.get('source_url', '')


            # make an entity lookup table from the named_entities section
            entity_labels = {}
            if 'named_entities' in data:
                for entity in data["named_entities"]:
                    entity_labels[entity['id']] = entity.get('label', None)

            # Prepare the data for TSV
            for key, relationships in data["extracted_object"].items():
                if key.endswith('relationships'):
                    category = key.replace('_relationships', '')
                    for relationship in relationships:
                        # remove reference, relationship and original text keys if they exist to find the subject and object keys
                        keys = list(relationship.keys())
                        keys.remove('references') if 'references' in keys else None
                        keys.remove('relationship') if 'relationship' in keys else None
                        keys.remove('original_text') if 'original_text' in keys else None
                        try:
                            subject, object = keys
                        except ValueError:
                            print(f'Error: extracted too many keys from {relationship.keys()}')
                            continue

                        pubmed_ids = []
                        for reference in relationship.get('references', []):
                            if source_url in references and reference in references[source_url]:
                                pubmed_ids.append(references[source_url][reference])

                        subject = relationship.get(subject, None)
                        subject_label = entity_labels.get(subject, None)
                        # if the subject comes back as a name rather than curie, then it is a label and we don't have a subject
                        if ':' not in subject and subject_label is None:
                            subject_label = subject
                            subject = None

                        object = relationship.get(object, None)
                        object_label = entity_labels.get(object, None)
                        # same for object
                        if ':' not in object and object_label is None:
                            object_label = object
                            object = None

                        association = Association(
                            category=category,
                            subject=subject,
                            subject_label=subject_label,
                            predicate=relationship['relationship'],
                            object=object,
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
            row['publications'] = '|'.join(row['publications'])  # Convert list to '|' joined string
            row['references'] = '|'.join(row['references'])  # Convert list to '|' joined string
            writer.writerow(row.values())

# Write the TSV files for each category
for category, associations_list in associations.items():
    output_file = os.path.join(output_dir, f'{category}.tsv')
    write_tsv_file(output_file, associations_list)

# Write the TSV file for all categories
all_associations = [association for associations_list in associations.values() for association in associations_list]
output_file = os.path.join(output_dir, 'raw_associations.tsv')
write_tsv_file(output_file, all_associations)
