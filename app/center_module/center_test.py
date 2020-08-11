import pytest
import json
import requests
from app.utils import test_base_url, BAD_REQUEST, OK, get_request_fn

pytestmark = pytest.mark.asyncio

base_url = f"{test_base_url}/centers"


@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center": "Headquarters", "from_time": 1000, "to_time": 2000}, OK,),
        ({}, BAD_REQUEST),
        (
            {"center": "WrongCenterName", "from_time": 1000, "to_time": 2000},
            BAD_REQUEST,
        ),
        ({"center": "Headquarters", "from_time": 2000, "to_time": 1000}, BAD_REQUEST,),
    ],
)
async def test_get_center_info(params, expected_response):
    r = requests.get(f"{base_url}/get_center_info", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        (
            {  # Good test
                "distance_points": [[12, 12], [12, 12]],
                "floor_plan": "data:image/png;base64,TestImageB64",
                "floor_plan_scale": 0.31,
                "location": "Test Location",
                "manager_email": "Manager_test@dewa.com",
                "manager_name": "Manager Test",
                "name": "Headquarters",
                "scale_meters": 3.25,
            },
            OK,
        ),
        (
            {  # wrong format numbers,  image, points, email, and center
                "distance_points": [["12", "12", "12"]],
                "floor_plan": "TestImageB64",
                "floor_plan_scale": "0.31",
                "location": "Test Location",
                "manager_email": "Manager_test",
                "manager_name": "Manager Test",
                "name": "WrongCenterName",
                "scale_meters": "3.25",
            },
            BAD_REQUEST,
        ),
        (
            {  # Missing values
                "distance_points": [[12, 12], [12, 12]],
                "manager_name": "Manager Test",
                "name": "Headquarters",
            },
            BAD_REQUEST,
        ),
    ],
)
async def test_update_center_info(params, expected_response):
    r = requests.put(f"{base_url}/update_center_info", json=params)
    assert r.status_code == expected_response


async def test_get_all_centers_name():
    r = requests.get(f"{base_url}/select/")
    assert r.status_code == OK


