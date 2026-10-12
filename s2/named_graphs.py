#%% Imports 
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, Tuple

import pandas as pd
from rdflib import ConjunctiveGraph, Graph, Literal, Namespace, URIRef
from rdflib import Dataset # Replaces ConjunctiveGraph in newer versions of rdflib
from rdflib.namespace import RDF, XSD


#%% Constants
# RDF namespace for the project
BASE = Namespace("https://ecosystem-training.local/")
# Named graph URIs
BUILDINGS_GRAPH = URIRef(BASE + "graphs/buildings")
WEATHER_GRAPH = URIRef(BASE + "graphs/weather")
MEASUREMENTS_GRAPH = URIRef(BASE + "graphs/measurements")



#%% Helper Functions

# Normalize a string to create a valid identifier for URIs
def normalize_identifier(value: object) -> str:
    text = str(value).strip().replace("/", "_").replace(" ", "_").replace("-", "_").lower()
    return text or "unknown"


# Convert an RDF value to its N-Triples representation
def _nt_value(value: object) -> str:
    if isinstance(value, URIRef):
        return f"<{value}>"
    if isinstance(value, Literal):
        lexical = value.toPython()
        if value.datatype is not None:
            return f'"{str(lexical)}"^^<{value.datatype}>'
        if value.language:
            return f'"{str(lexical)}"@{value.language}'
        return f'"{str(lexical)}"'
    raise TypeError(f"Unsupported RDF value: {type(value)!r}")


# Sort triples in a graph for consistent serialization
def _sort_triples(graph: Graph) -> Iterable[Tuple[URIRef, URIRef, object]]:
    return sorted(graph, key=lambda triple: (str(triple[0]), str(triple[1]), str(triple[2])))


