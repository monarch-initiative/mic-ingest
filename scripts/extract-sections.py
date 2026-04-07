"""
Extract sections from MIC HTML pages for section-by-section curation.

MIC pages are typically 200-300KB, too large for direct LLM context.
This script extracts individual sections as smaller, focused chunks.

Usage:
    # List all sections in a page
    uv run python scripts/extract-sections.py cache/mic-pages/vitamin-C.html --list

    # Extract a specific section
    uv run python scripts/extract-sections.py cache/mic-pages/vitamin-C.html --section deficiency

    # Extract all sections to cache directory
    uv run python scripts/extract-sections.py cache/mic-pages/vitamin-C.html --all --output cache/sections/vitamin-c/

    # Get summary with section sizes
    uv run python scripts/extract-sections.py cache/mic-pages/vitamin-C.html --summary
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import typer
from bs4 import BeautifulSoup, NavigableString
from markdownify import markdownify as md

app = typer.Typer(help="Extract sections from MIC HTML pages")


# Section ID patterns that map to schema fields
SECTION_PATTERNS = {
    "function": [r"^function$", r"^role-in-", r"^biological-"],
    "deficiency": [r"^deficiency$", r"^signs-.*deficiency"],
    "recommendations": [r"^RDA$", r"^AI$", r"^UL$", r"^dietary-recommend", r"^table-\d+"],
    "disease_prevention": [r"-prevention$", r"^disease-prevention$"],
    "disease_treatment": [r"-treatment$", r"^disease-treatment$"],
    "toxicity": [r"^toxicity$", r"^safety$", r"^adverse-", r"^pro-oxidant"],
    "food_sources": [r"^sources$", r"^food-sources$", r"^dietary-sources"],
    "drug_interactions": [r"^drug-interact", r"^medication"],
    "nutrient_interactions": [r"^nutrient-interact"],
    "bioavailability": [r"^bioavailability$", r"^absorption$"],
    "metabolism": [r"^metabolism$"],
    "references": [r"^references$"],
    "summary": [r"^summary$"],
}


@dataclass
class Section:
    """A section extracted from MIC HTML."""
    id: str
    title: str
    html: str
    markdown: str
    schema_field: Optional[str]
    char_count: int

    @property
    def is_small(self) -> bool:
        """Section is small enough for direct context."""
        return self.char_count < 10000


class MICSectionExtractor:
    """Extract sections from MIC HTML pages."""

    def __init__(self, html_path: str):
        self.path = Path(html_path)
        self.html = self.path.read_text(encoding='utf-8')
        self.soup = BeautifulSoup(self.html, 'html.parser')
        self._sections: dict[str, Section] = {}
        self._extract_sections()

    def _get_schema_field(self, section_id: str) -> Optional[str]:
        """Map section ID to schema field."""
        for field, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, section_id, re.IGNORECASE):
                    return field
        return None

    def _extract_sections(self):
        """Parse HTML and extract all sections."""
        # MIC uses <a name="..."> anchors for sections, not id attributes
        # Find all named anchors that represent content sections
        named_anchors = self.soup.find_all('a', attrs={'name': True})

        # Filter to content sections (skip references, figures, tables)
        skip_patterns = [
            r'^reference\d+$',  # Reference anchors
            r'^figure-\d+$',    # Figure anchors
            r'^table-\d+$',     # Table anchors (keep some)
        ]

        content_anchors = []
        for anchor in named_anchors:
            name = anchor.get('name', '')
            if not any(re.match(p, name) for p in skip_patterns):
                content_anchors.append(anchor)

        # Process each anchor as a section
        for i, anchor in enumerate(content_anchors):
            section_id = anchor.get('name', '')

            # Get section title
            title = self._get_section_title(anchor, section_id)

            # Get section content (until next section anchor)
            next_anchor = content_anchors[i + 1] if i + 1 < len(content_anchors) else None
            section_html = self._get_section_content_between(anchor, next_anchor)

            if section_html and len(section_html) > 50:  # Skip tiny sections
                section_md = self._html_to_markdown(section_html)
                schema_field = self._get_schema_field(section_id)

                self._sections[section_id] = Section(
                    id=section_id,
                    title=title,
                    html=section_html,
                    markdown=section_md,
                    schema_field=schema_field,
                    char_count=len(section_md)
                )

    def _get_section_title(self, elem, section_id: str) -> str:
        """Extract title from section element."""
        # Check for heading in or near the element
        heading = elem.find(['h1', 'h2', 'h3', 'h4'])
        if heading:
            return heading.get_text(strip=True)

        # Check if element itself is a heading
        if elem.name in ['h1', 'h2', 'h3', 'h4']:
            return elem.get_text(strip=True)

        # Check previous sibling
        prev = elem.find_previous_sibling(['h1', 'h2', 'h3', 'h4'])
        if prev:
            return prev.get_text(strip=True)

        # Fall back to ID
        return section_id.replace('-', ' ').title()

    def _get_section_content_between(self, start_anchor, end_anchor) -> str:
        """Get content between two named anchors."""
        content_parts = []

        # Start from the anchor's parent or next sibling
        current = start_anchor.parent if start_anchor.parent else start_anchor

        # Collect elements until we reach the end anchor
        visited = set()
        while current:
            # Avoid infinite loops
            if id(current) in visited:
                break
            visited.add(id(current))

            # Skip NavigableStrings first
            if isinstance(current, NavigableString):
                if current.strip():
                    content_parts.append(str(current))
                current = current.next_sibling
                continue

            # Check if we've reached the end anchor
            if end_anchor:
                if current == end_anchor or current == end_anchor.parent:
                    break
                # Check if end anchor is inside current element (only for Tag objects)
                try:
                    found = current.find('a', attrs={'name': end_anchor.get('name')})
                    if found:
                        break
                except (TypeError, AttributeError):
                    pass

            # Skip scripts and styles
            if hasattr(current, 'name') and current.name in ['script', 'style']:
                current = current.next_sibling
                continue

            content_parts.append(str(current))
            current = current.next_sibling

        return '\n'.join(content_parts)

    def _get_section_content(self, elem) -> str:
        """Get content from section element until next section."""
        content_parts = []

        # Include the element itself if it has content
        if elem.name in ['div', 'section', 'article']:
            content_parts.append(str(elem))
        else:
            # Include element and siblings until next section heading
            current = elem
            while current:
                if isinstance(current, NavigableString):
                    current = current.next_sibling
                    continue

                # Stop at next major section
                if current.name in ['h2', 'h3'] and current != elem:
                    if current.get('id'):
                        break

                content_parts.append(str(current))
                current = current.next_sibling

        return '\n'.join(content_parts)

    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to clean markdown."""
        # Parse to clean up
        soup = BeautifulSoup(html, 'html.parser')

        # Remove scripts, styles
        for tag in soup.find_all(['script', 'style']):
            tag.decompose()

        # Convert to markdown
        markdown = md(str(soup), heading_style='ATX', bullets='-')

        # Clean up excessive whitespace
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        markdown = re.sub(r' {2,}', ' ', markdown)

        return markdown.strip()

    def list_sections(self) -> list[dict]:
        """List all sections with metadata."""
        return [
            {
                'id': s.id,
                'title': s.title,
                'schema_field': s.schema_field,
                'char_count': s.char_count,
                'is_small': s.is_small
            }
            for s in self._sections.values()
        ]

    def get_section(self, section_id: str) -> Optional[Section]:
        """Get a specific section by ID."""
        # Exact match
        if section_id in self._sections:
            return self._sections[section_id]

        # Partial match
        for sid, section in self._sections.items():
            if section_id.lower() in sid.lower():
                return section

        return None

    def get_sections_by_field(self, schema_field: str) -> list[Section]:
        """Get all sections that map to a schema field."""
        return [s for s in self._sections.values() if s.schema_field == schema_field]

    def extract_all(self) -> dict[str, str]:
        """Extract all sections as markdown."""
        return {s.id: s.markdown for s in self._sections.values()}

    def get_summary(self) -> str:
        """Get a summary of all sections."""
        lines = [f"# Sections in {self.path.name}\n"]

        total_chars = sum(s.char_count for s in self._sections.values())
        lines.append(f"Total: {len(self._sections)} sections, {total_chars:,} characters\n")

        # Group by schema field
        by_field: dict[str, list[Section]] = {}
        for section in self._sections.values():
            field = section.schema_field or "other"
            if field not in by_field:
                by_field[field] = []
            by_field[field].append(section)

        for field, sections in sorted(by_field.items()):
            lines.append(f"\n## {field}")
            for s in sections:
                size_indicator = "small" if s.is_small else "LARGE"
                lines.append(f"- `{s.id}`: {s.title} ({s.char_count:,} chars) [{size_indicator}]")

        return '\n'.join(lines)


