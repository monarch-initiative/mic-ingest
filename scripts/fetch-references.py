import re

import requests
import typer
from bs4 import BeautifulSoup
import csv
import sys


def fetch_references(url: str, output_file: str = None):
    """
    Fetch references from a given URL and write them to an output file or stdout.

    Args:
        url (str): The URL of the webpage to fetch references from.
        output_file (str, optional): The path to the output file. If not provided, the output will be written to stdout.

    Raises:
        requests.exceptions.RequestException: If the HTTP request to the URL fails.
        re.error: If there is an error in the regular expression used to parse the references.

    The output is a tab-separated values (TSV) format with the following columns:
        - url: The URL of the webpage.
        - reference: The reference number.
        - pubmed_id: The PubMed ID of the reference, prefixed with 'PMID:'.
        - reference_text: The text of the reference without the reference number and PubMed ID.
    """
    # Fetch the HTML content from the URL
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    references_anchor = soup.find('a', id='references')

    if references_anchor:
        next_element = references_anchor.parent.find_next_sibling()
        references = []
        while next_element and next_element.name == 'p' and re.match(r'^\d+\..*', next_element.get_text(strip=True)):
            # Extract reference number from the beginning of the reference text
            reference_text = next_element.get_text(strip=True)
            match = re.match(r'^(\d+)\.', reference_text)
            if match:
                reference_number = match.group(1)
            else:
                reference_number = None

            # Extract PubMed ID from the link
            pubmed_link = next_element.find('a', href=True, string='(PubMed)')
            if pubmed_link:
                pubmed_id_match = re.search(r'/(\d{6,})$', pubmed_link['href'])
                pubmed_id = pubmed_id_match.group(1) if pubmed_id_match else None
            else:
                pubmed_id = None

            if pubmed_id is not None:
                pubmed_id = 'PMID:' + pubmed_id

            # strip the reference number and PubMed ID from the reference text
            if reference_number is not None and reference_text.startswith(f'{reference_number}.'):
                reference_text = reference_text.replace(f'{reference_number}.', '', 1).strip()
            if pubmed_id is not None and reference_text.endswith(f'(PubMed)'):
                reference_text = reference_text.replace(f'(PubMed)', '')

            references.append([url, reference_number, pubmed_id, reference_text])
            next_element = next_element.find_next_sibling()

        # Write to stdout or file
        output = sys.stdout if output_file is None else open(output_file, 'w', newline='')
        writer = csv.writer(output, delimiter='\t')
        writer.writerow(['url', 'reference', 'pubmed_id', 'reference_text'])
        writer.writerows(references)
        if output_file:
            output.close()
    else:
        print("No references anchor found on the page")

if __name__ == '__main__':
    typer.run(fetch_references)