@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center": "Headquarters"}, OK),
        ({}, BAD_REQUEST),
        ({"center": "WrongCenterName"}, BAD_REQUEST),
    ],
)
async def test_get_all_zones_name(params, expected_response):
    r = requests.get(f"{base_url}/select/zones", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "method, params, expected_response",
    [
        ("GET", {"center": "Headquarters"}, OK),
        ("GET", {"center": "WrongCenterName"}, BAD_REQUEST),
        ("GET", {}, BAD_REQUEST),
        (
            "POST",
            {
                "area_name": "Test Area",
                "area_type": "Test",
                "center_name": "Headquarters",
                "polygon": [[12, 12], [12, 12], [12, 12]],
            },
            OK,
        ),
        (
            "POST",
            {
                "area_name": "Test Area",
                "area_type": "Test",
                "center_name": "WrongCenterName",
                "polygon": [["12", "12", "12"]],
            },
            BAD_REQUEST,
        ),
        ("POST", {"center_name": "Headquarters",}, BAD_REQUEST,),
        ("POST", {}, BAD_REQUEST),
        (  # Good Request
            "PUT",
            {
                "old_zone": {
                    "area_name": "Test Area",
                    "area_type": "Test",
                    "center_name": "Headquarters",
                    "polygon": [[12, 12], [12, 12], [12, 12]],
                },
                "new_zone": {
                    "area_name": "Test Area Updated",
                    "area_type": "Test",
                    "center_name": "Headquarters",
                    "polygon": [[21, 21], [21, 21], [21, 21], [21, 21]],
                },
            },
            OK,
        ),
        (
            "PUT",
            {
                # Empty request
            },
            BAD_REQUEST,
        ),
        (  # Good old - bad new
            "PUT",
            {
                "old_zone": {
                    "area_name": "Main Entrance",
                    "area_type": "Entry",
                    "center_name": "Headquarters",
                    "polygon": [[12, 12], [12, 12], [12, 12]],
                },
                "new_zone": {
                    "area_name": "Test Area Updated",
                    "area_type": "Test Updated",
                    "center_name": "WrongCenterName",
                    "polygon": [[21, 21, 21, 21]],
                },
            },
            BAD_REQUEST,
        ),
        (  # Bad old - good New
            "PUT",
            {
                "old_zone": {
                    "area_name": "Wrong Test Area Name",
                    "area_type": "Test",
                    "center_name": "Wrong Center Name",
                    "polygon": [[12, 12, 12],],
                },
                "new_zone": {
                    "area_name": "Main Entrance",
                    "area_type": "Entry",
                    "center_name": "Headquarters",
                    "polygon": [[21, 21, 21, 21]],
                },
            },
            BAD_REQUEST,
        ),
        (  # Good Delete
            "DELETE",
            {
                "area_name": "Test Area Updated",
                "area_type": "Test",
                "center": "Headquarters",
            },
            OK,
        ),
        (  # Bad Delete
            "DELETE",
            {
                "area_name": "Wrong Area Name",
                "area_type": "Wrong Type",
                "center": "Wrong Name",
            },
            BAD_REQUEST,
        ),
    ],
)
async def test_zone_management(method, params, expected_response):
    request_fn = get_request_fn(method)
    r = None
    if method == "POST" or method == "PUT":
        r = request_fn(f"{base_url}/zones", json=params)
    if method == "GET" or method == "DELETE":
        r = request_fn(f"{base_url}/zones", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        # good request
        ({"center": "Headquarters", "from_time": 1000, "to_time": 2000,}, OK),
        # bad request
        ({"center": "WrongName", "from_time": 2000, "to_time": 1000,}, BAD_REQUEST),
        ({}, BAD_REQUEST),
    ],
)
async def test_waiting_statistics(params, expected_response):
    r = requests.get(f"{base_url}/waiting", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        # good request
        ({"center": "Headquarters", "from_time": 1000, "to_time": 2000,}, OK),
        # bad request
        ({"center": "WrongName", "from_time": 2000, "to_time": 1000,}, BAD_REQUEST),
        ({}, BAD_REQUEST),
    ],
)
async def test_happiness_per_area(params, expected_response):
    r = requests.get(f"{base_url}/area_happiness", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        # good request
        (
            {
                "center": "Headquarters",
                "from_time": 1000,
                "to_time": 2000,
                "live": True,
                "page": 0,
                "page_size": 1,
            },
            OK,
        ),
        # bad request
        (
            {
                "center": "WrongName",
                "from_time": 2000,
                "to_time": 1000,
                "live": True,
                "page": 0,
                "page_size": 1,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "WrongName",
                "from_time": 1000,
                "to_time": 2000,
                "live": True,
                "page": -1,
                "page_size": 1,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "WrongName",
                "from_time": 1000,
                "to_time": 2000,
                "live": True,
                "page": 0,
                "page_size": -1,
            },
            BAD_REQUEST,
        ),
        (
            {
                "center": "WrongName",
                "from_time": 1000,
                "to_time": 2000,
                "page": 0,
                "page_size": -1,
            },
            BAD_REQUEST,
        ),
        ({}, BAD_REQUEST),
    ],
)
async def test_customers_list(params, expected_response):
    r = requests.get(f"{base_url}/customers", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        # good request
        (
            {
                "center": "Headquarters",
                "from_time": 1000,
                "to_time": 2000,
                "live": True,
            },
            OK,
        ),
        # bad request
        (
            {
                "center": "WrongName",
                "from_time": 2000,
                "to_time": 1000,
                "live": True,
                "page": 0,
            },
            BAD_REQUEST,
        ),
        (
            {"center": "WrongName", "from_time": 2000, "to_time": 1000, "live": True},
            BAD_REQUEST,
        ),
        ({"center": "WrongName", "from_time": 1000, "to_time": 2000}, BAD_REQUEST),
        ({"center": "WrongName", "from_time": 1000}, BAD_REQUEST),
        ({"center": "WrongName"}, BAD_REQUEST),
        ({}, BAD_REQUEST),
    ],
)
async def test_area_statistics(params, expected_response):
    r = requests.get(f"{base_url}/area_statistics", params=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        # good request
        (
            {
                "center": "Headquarters",
                "from_time": 1000,
                "to_time": 2000
            },
            OK,
        ),
        # bad request
        (
            {
                "center": "WrongName",
                "from_time": 2000,
                "to_time": 1000,
                "page": 0,
            },
            BAD_REQUEST,
        ),
        (
            {"center": "WrongName", "from_time": 2000, "to_time": 1000, "live": True},
            BAD_REQUEST,
        ),
        ({"center": "WrongName", "from_time": 2000, "to_time": 1000}, BAD_REQUEST),
        ({"center": "WrongName", "from_time": 1000}, BAD_REQUEST),
        ({"center": "WrongName"}, BAD_REQUEST),
        ({}, BAD_REQUEST),
    ],
)
async def test_area_statistics(params, expected_response):
    r = requests.get(f"{base_url}/area_dwell_statistics", params=params)
    assert r.status_code == expected_response

@pytest.mark.parametrize(
    "params, expected_response",
    [
        # good request
        (
            {
                "center": "Headquarters",
                "global_identity": "C-0001"
            },
            OK,
        ),
        # bad request
        (
            {
                "center": "WrongName",
                "global_identity": "C-0001",
            },
            BAD_REQUEST,
        ),
        (
            {"center": "WrongName", "global_identity": "C-0001", "live": True},
            BAD_REQUEST,
        ),
        ({"center": "WrongName"}, BAD_REQUEST),
        ({}, BAD_REQUEST),
    ],
)
async def test_customer_journey(params, expected_response):
    r = requests.get(f"{base_url}/customer_journey", params=params)
    assert r.status_code == expected_response