@app.command()
def main(
    html_file: str = typer.Argument(..., help="Path to MIC HTML file"),
    section: Optional[str] = typer.Option(None, "--section", "-s", help="Extract specific section"),
    list_sections: bool = typer.Option(False, "--list", "-l", help="List all sections"),
    summary: bool = typer.Option(False, "--summary", help="Show section summary"),
    all_sections: bool = typer.Option(False, "--all", "-a", help="Extract all sections"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory for --all"),
    field: Optional[str] = typer.Option(None, "--field", "-f", help="Get sections by schema field"),
):
    """Extract sections from MIC HTML pages."""

    if not Path(html_file).exists():
        typer.echo(f"File not found: {html_file}", err=True)
        raise typer.Exit(1)

    extractor = MICSectionExtractor(html_file)

    if list_sections:
        for s in extractor.list_sections():
            field_str = f" -> {s['schema_field']}" if s['schema_field'] else ""
            typer.echo(f"{s['id']}: {s['title']} ({s['char_count']} chars){field_str}")
        return

    if summary:
        typer.echo(extractor.get_summary())
        return

    if field:
        sections = extractor.get_sections_by_field(field)
        if not sections:
            typer.echo(f"No sections found for field: {field}", err=True)
            raise typer.Exit(1)
        for s in sections:
            typer.echo(f"\n{'='*60}\n# {s.title} ({s.id})\n{'='*60}\n")
            typer.echo(s.markdown)
        return

    if section:
        s = extractor.get_section(section)
        if not s:
            typer.echo(f"Section not found: {section}", err=True)
            typer.echo("Available sections:")
            for sec in extractor.list_sections():
                typer.echo(f"  - {sec['id']}")
            raise typer.Exit(1)
        typer.echo(s.markdown)
        return

    if all_sections:
        output_dir = Path(output) if output else Path(f"cache/sections/{Path(html_file).stem}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write summary
        summary_path = output_dir / "summary.md"
        summary_path.write_text(extractor.get_summary(), encoding='utf-8')
        typer.echo(f"Wrote: {summary_path}")

        # Write each section
        for section_id, markdown in extractor.extract_all().items():
            section_path = output_dir / f"{section_id}.md"
            section_path.write_text(markdown, encoding='utf-8')
            typer.echo(f"Wrote: {section_path}")

        typer.echo(f"\nExtracted {len(extractor._sections)} sections to {output_dir}")
        return

    # Default: show summary
    typer.echo(extractor.get_summary())


if __name__ == '__main__':
    app()
