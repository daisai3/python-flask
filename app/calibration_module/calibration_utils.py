import json
import re

RTSP_REGEX = re.compile(
    r"(\b(rtsp):\/\/)?[-A-Za-z0-9+&@#\/%?=~_|!:,.;]+[-A-Za-z0-9+&@#\/%=~_|]"
)
ENCODING_LIST = ["H264", "H265"]


def camera_update_center_name(name):
    def camera_update(camera):
        camera.update({"name": name})
        return camera

    return camera_update


def camera_response_handler(camera):
    camera_dict = dict(camera)
    camera_settings_bytes = camera_dict.get("calibration_info")
    if camera_settings_bytes:
        camera_settings = json.loads(camera_settings_bytes)
        camera_dict.update(camera_settings)
    del camera_dict["calibration_info"]
    return camera_dict


def is_valid_RTSP_url(url):
    return RTSP_REGEX.match(url)


def is_valid_encoding(encoding):
    return encoding in ENCODING_LIST


def is_valid_resolution(resolution):
    width = resolution.get("width")
    height = resolution.get("height")
    return width is not None and height is not None and width > 0 and height > 0
