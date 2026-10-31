import csv
import os
import subprocess
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from s2.named_graphs import (
    BASE,
    BUILDINGS_GRAPH,
    GRAPH_EXPORTS,
    MEASUREMENTS_GRAPH,
    PERIOD_END,
    PERIOD_START,
    SELECTED_BUILDINGS,
    WEATHER_GRAPH,
    build_named_graphs,
    export_named_graphs,
    sha256_of_file,
)

DATA = ROOT / "data"
METADATA_PATH = DATA / "metadata.csv"
ELECTRICITY_PATH = DATA / "meters" / "cleaned" / "electricity_cleaned.csv"
WEATHER_PATH = DATA / "weather" / "weather.csv"


def _literal(value: str, datatype: URIRef) -> Literal:
    return Literal(Decimal(value), datatype=datatype, normalize=False)


def test_named_graphs_contain_observed_month_of_data():
    dataset = build_named_graphs(METADATA_PATH)
    buildings_graph = dataset.graph(BUILDINGS_GRAPH)
    measurements_graph = dataset.graph(MEASUREMENTS_GRAPH)
    weather_graph = dataset.graph(WEATHER_GRAPH)

    nonempty_graphs = {
        graph.identifier for graph in dataset.graphs() if len(graph) > 0
    }
    assert nonempty_graphs == set(GRAPH_EXPORTS.values())

    building_uris = {
        BASE[f"building/{building_id.lower()}"] for building_id in SELECTED_BUILDINGS
    }
    assert set(buildings_graph.subjects(RDF.type, BASE.Building)) == building_uris
    assert all(
        (building_uri, BASE.belongsToSite, BASE["site/robin"]) in buildings_graph
        for building_uri in building_uris
    )
    assert all(
        isinstance(area, Literal) and area.datatype == XSD.decimal
        for area in buildings_graph.objects(None, BASE.hasArea)
    )

    readings = set(measurements_graph.subjects(RDF.type, BASE.ElectricityReading))
    assert len(readings) == len(SELECTED_BUILDINGS) * 744
    timestamps = set(measurements_graph.objects(None, BASE.observedAt))
    expected_timestamps = {
        Literal(
            (PERIOD_START + timedelta(hours=hour)).isoformat(timespec="seconds"),
            datatype=XSD.dateTime,
            normalize=False,
        )
        for hour in range(int((PERIOD_END - PERIOD_START).total_seconds() // 3600))
    }
    assert timestamps == expected_timestamps
    assert all(
        isinstance(value, Literal) and value.datatype == XSD.decimal
        for value in measurements_graph.objects(None, BASE.electricityValue)
    )

    for building_id in SELECTED_BUILDINGS:
        building_uri = BASE[f"building/{building_id.lower()}"]
        meter_uri = BASE[f"meter/{building_id.lower()}/electricity"]
        assert (meter_uri, RDF.type, BASE.ElectricityMeter) in measurements_graph
        assert (meter_uri, BASE.meterForBuilding, building_uri) in measurements_graph
        assert any(
            (reading, BASE.forBuilding, building_uri) in measurements_graph
            and (reading, BASE.meter, meter_uri) in measurements_graph
            for reading in readings
        )

    with ELECTRICITY_PATH.open(newline="", encoding="utf-8-sig") as source:
        first_electricity = next(csv.DictReader(source))
    for building_id in SELECTED_BUILDINGS:
        expected_value = _literal(first_electricity[building_id], XSD.decimal)
        reading_uri = BASE[
            f"reading/{building_id.lower()}/{PERIOD_START.isoformat()}"
        ]
        assert (reading_uri, BASE.electricityValue, expected_value) in measurements_graph

    observations = set(weather_graph.subjects(RDF.type, BASE.WeatherObservation))
    assert len(observations) == 744
    assert set(weather_graph.objects(None, BASE.observedAt)) == expected_timestamps
    assert all(
        (observation, BASE.atSite, BASE["site/robin"]) in weather_graph
        for observation in observations
    )
    assert all(
        isinstance(value, Literal) and value.datatype == XSD.decimal
        for value in weather_graph.objects(None, BASE.airTemperature)
    )
    with WEATHER_PATH.open(newline="", encoding="utf-8-sig") as source:
        matching_weather = next(
            row
            for row in csv.DictReader(source)
            if row["site_id"] == "Robin"
            and row["timestamp"] == first_electricity["timestamp"]
        )
    observation_uri = BASE[
        f"weather_observation/robin/{PERIOD_START.isoformat()}"
    ]
    assert (
        observation_uri,
        BASE.airTemperature,
        _literal(matching_weather["airTemperature"], XSD.decimal),
    ) in weather_graph


def test_nt_exports_are_stable_and_only_export_named_graphs(tmp_path):
    dataset = build_named_graphs(METADATA_PATH)
    first_exports = export_named_graphs(dataset, tmp_path / "first")
    second_exports = export_named_graphs(dataset, tmp_path / "second")

    assert set(first_exports) == {"buildings", "measurements", "weather"}
    assert set(first_exports) == set(second_exports)
    assert {path.name for path in (tmp_path / "first").iterdir()} == {
        "buildings.nt",
        "measurements.nt",
        "weather.nt",
    }
    assert not (tmp_path / "first" / "urn:x-rdflib:default.nt").exists()
    for name in first_exports:
        first_path = Path(first_exports[name]["path"])
        second_path = Path(second_exports[name]["path"])
        assert first_exports[name]["sha256"] == sha256_of_file(second_path)
        assert second_exports[name]["sha256"] == sha256_of_file(first_path)
        lines = first_path.read_text(encoding="utf-8").splitlines()
        assert lines == sorted(lines)
        assert len(Graph().parse(first_path, format="nt")) == len(
            dataset.graph(GRAPH_EXPORTS[name])
        )
        assert first_path.read_text(encoding="utf-8").endswith("\n")


def test_missing_electricity_values_raise_instead_of_being_filled(tmp_path):
    electricity_path = tmp_path / "electricity.csv"
    with electricity_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["timestamp", *SELECTED_BUILDINGS])
        writer.writerow(["2016-01-01 00:00:00", "", "14.3", "52.25"])

    with pytest.raises(ValueError, match="Missing numeric value in electricity meter"):
        build_named_graphs(METADATA_PATH, electricity_path=electricity_path)


def test_missing_weather_hours_raise_instead_of_being_filled(tmp_path):
    weather_path = tmp_path / "weather.csv"
    with weather_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=["timestamp", "site_id", "airTemperature"])
        writer.writeheader()
        writer.writerow(
            {"timestamp": "2016-01-01 00:00:00", "site_id": "Robin", "airTemperature": "3.8"}
        )

    with pytest.raises(ValueError, match="Incomplete weather coverage for Robin: 743 missing"):
        build_named_graphs(METADATA_PATH, weather_path=weather_path)


def test_import_does_not_write_exports(tmp_path):
    environment = {**os.environ, "PYTHONPATH": str(ROOT)}
    subprocess.run(
        [sys.executable, "-c", "import s2.named_graphs"],
        cwd=tmp_path,
        env=environment,
        check=True,
    )
    assert not (tmp_path / "s2" / "output").exists()
