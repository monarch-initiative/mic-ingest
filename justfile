# MIC-Ingest Justfile
# Commands for managing the Micronutrient Information Center knowledge base

# Default recipe - show available commands
default:
    @just --list

# =============================================================================
# SETUP
# =============================================================================

# Install dependencies
install:
    uv sync

# Install development dependencies
install-dev:
    uv sync --all-extras

# =============================================================================
# VALIDATION
# =============================================================================

# Validate a single nutrient YAML file against the schema
validate file:
    uv run linkml-validate \
        --schema src/mic_ingest/schema/mic.yaml \
        --target-class Nutrient \
        {{file}}

# Validate all nutrient YAML files
validate-all:
    #!/usr/bin/env bash
    set -e
    for f in kb/nutrients/**/*.yaml; do
        if [ -f "$f" ]; then
            echo "Validating $f..."
            just validate "$f"
        fi
    done
    echo "All files validated successfully!"

# Validate ontology terms in a file (anti-hallucination check)
validate-terms-file file:
    uv run linkml-term-validator validate-data \
        --schema src/mic_ingest/schema/mic.yaml \
        --target-class Nutrient \
        --config conf/oak_config.yaml \
        --labels \
        {{file}}

# Validate ontology terms in all files
validate-terms:
    #!/usr/bin/env bash
    set -e
    for f in kb/nutrients/**/*.yaml; do
        if [ -f "$f" ]; then
            echo "Validating terms in $f..."
            just validate-terms-file "$f"
        fi
    done
    echo "All term validations complete!"

# Validate references/snippets in a file
validate-references file:
    uv run linkml-reference-validator validate data {{file}} \
        --schema src/mic_ingest/schema/mic.yaml \
        --target-class Nutrient

# Validate references in all files
validate-references-all:
    #!/usr/bin/env bash
    set -e
    for f in kb/nutrients/**/*.yaml; do
        if [ -f "$f" ]; then
            echo "Validating references in $f..."
            just validate-references "$f" || true
        fi
    done
    echo "Reference validation complete!"

# Run all QC checks (schema + terms + references)
qc:
    #!/usr/bin/env bash
    set -e
    echo "=== Schema Validation ==="
    just validate-all
    echo ""
    echo "=== Term Validation ==="
    just validate-terms || echo "Term validation had issues"
    echo ""
    echo "=== Reference Validation ==="
    just validate-references-all || echo "Reference validation had issues"
    echo ""
    echo "=== QC Complete ==="

# =============================================================================
# COMPLIANCE
# =============================================================================

# Check compliance of a single file
compliance file:
    uv run linkml-data-qc analyze {{file}} \
        --schema src/mic_ingest/schema/mic.yaml \
        --target-class Nutrient

# Check compliance of all files
compliance-all:
    #!/usr/bin/env bash
    for f in kb/nutrients/**/*.yaml; do
        if [ -f "$f" ]; then
            echo "=== $f ==="
            just compliance "$f" || true
            echo ""
        fi
    done

# Check compliance with weighted scoring
compliance-weighted:
    uv run linkml-data-qc analyze kb/nutrients/**/*.yaml \
        --schema src/mic_ingest/schema/mic.yaml \
        --target-class Nutrient \
        --config conf/qc_config.yaml

# Generate compliance CSV report
compliance-csv:
    uv run linkml-data-qc analyze kb/nutrients/**/*.yaml \
        --schema src/mic_ingest/schema/mic.yaml \
        --target-class Nutrient \
        --output-format csv \
        > reports/compliance.csv

# Generate compliance JSON report
compliance-report:
    uv run linkml-data-qc analyze kb/nutrients/**/*.yaml \
        --schema src/mic_ingest/schema/mic.yaml \
        --target-class Nutrient \
        --output-format json

# Generate visual compliance dashboard
gen-dashboard:
    mkdir -p dashboard
    uv run linkml-data-qc dashboard kb/nutrients/**/*.yaml \
        --schema src/mic_ingest/schema/mic.yaml \
        --target-class Nutrient \
        --output dashboard/index.html

# =============================================================================
# REFERENCES
# =============================================================================

# Fetch a reference abstract from PubMed
fetch-reference pmid:
    #!/usr/bin/env bash
    mkdir -p cache/references
    pmid_clean=$(echo "{{pmid}}" | sed 's/PMID://')
    output_file="cache/references/pmid_${pmid_clean}.md"

    echo "Fetching PMID:${pmid_clean}..."

    # Use NCBI E-utilities to fetch abstract
    url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=${pmid_clean}&rettype=abstract&retmode=text"
    curl -s "$url" > "$output_file"

    echo "Saved to $output_file"
    cat "$output_file"

# Repair references in a file (auto-fix minor mismatches)
repair-references file:
    uv run linkml-reference-validator repair data {{file}} \
        --schema src/mic_ingest/schema/mic.yaml \
        --target-class Nutrient \
        --no-dry-run \
        --fix-threshold 0.80

