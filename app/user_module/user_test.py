import pytest
import json
import requests
from app.utils import test_base_url, OK, BAD_REQUEST, get_request_fn

pytestmark = pytest.mark.asyncio

base_url = f"{test_base_url}/users"


@pytest.mark.parametrize(
    "method, params, expected_response",
    [
        ("GET", {}, OK),
        (
            "PUT",
            {
                "center_name": "Headquarters",
                "email": "admin@dewa.com",
                "role": "general-manager",
                "designated_zone_name": "D-25",
                "is_active": "Active",
                "job_title": "Admin",
                "language": "en",
                "name": "Admin",
                "working_hours": "Fulltime",
            },
            OK,
        ),
        (
            "PUT",
            {
                "center_name": "Happiness Center",
                "email": "admin@dewa.com",
                "role": "general-manager",
                "designated_zone_name": "D-25",
                "is_active": "Active",
                "job_title": "Admin",
                "language": "en",
                "name": "Admin",
                "working_hours": "Fulltime",
            },
            OK,
        ),
        ("PUT", {}, BAD_REQUEST),
        (
            "PUT",
            {
                "center_name": "Wrong Center Name",
                "designated_zone_name": "D-25",
                "email": "admin@dewa.com",
                "role": "general-manager",
                "is_active": "Active",
                "job_title": "Admin",
                "language": "en",
                "name": "Admin",
                "working_hours": "Fulltime",
            },
            BAD_REQUEST,
        ),
        (
            "PUT",
            {
                "center_name": "Headquarters",
                "designated_zone_name": "D-25",
                "email": "Wrong user name",
                "role": "general-manager",
                "is_active": "Active",
                "job_title": "Admin",
                "language": "en",
                "name": "Admin",
                "working_hours": "Fulltime",
            },
            BAD_REQUEST,
        ),
        (
            "PUT",
            {
                "center_name": "Headquarters",
                "designated_zone_name": "D-25",
                "email": "admin@dewa.com",
                "role": "officer",
                "is_active": "Active",
                "job_title": "Admin",
                "language": "en",
                "name": "Admin",
                "working_hours": "Fulltime",
            },
            OK,
        ),
        ("DELETE", {"center": "Headquarters", "email": "admin@dewa.com"}, OK),
        ("DELETE", {"center": "Wrong Center", "email": "admin@dewa.com"}, BAD_REQUEST,),
        ("DELETE", {"center": "Headquarters", "email": "Wrong email"}, BAD_REQUEST,),
        ("DELETE", {}, BAD_REQUEST,),
    ],
)
async def test_user_handler(method, params, expected_response):
    endpoint_url = f"{base_url}/"
    request_fn = get_request_fn(method)
    if method == "GET" or method == "DELETE":
        r = request_fn(endpoint_url, params=params)
    if method == "POST" or method == "PUT":
        r = request_fn(endpoint_url, json=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        (
            {
                "email": "test@dewa.com",
                "hws": "0ced7be8d04b3a0fc9eeb097b83d1f7660e21d41d4c5d7a7af75bdb8b6d1c9a5",
            },
            OK,
        ),
        ({}, BAD_REQUEST),
        ({"email": "test@dewa.com", "hws": "Wrong Password"}, BAD_REQUEST),
        ({"email": "Wrong Username", "hws": "Wrong Password"}, BAD_REQUEST),
    ],
)
async def test_login(params, expected_response):
    r = requests.post(f"{base_url}/login", json=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        (
            {
                "center_name": "Headquarters",
                "designated_zone_name": "Test Area",
                "email": "test_success_general_manager@dewa.com",
                "hashed_pass": "HashedPassword",
                "job_title": "Tester",
                "name": "Test Success",
                "role": "general-manager",
                "working_hours": "Fulltime",
            },
            OK,
        ),
        (
            {
                "center_name": "Headquarters",
                "designated_zone_name": "Test Area",
                "email": "test_success_general_manager@dewa.com",
                "hashed_pass": "HashedPassword",
                "job_title": "Tester",
                "name": "Repeated Email",
                "role": "general-manager",
                "working_hours": "Fulltime",
            },
            400,
        ),
        (
            {
                "center_name": "Headquarters",
                "designated_zone_name": "Test Area",
                "email": "test_success_center_manager@dewa.com",
                "hashed_pass": "HashedPassword",
                "job_title": "Tester",
                "name": "Test Success",
                "role": "center-manager",
                "working_hours": "Fulltime",
            },
            OK,
        ),
        (
            {
                "center_name": "Headquarters",
                "designated_zone_name": "Test Area",
                "email": "test_success_officer@dewa.com",
                "hashed_pass": "HashedPassword",
                "job_title": "Tester",
                "name": "Test Success",
                "role": "officer",
                "working_hours": "Fulltime",
            },
            OK,
        ),
        (
            {
                "center_name": "Wrong Center Name",
                "designated_zone_name": "Test Area",
                "email": "test_success@dewa.com",
                "hashed_pass": "HashedPassword",
                "job_title": "Tester",
                "name": "Test Success",
                "role": "general-manager",
                "working_hours": "Fulltime",
            },
            BAD_REQUEST,
        ),
        (
            {
                "center_name": "Headquarters",
                "designated_zone_name": "Test Area",
                "email": "Wrong Email Format",
                "hashed_pass": "HashedPassword",
                "job_title": "Tester",
                "name": "Test Success",
                "role": "general-manager",
                "working_hours": "Fulltime",
            },
            BAD_REQUEST,
        ),
        (
            {
                "center_name": "Headquarters",
                "designated_zone_name": "Test Area",
                "email": "test_success@dewa.com",
                "hashed_pass": "HashedPassword",
                "job_title": "Tester",
                "name": "Test Success",
                "role": "Bad Role Creation",
                "working_hours": "Fulltime",
            },
            BAD_REQUEST,
        ),
    ],
)
async def test_register(params, expected_response):
    r = requests.post(f"{base_url}/register", json=params)
    r.status_code == expected_response


async def test_logout():
    login = requests.post(
        f"{base_url}/login",
        json={
            "email": "test@dewa.com",
            "hws": "0ced7be8d04b3a0fc9eeb097b83d1f7660e21d41d4c5d7a7af75bdb8b6d1c9a5",
        },
    )
    token = login.json().get("auth_token")
    r = requests.get(f"{base_url}/logout", headers={"Authorization": token})
    assert r.status_code == OK


async def test_get_all_working_hours():
    r = requests.get(f"{base_url}/select/working_hours/")
    assert r.status_code == OK


async def test_get_all_user_status():
    r = requests.get(f"{base_url}/select/status/")
    assert r.status_code == OK


async def test_get_all_languages():
    r = requests.get(f"{base_url}/select/languages/")
    assert r.status_code == OK
