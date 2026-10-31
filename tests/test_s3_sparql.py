from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pyoxigraph import Literal, NamedNode, RdfFormat, Store

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sparql.dataset import GRAPH_IRIS, load_s2_exports

QUERY_DIR = ROOT / "sparql" / "queries"
EXPORT_DIR = ROOT / "s2" / "output"
EX = "https://ecosystem-training.local/"
XSD_DECIMAL = NamedNode("http://www.w3.org/2001/XMLSchema#decimal")
XSD_INTEGER = NamedNode("http://www.w3.org/2001/XMLSchema#integer")
XSD_DATETIME = NamedNode("http://www.w3.org/2001/XMLSchema#dateTime")
TEST_GRAPH = NamedNode("urn:s3-test:measurements")
TEST_ELECTRICITY_READING = NamedNode(EX + "ElectricityReading")
TEST_ELECTRICITY_VALUE = NamedNode(EX + "electricityValue")
TEST_ZERO_READING = NamedNode("urn:s3-test:reading-zero")
TEST_ABSENT_READING = NamedNode("urn:s3-test:reading-absent")
TEST_ZERO = Literal("0", datatype=XSD_DECIMAL)


def _node(value: str) -> NamedNode:
    return NamedNode(value)


def _decimal(value: str) -> Literal:
    return Literal(value, datatype=XSD_DECIMAL)


def _integer(value: int) -> Literal:
    return Literal(value)


def _datetime(value: str) -> Literal:
    return Literal(value, datatype=XSD_DATETIME)


@pytest.fixture(scope="module")
def s2_store() -> Store:
    return load_s2_exports(EXPORT_DIR)


@pytest.fixture
def zero_and_absence_store() -> Store:
    store = Store()
    store.load(
        input=(
            f"<{TEST_ZERO_READING.value}> "
            f"<http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
            f"<{TEST_ELECTRICITY_READING.value}> <{TEST_GRAPH.value}> .\n"
            f"<{TEST_ZERO_READING.value}> <{TEST_ELECTRICITY_VALUE.value}> "
            f"\"0\"^^<{XSD_DECIMAL.value}> <{TEST_GRAPH.value}> .\n"
            f"<{TEST_ABSENT_READING.value}> "
            f"<http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
            f"<{TEST_ELECTRICITY_READING.value}> <{TEST_GRAPH.value}> .\n"
        ),
        format=RdfFormat.N_QUADS,
    )
    return store


