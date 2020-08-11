import random
import hashlib
import requests
import json
import re
import base64
import time


authorized_roles = ["officer", "center-manager", "general-manager"]

test_base_url = "http://0.0.0.0:5000/api/v1"
test_headers = {"content-type": "application/json"}
BAD_REQUEST = requests.codes["bad"]
OK = requests.codes["ok"]

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
BASE64_HEADER = "data:image/png;base64"
DEFAULT_PAGE = 0
DEFAULT_PAGE_SIZE = 10

# ** ERROR MESSAGES ** #
EMPTY_REQUEST = "Empty request"
MISSING_PARAMS = "Missing parameters"
INVALID_FORMAT = "Wrong parameter format"
NULL_PARAMS = "Parameters can't be null"
INVALID_TIME_RANGES = "to_time has to be a higher epoch second than from_time"
CENTER_NOT_FOUND = "Center not found"
AREA_NOT_FOUND = "Area not found"
CUSTOMER_NOT_FOUND = "Customer not found"
USER_OR_PASSWORD_INCORRECT = "User or password incorrect"
INVALID_PAGE_NUMBER = "Wrong page number"

# **  ** #


def gen_salt():
    return "".join(random.choice(ALPHABET) for i in range(16))


def get_request_fn(method):
    if method == "GET":
        return requests.get
    elif method == "POST":
        return requests.post
    elif method == "PUT":
        return requests.put
    elif method == "DELETE":
        return requests.delete
    else:
        raise ValueError("Not supported method")


def validate_email(email):
    return EMAIL_REGEX.match(email)


def is_base64(string):
    return BASE64_HEADER in string


def is_list_of_coords(lst):
    if lst is not None and isinstance(lst, list):
        for pair in lst:
            if (
                not isinstance(pair, list)
                or len(pair) != 2
                or not isinstance(pair[0], int)
                or not isinstance(pair[1], int)
                or pair[0] < 0
                or pair[1] < 0
            ):
                return False
    return True


def is_valid_area(area):
    area_name = area.get("area_name")
    area_type = area.get("area_type")
    center = area.get("center_name")
    polygon = area.get("polygon")
    return (
        area_name is not None
        and area_type is not None
        and center is not None
        and is_list_of_coords(polygon)
    )


def bytes2b64string(bytes_data, img_encoding=BASE64_HEADER):
    base64_encoded_data = base64.b64encode(bytes_data)
    return f'{img_encoding},{base64_encoded_data.decode("utf-8")}'


def bytes2json(bytes_data):
    if bytes_data is not None:
        decoded_bytes = bytes_data.decode("utf-8").replace("'", '"')
        data = json.loads(decoded_bytes)
        return data
    return None


def area_response_handler(area):
    area = dict(area)
    area_shape = area.get("polygon")
    decoded_coords = bytes2json(area_shape)
    area.update({"polygon": decoded_coords})
    return area


def add_dwell_time_to_customer(customer):
    updated_customer = dict(customer)
    updated_customer["dwell_time"] = (
        customer.live_dwell_time if customer.live_dwell_time is not None else 0
    )
    return updated_customer


def create_area_mapper(areas):
    area_map = {}
    for area in areas:
        area_map[area.area_name] = area_response_handler(area)

    def area_mapper(area_name):
        return area_map[area_name]

    return area_mapper
