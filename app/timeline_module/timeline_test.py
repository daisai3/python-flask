import pytest
import json
import requests
from app.utils import test_base_url, BAD_REQUEST, OK

pytestmark = pytest.mark.asyncio

base_url = f"{test_base_url}/timeline"


@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center": "Headquarters", "customer": "C-0001", "from_time": 1000}, OK),
        (
            {"center": "Wrong Center Name", "customer": "C-0001", "from_time": 1000},
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "customer": "Wrong Customer ID",
                "from_time": 1000,
            },
            BAD_REQUEST,
        ),
        (
            {"center": "Headquarters", "customer": "C-0001", "from_time": "Wrong Time"},
            BAD_REQUEST,
        ),
        ({}, BAD_REQUEST),
    ],
)
async def test_get_happiness_timeline(params, expected_response):
    r = requests.get(f"{base_url}/happiness", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center": "Headquarters", "customer": "C-0001", "from_time": 1000}, OK),
        (
            {"center": "Wrong Center Name", "customer": "C-0001", "from_time": 1000},
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "customer": "Wrong Customer ID",
                "from_time": 1000,
            },
            BAD_REQUEST,
        ),
        (
            {"center": "Headquarters", "customer": "C-0001", "from_time": "Wrong Time"},
            BAD_REQUEST,
        ),
        ({}, BAD_REQUEST),
    ],
)
async def test_get_stages_timeline(params, expected_response):
    r = requests.get(f"{base_url}/stages", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center": "Headquarters", "customer": "C-0001", "from_time": 1000}, OK),
        (
            {"center": "Wrong Center Name", "customer": "C-0001", "from_time": 1000},
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "customer": "Wrong Customer ID",
                "from_time": 1000,
            },
            BAD_REQUEST,
        ),
        (
            {"center": "Headquarters", "customer": "C-0001", "from_time": "Wrong Time"},
            BAD_REQUEST,
        ),
        ({}, BAD_REQUEST),
    ],
)
async def test_get_footage_timeline(params, expected_response):
    r = requests.get(f"{base_url}/footage", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        (
            {
                "center": "Headquarters",
                "history_type": "happiness",
                "from_time": 1591106400,
                "to_time": 1591110470,
                "time_interval": 60,
            },
            OK,
        ),
        (
            {
                "center": "Wrong Center",
                "history_type": "happiness",
                "from_time": 1591106400,
                "to_time": 1591110470,
                "time_interval": 60,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "history_type": "Wrong type of history",
                "from_time": 1591106400,
                "to_time": 1591110470,
                "time_interval": 60,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "history_type": "happiness",
                "from_time": 1591106400,
                "to_time": 150470,
                "time_interval": 60,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "history_type": "happiness",
                "from_time": "Wrong from time",
                "to_time": "1591110470",
                "time_interval": 60,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "history_type": "happiness",
                "from_time": 1591106400,
                "to_time": "Wrong to time",
                "time_interval": 60,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "history_type": "happiness",
                "from_time": 1591106400,
                "to_time": 1591110470,
                "time_interval": "Wrong time interval",
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "history_type": "attendance",
                "from_time": 1591106400,
                "to_time": 1591110470,
                "time_interval": 60,
            },
            OK,
        ),
        (
            {
                "center": "Wrong Center",
                "history_type": "attendance",
                "from_time": 1591106400,
                "to_time": 1591110470,
                "time_interval": 60,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "history_type": "attendance",
                "from_time": 1591106400,
                "to_time": 150470,
                "time_interval": 60,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "history_type": "attendance",
                "from_time": "Wrong from time",
                "to_time": "1591110470",
                "time_interval": 60,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "history_type": "attendance",
                "from_time": 1591106400,
                "to_time": "Wrong to time",
                "time_interval": 60,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "Headquarters",
                "history_type": "attendance",
                "from_time": 1591106400,
                "to_time": 1591110470,
                "time_interval": "Wrong time interval",
            },
            BAD_REQUEST,
        ),
    ],
)
async def test_get_history(params, expected_response):
    r = requests.get(f"{base_url}/history", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center": "Headquarters", "from_time": 1000, "to_time": 2000}, OK),
        (
            {"center": "Wrong Center Name", "from_time": 1000, "to_time": 2000},
            BAD_REQUEST,
        ),
        ({"center": "Headquarters", "from_time": 3000, "to_time": 2000}, BAD_REQUEST),
        ({"center": "Headquarters", "from_time": "Wrong Time"}, BAD_REQUEST),
        ({}, BAD_REQUEST),
    ],
)
async def test_get_journey_summary(params, expected_response):
    r = requests.get(f"{base_url}/journey-summary", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center": "Headquarters", "from_time": 1000, "to_time": 2000}, OK),
        (
            {"center": "Wrong Center Name", "from_time": 1000, "to_time": 2000},
            BAD_REQUEST,
        ),
        ({"center": "Headquarters", "from_time": 3000, "to_time": 2000}, BAD_REQUEST),
        ({"center": "Headquarters", "from_time": "Wrong Time"}, BAD_REQUEST),
        ({}, BAD_REQUEST),
    ],
)
async def test_get_most_traveled_journeys(params, expected_response):
    r = requests.get(f"{base_url}/most-traveled-journeys", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center": "Headquarters", "from_time": 1000, "to_time": 2000}, OK),
        (
            {"center": "Wrong Center Name", "from_time": 1000, "to_time": 2000},
            BAD_REQUEST,
        ),
        ({"center": "Headquarters", "from_time": 3000, "to_time": 2000}, BAD_REQUEST),
        ({"center": "Headquarters", "from_time": "Wrong Time"}, BAD_REQUEST),
        ({}, BAD_REQUEST),
    ],
)
async def test_heatmap_positions(params, expected_response):
    r = requests.get(f"{base_url}/position_heatmap", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center": "Headquarters", "from_time": 1000, "to_time": 2000, "global_identity": "C-0001"}, OK),
        (
            {"center": "Wrong Center Name", "from_time": 1000, "to_time": 2000,"global_identity": "C-0001"},
            BAD_REQUEST,
        ),
        ({"center": "Headquarters", "from_time": 3000, "to_time": 2000, "global_identity": "C-0001"}, BAD_REQUEST),
        ({"center": "Headquarters", "from_time": "Wrong Time"}, BAD_REQUEST),
        ({}, BAD_REQUEST),
    ],
)
async def test_customer_positions_heatmap(params, expected_response):
    r = requests.get(f"{base_url}/customer_position_heatmap", params=params)
    assert r.status_code == expected_response

