# mic-ingest

| [Documentation](https://monarch-initiative.github.io/mic-ingest) |

Ingest for Micronutrient Information Center using OntoGPT

## Requirements

- Python >= 3.10
- [Poetry](https://python-poetry.org/docs/#installation)
- [Cruft](https://cruft.github.io/cruft/#installation) (optional)


# Setting Up a New Project -- Delete this section when completed

Upon creating a new project from the `cookiecutter-monarch-ingest` template, you can install and test the project:

```bash
cd mic-ingest
make install
make test
```

There are a few additional steps to complete before the project is ready for use.

#### GitHub Repository

1. Create a new repository on GitHub.
1. Enable GitHub Actions to read and write to the repository (required to deploy the project to GitHub Pages).
   - in GitHub, go to Settings -> Action -> General -> Workflow permissions and choose read and write permissions
1. Initialize the local repository and push the code to GitHub. For example:

   ```bash
   cd mic-ingest
   git init
   git remote add origin https://github.com/<username>/<repository>.git
   git add -A && git commit -m "Initial commit"
   git push -u origin main
   ```

#### Transform Code and Configuration

1. Edit the `download.yaml`, `transform.py`, `transform.yaml`, and `metadata.yaml` files to suit your needs.
   - For more information, see the [Koza documentation](https://koza.monarchinitiative.org) and [kghub-downloader](https://github.com/monarch-initiative/kghub-downloader).
1. Add any additional dependencies to the `pyproject.toml` file.
1. Adjust the contents of the `tests` directory to test the functionality of your transform.

#### Documentation

1. Update this `README.md` file with any additional information about the project.
1. Add any appropriate documentation to the `docs` directory.

> **Note:** After the GitHub Actions for deploying documentation runs, the documentation will be automatically deployed to GitHub Pages.  
> However, you will need to go to the repository settings and set the GitHub Pages source to the `gh-pages` branch, using the `/docs` directory.

Once you have completed these steps, you can remove the [Setting Up a New Project](#setting-up-a-new-project) section from this `README.md` file.

## Data Sources
Update this section to describe the source of the data for the ingest. Include information about the projects and groups that create or curate the data, which data files are used, and the specific sources and/or versions of those files. It is also valuable to document what model is used for the ingest (generally the Biolink Model) and what types of nodes and edges are created. Here is an example of how you might document this:

Data files for YOUR_SOURCE_DATA_TYPE are available from GROUP_OR_PROJECT through there portal at (include links where possible).

### Source Files
This ingest relies on N data files from GROUP_OR_PROJECT and one additional data file for FILE_USAGE (often mapping) from OTHER_GROUP_OR_PROJECT.
  - FILENAME_1 - Describe the data in the file and give a basic description of how it's used. It's nice to include the URL's here as well as having them in the downloads.yaml later

### Nodes and Edges
Use this section describe the nodes and edges generated from the ingest for instance
 - Gene Nodes - Description of which nodes are created and what data may be excluded from the ingest.
 - Gene → Disease - Similar description of the edges and which edges are created or how the data may be filtered.

## Transform Code and Configuration
Metadata for the infest is in the `metadata.yaml` file and may require some adjustment depending on your configuration. Data files and locations are listed in the `download.yaml` file which is used to download all of the data sources before the transform. The `transform.yaml` file and python file `transform.py` contain the configuration and transformation code, respectively. 

For more information, see the [Koza documentation](https://koza.monarchinitiative.org) and [kghub-downloader](https://github.com/monarch-initiative/kghub-downloader).

Dependencies are listed in `pyproject.toml` file. This project uses pytest for development testing located in the `tests` directory to test the functionality of your transform.

## Documentation
The documentation for this ingest is in this `README.md` file and additional documentation is in the `docs` directory.

> **Note:** After the GitHub Actions for deploying documentation runs, the documentation will be automatically deployed to GitHub Pages.  

#### GitHub Actions

This project is set up with several GitHub Actions workflows.
You should not need to modify these workflows unless you want to change the behavior.
The workflows are located in the `.github/workflows` directory:

- `test.yaml`: Run the pytest suite.
- `create-release.yaml`: Create a new release once a week, or manually.
- `deploy-docs.yaml`: Deploy the documentation to GitHub Pages (on pushes to main).
- `update-docs.yaml`: After a release, update the documentation with node/edge reports.

## Installation

```bash
cd mic-ingest
make install
# or
poetry install
```

> **Note** that the `make install` command is just a convenience wrapper around `poetry install`.

Once installed, you can check that everything is working as expected:

```bash
# Run the pytest suite
make test
# Download the data and run the Koza transform
make download
make run
```

## Usage

This project is set up with a Makefile for common tasks.  
To see available options:

```bash
make help
```

### Download and Transform

Download the data for the mic_ingest transform:

```bash
poetry run mic_ingest download
```

To run the Koza transform for mic-ingest:

```bash
poetry run mic_ingest transform
```

To see available options:

```bash
poetry run mic_ingest download --help
# or
poetry run mic_ingest transform --help
```

### Testing

To run the test suite:

```bash
make test
```

---

> This project was generated using [monarch-initiative/cookiecutter-monarch-ingest](https://github.com/monarch-initiative/cookiecutter-monarch-ingest).  
> Keep this project up to date using cruft by occasionally running in the project directory:
>
> ```bash
> cruft update
> ```
>
> For more information, see the [cruft documentation](https://cruft.github.io/cruft/#updating-a-project)
