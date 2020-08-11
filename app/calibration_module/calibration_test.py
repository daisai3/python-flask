import pytest
import json
import requests
from app.utils import test_base_url, BAD_REQUEST, OK

pytestmark = pytest.mark.asyncio

base_url = f"{test_base_url}/calibration"


@pytest.mark.parametrize(
    "params, expected_response",
    [
        (
            {
                "cameraConfig": {
                    "name": "Headquarters",
                    "cameras": [
                        {
                            "cameraRTSP": "rtsp://localhost",
                            "camera_coords": [[1, 1]],
                            "camera_id": "camera-1",
                            "camera_img": "data:image/png;base64,TestImageBase64",
                            "camera_position": [[1, 1]],
                            "encoding": "H265",
                            "floor_coords": [[1, 1]],
                            "focal_length": 3.8,
                            "resolution": {"width": 1920, "height": 1080},
                        }
                    ],
                }
            },
            OK,
        ),
        (
            {
                "cameraConfig": {
                    "name": "Wrong Name Center",
                    "cameras": [
                        {
                            "cameraRTSP": "rtsp://localhost",
                            "camera_coords": [[1, 1]],
                            "camera_id": "camera-1",
                            "camera_img": "data:image/png;base64,TestImageBase64",
                            "camera_position": [[1, 1]],
                            "encoding": "256",
                            "floor_coords": [[1, 1]],
                            "focal_length": 3.8,
                            "resolution": {"width": 1920, "height": 1080},
                        }
                    ],
                }
            },
            BAD_REQUEST,
        ),
        (
            {
                "cameraConfig": {
                    "name": "Headquarters",
                    "cameras": [
                        {
                            "cameraRTSP": "Wrong RTSP",
                            "camera_coords": [[1, 1, 1], 1],
                            "camera_position": [[1, 1, "2"], "2"],
                            "floor_coords": [[1, {}], ["1", []]],
                            "focal_length": "3.8",
                            "resolution": {"height": 1080},
                        }
                    ],
                }
            },
            BAD_REQUEST,
        ),
    ],
)
async def test_get_center_info(params, expected_response):
    r = requests.post(f"{base_url}/camera_calibration", json=params)
    assert r.status_code == expected_response


@pytest.mark.parametrize(
    "params, expected_response",
    [
        ({"center_name": "Headquarters", "camera_id": "camera-1",}, OK),
        ({"center_name": "Wrong Center", "camera_id": "camera-1",}, BAD_REQUEST),
        (
            {"center_name": "Headquarters", "camera_id": "Camera doesn't exist",},
            BAD_REQUEST,
        ),
        ({}, BAD_REQUEST),
    ],
)
async def test_delete_camera(params, expected_response):
    r = requests.delete(f"{base_url}/camera_calibration", params=params)
    assert r.status_code == expected_response
