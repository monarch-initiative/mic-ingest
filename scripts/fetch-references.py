import re
import requests
import typer
from bs4 import BeautifulSoup
import csv
import sys


def fetch_references(url: str, output_file: str = None):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise e

    soup = BeautifulSoup(response.content, 'html.parser')

    references_data = []

    # Find <a> tags by name attribute, like <a name="reference1">
    reference_anchors = soup.find_all("a", attrs={"name": re.compile(r"^reference\d+$")})

    if not reference_anchors:
        print(f"No references found on the page: {url}")


    for anchor in reference_anchors:
        # Get the parent <li> element containing the full reference
        li = anchor.find_parent("li")
        if not li:
            continue

        full_li_text = li.get_text(separator=' ', strip=True)

        reference_number_str = None
        pubmed_id_str = None

        num_match = re.match(r'^reference(\d+)$', anchor['name'])
        if num_match:
            reference_number_str = num_match.group(1)

        link_texts_to_remove = []

        for link in li.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            if '(PubMed)' in link_text:
                pubmed_url = link['href']
                pubmed_id_match = re.search(r'(?:pubmed\.ncbi\.nlm\.nih\.gov/|ncbi\.nlm\.nih\.gov/pubmed/)(\d+)', pubmed_url)
                if pubmed_id_match:
                    pubmed_id_str = 'PMID:' + pubmed_id_match.group(1)
                link_texts_to_remove.append(link_text)

        cleaned_reference_text = full_li_text

        if reference_number_str and cleaned_reference_text.startswith(f"{reference_number_str}."):
            cleaned_reference_text = cleaned_reference_text[len(f"{reference_number_str}."):]
            
        for text_to_remove in link_texts_to_remove:
            cleaned_reference_text = cleaned_reference_text.replace(text_to_remove, '').strip()

        cleaned_reference_text = re.sub(r'^\s*<a[^>]*name="reference\d+"[^>]*></a>\s*', '', cleaned_reference_text)
        cleaned_reference_text = re.sub(r'\s+', ' ', cleaned_reference_text).strip()

        references_data.append([
            url,
            reference_number_str,
            pubmed_id_str,
            cleaned_reference_text
        ])

    if output_file:
        try:
            output = open(output_file, 'w', newline='', encoding='utf-8')
            writer = csv.writer(output, delimiter='\t')
            writer.writerow(['url', 'reference', 'pubmed_id', 'reference_text'])
            writer.writerows(references_data)
            output.close()
        except IOError as e:
            raise e

if __name__ == '__main__':
    typer.run(fetch_references)
