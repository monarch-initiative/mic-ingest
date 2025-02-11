import json
import csv
import os
from pydantic import BaseModel
from typing import List

input_dir = 'output/'
output_dir = 'output/tsv'

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# A pydantic model for category, subject, predicate, object, references (list), source_url
class Association(BaseModel):
    category: str
    subject: str
    predicate: str
    object: str
    references: List[str] = []
    source_url: str

    class Config:
        str_min_length = 1
        str_strip_whitespace = True

# A dictionary to hold a map from category to a list of associations matching that category
associations = {}


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
                        association = Association(
                            category=category,
                            subject=relationship[subject],
                            predicate=relationship['relationship'],
                            object=relationship[object],
                            references=relationship.get('references', []),
                            source_url=source_url
                        )

                        if category not in associations:
                            associations[category] = []

                        associations[category].append(association)

# Write the TSV files for each category
for category, associations_list in associations.items():
    output_file = os.path.join(output_dir, f'{category}.tsv')

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(Association.model_fields.keys())

        for association in associations_list:
            writer.writerow(association.model_dump().values())
