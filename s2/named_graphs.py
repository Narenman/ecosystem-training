from __future__ import annotations

import csv
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path

from rdflib import Dataset, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

BASE = Namespace("https://ecosystem-training.local/")
BUILDINGS_GRAPH = URIRef(BASE + "graphs/buildings")
WEATHER_GRAPH = URIRef(BASE + "graphs/weather")
MEASUREMENTS_GRAPH = URIRef(BASE + "graphs/measurements")

PERIOD_START = datetime(2016, 1, 1)
PERIOD_END = datetime(2016, 2, 1)
SELECTED_BUILDINGS = (
    "Robin_public_Carolina",
    "Robin_lodging_Dorthy",
    "Robin_education_Zenia",
)

GRAPH_EXPORTS = {
    "buildings": BUILDINGS_GRAPH,
    "measurements": MEASUREMENTS_GRAPH,
    "weather": WEATHER_GRAPH,
}


def normalize_identifier(value: object) -> str:
    text = str(value).strip().replace("/", "_").replace(" ", "_").replace("-", "_").lower()
    return text or "unknown"


def _parse_datetime(value: str, *, source: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"Invalid timestamp in {source}: {value!r}") from error


def _parse_decimal(value: str | None, *, source: str) -> Decimal:
    if value is None or not value.strip():
        raise ValueError(f"Missing numeric value in {source}")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"Invalid numeric value in {source}: {value!r}") from error
    if not number.is_finite():
        raise ValueError(f"Non-finite numeric value in {source}: {value!r}")
    return number


def _decimal_literal(value: Decimal) -> Literal:
    return Literal(value, datatype=XSD.decimal, normalize=False)


def _datetime_literal(value: datetime) -> Literal:
    return Literal(value.isoformat(timespec="seconds"), datatype=XSD.dateTime, normalize=False)


def _expected_timestamps() -> set[datetime]:
    timestamps: set[datetime] = set()
    timestamp = PERIOD_START
    while timestamp < PERIOD_END:
        timestamps.add(timestamp)
        timestamp += timedelta(hours=1)
    return timestamps


def _validate_coverage(
    actual: set[datetime], *, source: str, identifier: str
) -> None:
    expected = _expected_timestamps()
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"{len(missing)} missing hourly timestamps")
        if unexpected:
            details.append(f"{len(unexpected)} unexpected timestamps")
        raise ValueError(f"Incomplete {source} coverage for {identifier}: {', '.join(details)}")


def _nt_value(value: object) -> str:
    if isinstance(value, (URIRef, Literal)):
        return value.n3()
    raise TypeError(f"Unsupported RDF value: {type(value)!r}")


