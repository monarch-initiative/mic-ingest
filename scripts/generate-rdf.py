from pathlib import Path

from kgx.cli.cli_utils import transform as kgx_transform
from loguru import logger

logger.info(f"Creating rdf output: output/lpi_chemical_to_pathway.nt.gz ...")

src_files = []
src_nodes = f"output/lpi_chemical_to_pathway_nodes.tsv"
src_edges = f"output/lpi_chemical_to_pathway_edges.tsv"

if Path(src_nodes).is_file():
    src_files.append(src_nodes)
if Path(src_edges).is_file():
    src_files.append(src_edges)

kgx_transform(
    inputs=src_files,
    input_format="tsv",
    stream=True,
    output=f"output/lpi_chemical_to_pathway.nt.gz",
    output_format="nt",
    output_compression="gz",
)