# Serialize a graph to N-Triples format and write to a file
def serialize_graph_to_nt(graph: Graph, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for subject, predicate, obj in _sort_triples(graph):
        lines.append(f"{_nt_value(subject)} {_nt_value(predicate)} {_nt_value(obj)} .")
    destination.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


# Compute the SHA-256 hash of a file's contents
def sha256_of_file(path: Path) -> str:
    digest = sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()



# Build named graphs from metadata
def build_named_graphs(metadata_path: Path) -> ConjunctiveGraph:
    df = pd.read_csv(metadata_path)
    sample = df.head(10).copy()

    # Create a ConjunctiveGraph to hold multiple named graphs
    # dataset = ConjunctiveGraph()
    dataset = Dataset()  # Use Dataset for newer versions of rdflib

    buildings_graph = dataset.get_context(BUILDINGS_GRAPH)
    weather_graph = dataset.get_context(WEATHER_GRAPH)
    measurements_graph = dataset.get_context(MEASUREMENTS_GRAPH)


    # Add building and site information to the buildings graph
    site_ids = sample["site_id"].dropna().unique().tolist()
    for _, row in sample.iterrows():
        building_id = str(row["building_id"]) if pd.notna(row["building_id"]) else "unknown"
        site_id = str(row["site_id"]) if pd.notna(row["site_id"]) else "unknown"
        building_uri = URIRef(BASE + f"building/{normalize_identifier(building_id)}")
        site_uri = URIRef(BASE + f"site/{normalize_identifier(site_id)}")
        buildings_graph.add((building_uri, RDF.type, BASE.Building))
        buildings_graph.add((site_uri, RDF.type, BASE.Site))
        buildings_graph.add((building_uri, BASE.belongsToSite, site_uri))

        # Add area information if available
        if pd.notna(row["sqm"]):
            buildings_graph.add((building_uri, BASE.hasArea, Literal(float(row["sqm"]), datatype=XSD.float)))

        # Add primary space usage information if available
        usage_value = row["primaryspaceusage"]
        if pd.notna(usage_value):
            usage_uri = URIRef(BASE + f"usage/{normalize_identifier(usage_value)}")
            buildings_graph.add((usage_uri, RDF.type, BASE.PrimarySpaceUsage))
            buildings_graph.add((building_uri, BASE.hasUsage, usage_uri))


    # Add weather information to the weather graph
    for index, site_id in enumerate(site_ids[:3]): # Limit to first 3 sites for demonstration
        site_uri = URIRef(BASE + f"site/{normalize_identifier(site_id)}")
        station_uri = URIRef(BASE + f"weather_station/{normalize_identifier(site_id)}")
        weather_graph.add((station_uri, RDF.type, BASE.WeatherStation))
        weather_graph.add((station_uri, BASE.atSite, site_uri))

        for day in range(1, 4): # Limit to first 3 days for demonstration
            observation_uri = URIRef(BASE + f"weather_observation/{normalize_identifier(site_id)}/{day}")
            temperature = 18.0 + (index * 2.5) + day 
            weather_graph.add((observation_uri, RDF.type, BASE.WeatherObservation))
            weather_graph.add((observation_uri, BASE.atSite, site_uri))
            weather_graph.add((observation_uri, BASE.temperatureCelsius, Literal(temperature, datatype=XSD.float)))

    
    # Add electricity readings to the measurements graph
    for index, building_id in enumerate(sample["building_id"].head(3).tolist()):
        normalized_building = normalize_identifier(building_id)
        building_uri = URIRef(BASE + f"building/{normalized_building}")
        meter_uri = URIRef(BASE + f"meter/{normalized_building}/electricity")
        for hour in range(3): # Limit to first 3 hours for demonstration
            reading_uri = URIRef(BASE + f"reading/{normalized_building}/{hour}")
            value = 42.0 + index * 8.5 + hour # Generate a sample reading value
            measurements_graph.add((reading_uri, RDF.type, BASE.ElectricityReading))
            measurements_graph.add((reading_uri, BASE.forBuilding, building_uri))
            measurements_graph.add((reading_uri, BASE.meter, meter_uri))
            measurements_graph.add((reading_uri, BASE.kwh, Literal(value, datatype=XSD.float)))

    return dataset


# Export named graphs to N-Triples files and compute their SHA-256 hashes
def export_named_graphs(dataset: ConjunctiveGraph, output_dir: Path) -> Dict[str, Dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    exports: Dict[str, Dict[str, str]] = {}

    # for graph in dataset.contexts():
    for graph in dataset.graphs():  # Use .graphs() for Dataset
        if str(graph.identifier) == "urn:x-rdflib:default": # Validate only when using Dataset, skip the default graph
            continue  # Skip the default graph

        graph_name = str(graph.identifier).split("/")[-1]
        path = output_dir / f"{graph_name}.nt"
        serialize_graph_to_nt(graph, path)
        exports[graph_name] = {
            "path": str(path),
            "sha256": sha256_of_file(path),
        }

    return exports


# %% Main Execution
# def main() -> None:
#     project_root = Path(__file__).resolve().parents[1]
#     metadata_path = project_root / "data" / "metadata.csv"
#     output_dir = Path(__file__).resolve().parent / "output"

#     dataset = build_named_graphs(metadata_path)
#     exports = export_named_graphs(dataset, output_dir)

#     print("Named graph exports generated:")
#     for graph_name, info in sorted(exports.items()):
#         print(f"- {graph_name}: {info['path']} (sha256={info['sha256']})")


# if __name__ == "__main__":
#     main()

project_root = Path(__file__).resolve().parents[1]          # Get the project root directory (two levels up from the current file)
metadata_path = project_root / "data" / "metadata.csv"      # Get the path to the metadata CSV file
output_dir = Path(__file__).resolve().parent / "output"     # Get the output directory (same level as the current file, in a folder named "output")

dataset = build_named_graphs(metadata_path)
exports = export_named_graphs(dataset, output_dir)

print("Named graph exports generated:")
for graph_name, info in sorted(exports.items()):
    print(f"- {graph_name}: {info['path']} (sha256={info['sha256']})")