# =============================================================================
# MIC PAGE HANDLING
# =============================================================================

# Fetch a MIC page and cache it
fetch-mic-page path:
    #!/usr/bin/env bash
    mkdir -p cache/mic-pages
    url="https://lpi.oregonstate.edu/mic/{{path}}"
    output_file="cache/mic-pages/$(basename {{path}}).html"

    echo "Fetching $url..."
    curl -s "$url" > "$output_file"
    echo "Saved to $output_file"

# Extract references from a cached MIC page to TSV
extract-refs file:
    uv run python scripts/fetch-references.py extract {{file}} --from-file

# Extract references and save to cache
extract-refs-save file:
    #!/usr/bin/env bash
    mkdir -p cache/mic-refs
    basename=$(basename {{file}} .html)
    output="cache/mic-refs/${basename}-refs.tsv"
    uv run python scripts/fetch-references.py extract {{file}} --from-file -o "$output"
    echo "Saved to $output"

# Fetch all PubMed abstracts for a references TSV file
fetch-all-abstracts refs_file:
    uv run python scripts/fetch-references.py fetch-abstracts {{refs_file}}

# =============================================================================
# SECTION EXTRACTION
# =============================================================================

# List all sections in a MIC HTML file
list-sections file:
    uv run python scripts/extract-sections.py {{file}} --list

# Get summary of sections in a MIC HTML file
sections-summary file:
    uv run python scripts/extract-sections.py {{file}} --summary

# Extract a specific section from a MIC HTML file
extract-section file section:
    uv run python scripts/extract-sections.py {{file}} --section {{section}}

# Extract all sections to cache directory
extract-sections file:
    #!/usr/bin/env bash
    basename=$(basename {{file}} .html)
    output_dir="cache/sections/${basename}"
    uv run python scripts/extract-sections.py {{file}} --all --output "$output_dir"

# Extract sections for a schema field (function, deficiency, etc.)
extract-field file field:
    uv run python scripts/extract-sections.py {{file}} --field {{field}}

# =============================================================================
# RENDERING
# =============================================================================

# Render a single nutrient to HTML
render file:
    uv run python -m mic_ingest.render {{file}}

# Render all nutrients to HTML
render-all:
    uv run python -m mic_ingest.render --all

# =============================================================================
# EXPORT
# =============================================================================

# Export to KGX format (nodes and edges JSONL)
export-kgx:
    mkdir -p output/kgx
    uv run koza transform src/mic_ingest/export/kgx_export.py -o output/kgx -f jsonl kb/nutrients/*/*.yaml
    mv output/kgx/kgx_export_nodes.jsonl output/kgx/mic_nodes.jsonl
    mv output/kgx/kgx_export_edges.jsonl output/kgx/mic_edges.jsonl

# Export to JSON for browser
export-json:
    uv run python -m mic_ingest.export.browser

# =============================================================================
# SCHEMA
# =============================================================================

# Generate Python dataclasses from schema
gen-python:
    gen-python src/mic_ingest/schema/mic.yaml > src/mic_ingest/datamodel/mic.py

# Generate JSON Schema from LinkML
gen-jsonschema:
    gen-json-schema src/mic_ingest/schema/mic.yaml > src/mic_ingest/schema/mic.schema.json

# Generate documentation
gen-docs:
    gen-doc -d docs/schema src/mic_ingest/schema/mic.yaml

# =============================================================================
# TESTING
# =============================================================================

# Run pytest
test:
    uv run pytest tests/ -v

# Run pytest with coverage
test-cov:
    uv run pytest tests/ -v --cov=mic_ingest --cov-report=html

# =============================================================================
# UTILITIES
# =============================================================================

# List all nutrient files
list-nutrients:
    @find kb/nutrients -name "*.yaml" | sort

# Count nutrients by category
count-nutrients:
    @echo "Vitamins: $(find kb/nutrients/vitamins -name '*.yaml' 2>/dev/null | wc -l | tr -d ' ')"
    @echo "Minerals: $(find kb/nutrients/minerals -name '*.yaml' 2>/dev/null | wc -l | tr -d ' ')"
    @echo "Dietary Factors: $(find kb/nutrients/dietary-factors -name '*.yaml' 2>/dev/null | wc -l | tr -d ' ')"
    @echo "Food/Beverages: $(find kb/nutrients/food-beverages -name '*.yaml' 2>/dev/null | wc -l | tr -d ' ')"

# Clean generated files
clean:
    rm -rf cache/references/*
    rm -rf cache/mic-pages/*
    rm -rf dashboard/*
    rm -rf pages/nutrients/*
    rm -rf reports/*

# OAK helper - lookup a term
oak-lookup ontology term:
    uv run runoak -i sqlite:obo:{{ontology}} info "{{term}}"

# OAK helper - fuzzy search
oak-search ontology term:
    uv run runoak -i sqlite:obo:{{ontology}} info "l~{{term}}"
