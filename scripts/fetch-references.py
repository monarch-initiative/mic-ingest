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

    output_stream = None
    writer = None

    try:
        if output_file:
            output_stream = open(output_file, 'w', newline='', encoding='utf-8')
        else:
            output_stream = sys.stdout  # <- stdout important for Makefile!

        writer = csv.writer(output_stream, delimiter='\t')
        writer.writerow(['url', 'reference', 'pubmed_id', 'reference_text'])
        writer.writerows(references_data)

    except IOError as e:
        raise e

    finally:
        if output_file and output_stream:
            output_stream.close()

    # Fail if no references found but dont error out
    if not references_data:
        print(f"NO_REFERENCES\t{url}", file=sys.stderr)
        # still write header-only TSV if output_file is given
        if output_file:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter="\t")
                writer.writerow(["url", "reference", "pubmed_id", "reference_text"])

if __name__ == '__main__':
    typer.run(fetch_references)