def serialize_graph_to_nt(graph: Graph, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = sorted(
        f"{_nt_value(subject)} {_nt_value(predicate)} {_nt_value(obj)} ."
        for subject, predicate, obj in graph
    )
    destination.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def sha256_of_file(path: Path) -> str:
    digest = sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def build_named_graphs(
    metadata_path: Path,
    electricity_path: Path | None = None,
    weather_path: Path | None = None,
) -> Dataset:
    data_dir = metadata_path.parent
    electricity_path = electricity_path or (
        data_dir / "meters" / "cleaned" / "electricity_cleaned.csv"
    )
    weather_path = weather_path or data_dir / "weather" / "weather.csv"

    with metadata_path.open(newline="", encoding="utf-8-sig") as metadata_file:
        metadata_rows = {
            row["building_id"]: row
            for row in csv.DictReader(metadata_file)
            if row.get("building_id")
        }

    missing_buildings = set(SELECTED_BUILDINGS) - metadata_rows.keys()
    if missing_buildings:
        raise ValueError(f"Buildings missing from metadata: {sorted(missing_buildings)}")

    selected_metadata = {building_id: metadata_rows[building_id] for building_id in SELECTED_BUILDINGS}
    sites = {row["site_id"] for row in selected_metadata.values() if row.get("site_id")}
    if len(sites) != 1 or any(not row.get("site_id") for row in selected_metadata.values()):
        raise ValueError("Selected buildings must have a metadata site_id")

    dataset = Dataset(default_union=False)
    buildings_graph = dataset.graph(BUILDINGS_GRAPH)
    measurements_graph = dataset.graph(MEASUREMENTS_GRAPH)
    weather_graph = dataset.graph(WEATHER_GRAPH)

    for building_id, row in selected_metadata.items():
        building_uri = URIRef(BASE + f"building/{normalize_identifier(building_id)}")
        site_uri = URIRef(BASE + f"site/{normalize_identifier(row['site_id'])}")
        buildings_graph.add((building_uri, RDF.type, BASE.Building))
        buildings_graph.add((site_uri, RDF.type, BASE.Site))
        buildings_graph.add((building_uri, BASE.belongsToSite, site_uri))

        area = row.get("sqm", "").strip()
        if area:
            buildings_graph.add(
                (
                    building_uri,
                    BASE.hasArea,
                    _decimal_literal(_parse_decimal(area, source=f"metadata sqm for {building_id}")),
                )
            )

        usage = row.get("primaryspaceusage", "").strip()
        if usage:
            usage_uri = URIRef(BASE + f"usage/{normalize_identifier(usage)}")
            buildings_graph.add((usage_uri, RDF.type, BASE.PrimarySpaceUsage))
            buildings_graph.add((building_uri, BASE.hasUsage, usage_uri))

    readings: dict[datetime, dict[str, Decimal]] = {}
    with electricity_path.open(newline="", encoding="utf-8-sig") as electricity_file:
        reader = csv.DictReader(electricity_file)
        fields = set(reader.fieldnames or ())
        required_fields = {"timestamp", *SELECTED_BUILDINGS}
        if not required_fields <= fields:
            raise ValueError(
                f"Electricity CSV is missing columns: {sorted(required_fields - fields)}"
            )

        for row in reader:
            timestamp = _parse_datetime(row["timestamp"], source=str(electricity_path))
            if not PERIOD_START <= timestamp < PERIOD_END:
                continue
            if timestamp in readings:
                raise ValueError(f"Duplicate electricity timestamp: {timestamp.isoformat()}")

            readings[timestamp] = {
                building_id: _parse_decimal(
                    row[building_id],
                    source=f"electricity meter {building_id} at {timestamp.isoformat()}",
                )
                for building_id in SELECTED_BUILDINGS
            }

    _validate_coverage(set(readings), source="electricity", identifier=", ".join(SELECTED_BUILDINGS))

    for timestamp, values in readings.items():
        timestamp_literal = _datetime_literal(timestamp)
        for building_id, value in values.items():
            building_uri = URIRef(BASE + f"building/{normalize_identifier(building_id)}")
            meter_uri = URIRef(BASE + f"meter/{normalize_identifier(building_id)}/electricity")
            reading_uri = URIRef(
                BASE + f"reading/{normalize_identifier(building_id)}/{timestamp.isoformat()}"
            )
            measurements_graph.add((reading_uri, RDF.type, BASE.ElectricityReading))
            measurements_graph.add((reading_uri, BASE.forBuilding, building_uri))
            measurements_graph.add((reading_uri, BASE.meter, meter_uri))
            measurements_graph.add((meter_uri, RDF.type, BASE.ElectricityMeter))
            measurements_graph.add((meter_uri, BASE.meterForBuilding, building_uri))
            measurements_graph.add((reading_uri, BASE.observedAt, timestamp_literal))
            measurements_graph.add((reading_uri, BASE.electricityValue, _decimal_literal(value)))

    site_id = next(iter(sites))
    site_uri = URIRef(BASE + f"site/{normalize_identifier(site_id)}")
    station_uri = URIRef(BASE + f"weather_station/{normalize_identifier(site_id)}")
    weather_graph.add((station_uri, RDF.type, BASE.WeatherStation))
    weather_graph.add((station_uri, BASE.atSite, site_uri))

    weather_observations: dict[datetime, Decimal] = {}
    with weather_path.open(newline="", encoding="utf-8-sig") as weather_file:
        reader = csv.DictReader(weather_file)
        required_fields = {"timestamp", "site_id", "airTemperature"}
        fields = set(reader.fieldnames or ())
        if not required_fields <= fields:
            raise ValueError(f"Weather CSV is missing columns: {sorted(required_fields - fields)}")

        for row in reader:
            if row["site_id"] != site_id:
                continue
            timestamp = _parse_datetime(row["timestamp"], source=str(weather_path))
            if not PERIOD_START <= timestamp < PERIOD_END:
                continue
            if timestamp in weather_observations:
                raise ValueError(
                    f"Duplicate weather timestamp for site {site_id}: {timestamp.isoformat()}"
                )
            weather_observations[timestamp] = _parse_decimal(
                row["airTemperature"],
                source=f"weather airTemperature for site {site_id} at {timestamp.isoformat()}",
            )

    _validate_coverage(set(weather_observations), source="weather", identifier=site_id)

    for timestamp, temperature in weather_observations.items():
        observation_uri = URIRef(
            BASE + f"weather_observation/{normalize_identifier(site_id)}/{timestamp.isoformat()}"
        )
        weather_graph.add((observation_uri, RDF.type, BASE.WeatherObservation))
        weather_graph.add((observation_uri, BASE.atSite, site_uri))
        weather_graph.add((observation_uri, BASE.observedAt, _datetime_literal(timestamp)))
        weather_graph.add((observation_uri, BASE.airTemperature, _decimal_literal(temperature)))

    return dataset


def export_named_graphs(dataset: Dataset, output_dir: Path) -> dict[str, dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    exports: dict[str, dict[str, str]] = {}

    for graph_name, graph_uri in GRAPH_EXPORTS.items():
        path = output_dir / f"{graph_name}.nt"
        serialize_graph_to_nt(dataset.graph(graph_uri), path)
        exports[graph_name] = {
            "path": str(path),
            "sha256": sha256_of_file(path),
        }
    return exports


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    metadata_path = project_root / "data" / "metadata.csv"
    output_dir = Path(__file__).resolve().parent / "output"
    exports = export_named_graphs(build_named_graphs(metadata_path), output_dir)

    print("Named graph exports generated:")
    for graph_name, info in sorted(exports.items()):
        print(f"- {graph_name}: {info['path']} (sha256={info['sha256']})")


if __name__ == "__main__":
    main()
