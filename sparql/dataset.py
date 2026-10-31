from __future__ import annotations

from pathlib import Path

from pyoxigraph import DefaultGraph, NamedNode, RdfFormat, Store

GRAPH_IRIS = {
    "buildings": "https://ecosystem-training.local/graphs/buildings",
    "measurements": "https://ecosystem-training.local/graphs/measurements",
    "weather": "https://ecosystem-training.local/graphs/weather",
}


def load_s2_exports(output_dir: Path) -> Store:
    """Load each S2 N-Triples export into its corresponding Oxigraph named graph."""
    store = Store()
    expected_graphs = {NamedNode(iri) for iri in GRAPH_IRIS.values()}

    for graph_name, graph_iri in GRAPH_IRIS.items():
        path = output_dir / f"{graph_name}.nt"
        if not path.is_file():
            raise FileNotFoundError(f"Required S2 export is missing: {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Required S2 export is empty: {path}")
        try:
            store.load(
                path=path,
                format=RdfFormat.N_TRIPLES,
                to_graph=NamedNode(graph_iri),
            )
        except (OSError, SyntaxError, ValueError) as error:
            raise ValueError(f"Could not load S2 N-Triples export {path}: {error}") from error

    actual_graphs = set(store.named_graphs())
    if actual_graphs != expected_graphs:
        raise ValueError(
            "Loaded S2 exports do not contain exactly the expected named graphs: "
            f"{sorted(graph.value for graph in actual_graphs)}"
        )
    if next(store.quads_for_pattern(None, None, None, DefaultGraph()), None) is not None:
        raise ValueError("S2 exports unexpectedly populated the default graph")

    return store
