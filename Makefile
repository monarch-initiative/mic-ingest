ROOTDIR = $(shell pwd)
RUN = poetry run
VERSION = $(shell poetry -C src/mic_ingest version -s)

# logs if parsing errors or no references for debugging (cleans up with each new run)
QUALITY_DIR := quality_control
QC_REFERENCES := $(QUALITY_DIR)/missing_references.txt
QC_ONTOGPT := $(QUALITY_DIR)/ontogpt_failures.txt

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
create_output: clean_qc $(QUALITY_DIR) $(JSON_OUTPUT) $(OUTPUT_DIR)/references.tsv

# .PRECIOUS: $(DOWNLOAD_DIR)/%.html:
# $(DOWNLOAD_DIR)/%.html:
# 	mkdir -p $(dir $@)
# 	wget $(URI_BASE)/$* -O $@

.PHONY: clean_qc
clean_qc:
	rm -rf $(QUALITY_DIR)

$(QUALITY_DIR):
	mkdir -p $(QUALITY_DIR)

$(OUTPUT_DIR)/references/%.tsv: | $(QUALITY_DIR)
	mkdir -p $(dir $@)
	@if ! $(RUN) python scripts/fetch-references.py $(URI_BASE)/$* > $@ 2>> $(QC_REFERENCES); then \
		echo "$(URI_BASE)/$*" >> $(QC_REFERENCES); \
	elif [ $$(wc -l < $@) -le 1 ]; then \
		echo "$(URI_BASE)/$*" >> $(QC_REFERENCES); \
	fi

# Merge all the references into a single tsv file
$(OUTPUT_DIR)/references.tsv: $(REFERENCE_OUTPUT)
	mkdir -p $(dir $@)
	@echo appending header from $(firstword $^)
	head -n 1 $(firstword $^) > $@  # Add header from the first file
	tail -n +2 -q $^ >> $@  # Append the rest of the files without their headers

# Note: $* is the name of the category, $@ is the name of the json file, $< is
# the name of the downloaded HTML file
# anytime we face ERROR: we capture and write to QC_ONTOGPT
$(OUTPUT_DIR)/%.json: $(OUTPUT_DIR)/references/%.tsv | $(QUALITY_DIR)
	mkdir -p $(dir $@)
	@ontogpt web-extract -O json -t mic $(URI_BASE)/$* -o $@ 2> .ontogpt_tmp_log || \
		( echo "$(URI_BASE)/$*" >> $(QC_ONTOGPT); exit 0 )
	@if grep -q 'ERROR:' .ontogpt_tmp_log; then \
		echo "$(URI_BASE)/$*" >> $(QC_ONTOGPT); \
	else \
		if ! grep -q '"extracted_object"' $@; then \
			echo "$(URI_BASE)/$*" >> $(QC_ONTOGPT); \
		fi \
	fi
	@jq '. += {"source_url": "$(URI_BASE)/$*"}' $@ > $@.tmp && mv $@.tmp $@
	@rm -f .ontogpt_tmp_log

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
