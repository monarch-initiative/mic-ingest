ROOTDIR = $(shell pwd)
RUN = poetry run
VERSION = $(shell poetry -C src/mic_ingest version -s)

### Help ###

define HELP
╭───────────────────────────────────────────────────────────╮
  Makefile for mic_ingest			    
│ ───────────────────────────────────────────────────────── │
│ Usage:                                                    │
│     make <target>                                         │
│                                                           │
│ Targets:                                                  │
│     help                Print this help message           │
│                                                           │
│     all                 Install everything and test       │
│     fresh               Clean and install everything      │
│     clean               Clean up build artifacts          │
│     clobber             Clean up generated files          │
│                                                           │
│     install             Poetry install package            │
│     download            Download data                     │
│     run                 Run the transform                 │
│                                                           │
│     docs                Generate documentation            │
│                                                           │
│     test                Run all tests                     │
│                                                           │
│     lint                Lint all code                     │
│     format              Format all code                   │
╰───────────────────────────────────────────────────────────╯
endef
export HELP

.PHONY: help
help:
	@printf "$${HELP}"


### Installation and Setup ###

.PHONY: fresh
fresh: clean clobber all

.PHONY: all
all: install test

.PHONY: install
install: 
	poetry install --with dev


### Documentation ###

.PHONY: docs
docs:
	$(RUN) mkdocs build


### Testing ###

.PHONY: test
test: 
	$(RUN) pytest tests

### Download and Preprocess

DOWNLOAD_DIR ?= data
OUTPUT_DIR ?= output
URI_BASE := https://lpi.oregonstate.edu/mic

CATEGORIES ?= vitamins \
	     minerals \
	     dietary-factors \
		 food-beverages \
		 health-disease

GREP_PATTERNS = $(foreach category,$(CATEGORIES),-e '$(category)/.*')
TARGET_RESOURCES = $(shell grep -o $(GREP_PATTERNS) mic_pages.txt)
HTML_OUTPUT = $(foreach resource,$(TARGET_RESOURCES),$(DOWNLOAD_DIR)/$(resource).html)
JSON_OUTPUT = $(foreach resource,$(TARGET_RESOURCES),$(OUTPUT_DIR)/$(resource).json)
REFERENCE_OUTPUT = $(foreach resource,$(TARGET_RESOURCES),$(OUTPUT_DIR)/references/$(resource).tsv)

.PHONY: create_output
create_output: $(JSON_OUTPUT) $(OUTPUT_DIR)/references.tsv

# .PRECIOUS: $(DOWNLOAD_DIR)/%.html:
# $(DOWNLOAD_DIR)/%.html:
# 	mkdir -p $(dir $@)
# 	wget $(URI_BASE)/$* -O $@


$(OUTPUT_DIR)/references/%.tsv: 
	mkdir -p $(dir $@)
	$(RUN) python scripts/fetch-references.py $(URI_BASE)/$* > $@

# Merge all the references into a single tsv file
$(OUTPUT_DIR)/references.tsv: $(REFERENCE_OUTPUT)
	mkdir -p $(dir $@)
	@echo appending header from $(firstword $^)
	head -n 1 $(firstword $^) > $@  # Add header from the first file
	tail -n +2 -q $^ >> $@  # Append the rest of the files without their headers

# Note: $* is the name of the category, $@ is the name of the json file, $< is
# the name of the downloaded HTML file
$(OUTPUT_DIR)/%.json: $(OUTPUT_DIR)/references/%.tsv 
	mkdir -p $(dir $@)
	ontogpt web-extract -O json -t mic $(URI_BASE)/$* -o $@
	jq '. += {"source_url": "$(URI_BASE)/$*"}' $@ > $@.tmp
	mv $@.tmp $@

$(OUTPUT_DIR)/tsv/raw_associations.tsv: $(OUTPUT_DIR)/references.tsv	
	$(RUN) python scripts/json-extract.py 

### Running ###

.PHONY: download
download:
	$(RUN) ingest download

.PHONY: run
run: download
	$(RUN) ingest transform
	$(RUN) python scripts/generate-report.py


### Linting, Formatting, and Cleaning ###

.PHONY: clean
clean:
	rm -f `find . -type f -name '*.py[co]' `
	rm -rf `find . -name __pycache__` \
		.venv .ruff_cache .pytest_cache **/.ipynb_checkpoints

.PHONY: clobber
clobber:
	# Add any files to remove here
	@echo "Nothing to remove. Add files to remove to clobber target."

.PHONY: lint
lint: 
	$(RUN) ruff check --diff --exit-zero
	$(RUN) black -l 120 --check --diff src tests

.PHONY: format
format: 
	$(RUN) ruff check --fix --exit-zero
	$(RUN) black -l 120 src tests