@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center": "Headquarters", "from_time": 1000, "to_time": 2000}, OK),
        (
            {"center": "Wrong Center Name", "from_time": 1000, "to_time": 2000},
            BAD_REQUEST,
        ),
        ({"center": "Headquarters", "from_time": 3000, "to_time": 2000}, BAD_REQUEST),
        ({"center": "Headquarters", "from_time": "Wrong Time"}, BAD_REQUEST),
        ({}, BAD_REQUEST),
    ],
)
async def test_heatmap_dwell_positions(params, expected_response):
    r = requests.get(f"{base_url}/position_dwell_heatmap", params=params)
    assert r.status_code == expected_response

@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center": "Headquarters", "from_time": 1000, "to_time": 2000}, OK),
        (
            {"center": "Wrong Center Name", "from_time": 1000, "to_time": 2000},
            BAD_REQUEST,
        ),
        ({"center": "Headquarters", "from_time": 3000, "to_time": 2000}, BAD_REQUEST),
        ({"center": "Headquarters", "from_time": "Wrong Time"}, BAD_REQUEST),
        ({}, BAD_REQUEST),
    ],
)
async def test_historic_attendance(params, expected_response):
    r = requests.get(f"{base_url}/historic_attendance", params=params)
    assert r.status_code == expected_response
