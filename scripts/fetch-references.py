"""
Extract references from MIC (Micronutrient Information Center) pages.

This script parses MIC HTML pages to extract reference numbers and their
associated PubMed IDs, producing a TSV mapping file.

Usage:
    # From URL
    uv run python scripts/fetch-references.py https://lpi.oregonstate.edu/mic/vitamins/vitamin-C

    # From cached HTML file
    uv run python scripts/fetch-references.py cache/mic-pages/vitamin-C.html --from-file

    # Output to file
    uv run python scripts/fetch-references.py URL -o cache/references/vitamin-c-refs.tsv
"""

import re
import sys
import time
from pathlib import Path

import requests
import typer
from bs4 import BeautifulSoup
import csv


app = typer.Typer(help="Extract references from MIC pages")


def parse_references_from_html(html_content: str, source: str) -> list:
    """Parse references from MIC HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    references_data = []

    # Find <a> tags by name attribute, like <a name="reference1">
    reference_anchors = soup.find_all("a", attrs={"name": re.compile(r"^reference\d+$")})

    if not reference_anchors:
        print(f"No references found: {source}", file=sys.stderr)
        return references_data

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
                pubmed_id_match = re.search(
                    r'(?:pubmed\.ncbi\.nlm\.nih\.gov/|ncbi\.nlm\.nih\.gov/pubmed/)(\d+)',
                    pubmed_url
                )
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

        references_data.append({
            'source': source,
            'reference_number': reference_number_str,
            'pubmed_id': pubmed_id_str,
            'citation': cleaned_reference_text
        })

    return references_data


@app.command()
def extract(
    source: str = typer.Argument(..., help="URL or file path to MIC page"),
    output: str = typer.Option(None, "-o", "--output", help="Output file (default: stdout)"),
    from_file: bool = typer.Option(False, "--from-file", help="Read from local file instead of URL"),
    format: str = typer.Option("tsv", "--format", "-f", help="Output format: tsv or yaml"),
):
    """Extract references from a MIC page (URL or cached HTML file)."""

    if from_file:
        # Read from local file
        path = Path(source)
        if not path.exists():
            typer.echo(f"File not found: {source}", err=True)
            raise typer.Exit(1)
        html_content = path.read_text(encoding='utf-8')
        source_name = path.name
    else:
        # Fetch from URL
        try:
            response = requests.get(source)
            response.raise_for_status()
            html_content = response.text
            source_name = source
            time.sleep(1)  # Rate limiting
        except requests.exceptions.RequestException as e:
            typer.echo(f"Failed to fetch URL: {e}", err=True)
            raise typer.Exit(1)

    references = parse_references_from_html(html_content, source_name)

    if not references:
        typer.echo(f"NO_REFERENCES\t{source_name}", err=True)
        # Still output empty structure
        if format == "yaml":
            output_content = "references: []\n"
        else:
            output_content = "source\treference_number\tpubmed_id\tcitation\n"
    elif format == "yaml":
        import yaml
        output_content = yaml.dump({'references': references}, default_flow_style=False, allow_unicode=True)
    else:
        # TSV format
        output_stream = sys.stdout if not output else open(output, 'w', newline='', encoding='utf-8')
        try:
            writer = csv.writer(output_stream, delimiter='\t')
            writer.writerow(['source', 'reference_number', 'pubmed_id', 'citation'])
            for ref in references:
                writer.writerow([ref['source'], ref['reference_number'], ref['pubmed_id'], ref['citation']])
        finally:
            if output:
                output_stream.close()
        return

    # For YAML output
    if output:
        Path(output).write_text(output_content, encoding='utf-8')
    else:
        typer.echo(output_content, nl=False)


@app.command()
def fetch_abstracts(
    references_file: str = typer.Argument(..., help="TSV file with references"),
    output_dir: str = typer.Option("cache/references", help="Directory for cached abstracts"),
):
    """Fetch PubMed abstracts for all PMIDs in a references file."""
    import subprocess

    refs_path = Path(references_file)
    if not refs_path.exists():
        typer.echo(f"File not found: {references_file}", err=True)
        raise typer.Exit(1)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(refs_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            pmid = row.get('pubmed_id')
            if not pmid:
                continue

            # Check if already cached
            pmid_num = pmid.replace('PMID:', '')
            cache_file = output_path / f"pmid_{pmid_num}.md"
            if cache_file.exists():
                typer.echo(f"Already cached: {pmid}")
                continue

            typer.echo(f"Fetching: {pmid}")
            try:
                subprocess.run(
                    ["just", "fetch-reference", pmid],
                    check=True,
                    capture_output=True
                )
                time.sleep(0.5)  # Rate limiting
            except subprocess.CalledProcessError as e:
                typer.echo(f"Failed to fetch {pmid}: {e}", err=True)


if __name__ == '__main__':
    app()