DATA_QUESTIONS = [
    pytest.param(
        "01-buildings-at-robin.rq",
        [
            (_node(EX + "building/robin_education_zenia"),),
            (_node(EX + "building/robin_lodging_dorthy"),),
            (_node(EX + "building/robin_public_carolina"),),
        ],
        id="buildings-at-robin",
    ),
    pytest.param(
        "02-building-area-and-usage.rq",
        [
            (
                _node(EX + "building/robin_education_zenia"),
                _decimal("6337"),
                _node(EX + "usage/education"),
            ),
            (
                _node(EX + "building/robin_lodging_dorthy"),
                _decimal("5842.9"),
                _node(EX + "usage/lodging_residential"),
            ),
            (
                _node(EX + "building/robin_public_carolina"),
                _decimal("10984"),
                _node(EX + "usage/public_services"),
            ),
        ],
        id="building-area-and-usage",
    ),
    pytest.param(
        "03-meters-for-buildings.rq",
        [
            (
                _node(EX + "meter/robin_education_zenia/electricity"),
                _node(EX + "building/robin_education_zenia"),
            ),
            (
                _node(EX + "meter/robin_lodging_dorthy/electricity"),
                _node(EX + "building/robin_lodging_dorthy"),
            ),
            (
                _node(EX + "meter/robin_public_carolina/electricity"),
                _node(EX + "building/robin_public_carolina"),
            ),
        ],
        id="meters-for-buildings",
    ),
    pytest.param(
        "04-readings-count-per-meter.rq",
        [
            (_node(EX + "meter/robin_education_zenia/electricity"), _integer(744)),
            (_node(EX + "meter/robin_lodging_dorthy/electricity"), _integer(744)),
            (_node(EX + "meter/robin_public_carolina/electricity"), _integer(744)),
        ],
        id="readings-count-per-meter",
    ),
    pytest.param(
        "05-readings-at-period-start.rq",
        [
            (_node(EX + "building/robin_education_zenia"), _decimal("52.25")),
            (_node(EX + "building/robin_lodging_dorthy"), _decimal("14.3")),
            (_node(EX + "building/robin_public_carolina"), _decimal("36.438")),
        ],
        id="observed-readings-at-period-start",
    ),
    pytest.param(
        "06-readings-at-noon.rq",
        [
            (_node(EX + "building/robin_education_zenia"), _decimal("136.5")),
            (_node(EX + "building/robin_lodging_dorthy"), _decimal("41.5")),
            (_node(EX + "building/robin_public_carolina"), _decimal("101.93799999999999")),
        ],
        id="observed-readings-at-noon",
    ),
    pytest.param(
        "07-monthly-electricity-totals.rq",
        [
            (
                _node(EX + "meter/robin_education_zenia/electricity"),
                _decimal("102907.5026"),
            ),
            (
                _node(EX + "meter/robin_lodging_dorthy/electricity"),
                _decimal("24945.8"),
            ),
            (
                _node(EX + "meter/robin_public_carolina/electricity"),
                _decimal("110441.6953"),
            ),
        ],
        id="monthly-electricity-sums",
    ),
    pytest.param(
        "08-weather-observation-count.rq",
        [(_node(EX + "site/robin"), _integer(744))],
        id="weather-observation-count",
    ),
    pytest.param(
        "09-weather-at-period-start.rq",
        [
            (_datetime("2016-01-01T00:00:00"), _decimal("3.8")),
            (_datetime("2016-01-01T01:00:00"), _decimal("3.7")),
        ],
        id="observed-weather-at-period-start",
    ),
    pytest.param(
        "10-weather-temperature-extremes.rq",
        [(_decimal("-3.8"), _decimal("14.9"))],
        id="weather-temperature-minimum-and-maximum",
    ),
    pytest.param(
        "11-buildings-without-area.rq",
        [],
        id="optional-area-is-unbound-for-no-buildings",
    ),
    pytest.param(
        "12-readings-without-value.rq",
        [],
        id="no-measurement-facts-missing-a-value",
    ),
]

ZERO_AND_ABSENCE_QUESTIONS = [
    pytest.param(
        "13-test-observed-zero.rq",
        [(TEST_ZERO_READING, TEST_ZERO)],
        id="test-only-observed-zero-is-a-fact",
    ),
    pytest.param(
        "14-test-absent-value.rq",
        [(TEST_ABSENT_READING,)],
        id="test-only-absence-is-not-zero",
    ),
    pytest.param(
        "15-test-optional-value-bound.rq",
        [(TEST_ABSENT_READING, None), (TEST_ZERO_READING, TEST_ZERO)],
        id="test-only-optional-distinguishes-bound-from-unbound",
    ),
]


@pytest.mark.parametrize(("query_name", "expected"), DATA_QUESTIONS)
def test_sparql_competency_questions(
    s2_store: Store,
    query_name: str,
    expected: list[tuple[NamedNode | Literal, ...]],
) -> None:
    query = (QUERY_DIR / query_name).read_text(encoding="utf-8")
    actual = [tuple(row) for row in s2_store.query(query)]
    assert actual == expected


@pytest.mark.parametrize(("query_name", "expected"), ZERO_AND_ABSENCE_QUESTIONS)
def test_zero_is_distinct_from_an_absent_fact(
    zero_and_absence_store: Store,
    query_name: str,
    expected: list[tuple[NamedNode | Literal | None, ...]],
) -> None:
    query = (QUERY_DIR / query_name).read_text(encoding="utf-8")
    actual = [tuple(row) for row in zero_and_absence_store.query(query)]
    assert actual == expected


def test_missing_s2_export_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Required S2 export is missing"):
        load_s2_exports(tmp_path)


def test_invalid_s2_export_fails_clearly(tmp_path: Path) -> None:
    for graph_name in GRAPH_IRIS:
        (tmp_path / f"{graph_name}.nt").write_text("<not valid N-Triples", encoding="utf-8")

    with pytest.raises(ValueError, match="Could not load S2 N-Triples export"):
        load_s2_exports(tmp_path)
