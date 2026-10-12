import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rdflib import Literal
from rdflib.namespace import RDF, XSD

from s2.named_graphs import (
    BASE,
    BUILDINGS_GRAPH,
    MEASUREMENTS_GRAPH,
    WEATHER_GRAPH,
    build_named_graphs,
    export_named_graphs,
    sha256_of_file,
)


def test_named_graphs_are_built_and_typed():
    metadata_path = Path(__file__).resolve().parents[1] / "data" / "metadata.csv"
    dataset = build_named_graphs(metadata_path)

    buildings_graph = dataset.get_context(BUILDINGS_GRAPH)
    weather_graph = dataset.get_context(WEATHER_GRAPH)
    measurements_graph = dataset.get_context(MEASUREMENTS_GRAPH)

    assert len(buildings_graph) > 0
    assert len(weather_graph) > 0
    assert len(measurements_graph) > 0

    first_building = next(iter(buildings_graph.subjects(RDF.type, BASE.Building)))
    building_area = next(buildings_graph.objects(first_building, BASE.hasArea))
    assert isinstance(building_area, Literal)
    assert building_area.datatype == XSD.float

    # assert any(graph for graph in dataset.contexts())
    assert any(graph for graph in dataset.graphs())  # Use .graphs() for Dataset



def test_nt_exports_are_stable_and_hashable(tmp_path):
    metadata_path = Path(__file__).resolve().parents[1] / "data" / "metadata.csv"
    dataset = build_named_graphs(metadata_path)

    first_exports = export_named_graphs(dataset, tmp_path / "first")
    second_exports = export_named_graphs(dataset, tmp_path / "second")

    assert set(first_exports) == set(second_exports)
    for name in first_exports:
        original_hash = first_exports[name]["sha256"]
        repeated_hash = sha256_of_file(Path(second_exports[name]["path"]))
        assert original_hash == repeated_hash
        assert Path(first_exports[name]["path"]).read_text(encoding="utf-8").endswith("\n")


def test_graph_contexts_are_named():
    metadata_path = Path(__file__).resolve().parents[1] / "data" / "metadata.csv"
    dataset = build_named_graphs(metadata_path)

    # names = {str(context.identifier) for context in dataset.contexts()}
    names = {str(graph.identifier) for graph in dataset.graphs()}  # Use .graphs() for Dataset
    assert str(BUILDINGS_GRAPH) in names
    assert str(WEATHER_GRAPH) in names
    assert str(MEASUREMENTS_GRAPH) in names
