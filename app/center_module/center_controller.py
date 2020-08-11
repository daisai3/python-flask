from flask import Blueprint, request, jsonify, abort, make_response
from .center_facade import CenterFacade
from app.user_module.user_facade import UserFacade
from app.timeline_module.timeline_facade import TimelineFacade
from app.utils import (
    EMPTY_REQUEST,
    INVALID_FORMAT,
    MISSING_PARAMS,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
)
from app.auth_tools import protected_endpoint
from app import auto


centers_controller = Blueprint("centers", __name__, url_prefix="/api/v1/centers")


@centers_controller.route("/get_center_info", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_center_info():
    """
    CENTER INFO - GET /api/v1/centers/get_center_info

    Detailed information about the specified center within a time interval

    Header {
      Authorization: Auth Token - JWT
    }

    Params
        - center: String (Center's Name)
        - from_time: BigInt (Epoch time in seconds)
        - to_time: BigInt (Epoch time in seconds)

    Returns CenterInfoResponse {
        avg_waiting_time: Float
        floor_plan_px_per_meter: Float,
        lat: Float,
        lng: Float,
        location: String,
        manager_email: String,
        manager_name: String,
        name: "Headquarters",
        scale_meters: Float,
        floor_plan: String,
        distance_points: List<List<Integer>>,
        employee_list: [
            {
                center_name: String
                designated_zone_name: String
                email: String
                is_active: String
                job_title: String
                language: String
                name: String
                photo: String
                working_hours: String
            },
        ],
        customer_list: [
            {
                age_range: String
                area: String
                center_name: String
                dwell_time: Float
                epoch_second: Integer
                ethnicity: String
                gender: String
                global_identity: String
                happiness_index: Float
                position_x: Integer
                position_y: Integer
            }
        ],
        cameras: [
            {
                calibration_matrix: List<List<Float>>
                cameraRTSP: String
                camera_coords: List<List<Integer>>
                camera_id: String
                camera_img: String
                camera_position: [[888, 2555]]
                center_name: String
                encoding: String
                floor_coords: List<List<Integer>>
                focal_length: String
                resolution: String
            }
        ]
    }
    """
    if request.method == "GET":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center_name = request.args.get("center")
        try:
            from_time = float(request.args.get("from_time"))
            to_time = float(request.args.get("to_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        if center_name is None or from_time is None or to_time is None:
            abort(make_response(jsonify(error=MISSING_PARAMS), 400))
        center_info = CenterFacade.get_center_info(center_name, from_time, to_time)
        return center_info


@centers_controller.route("/update_center_info", methods=["PUT"])
@auto.doc()
@protected_endpoint(["center-manager", "general-manager"], True)
def update_center_info(role):
    """
    UPDATE CENTER INFO - PUT /api/v1/centers/update_center_info

    Updates the basic information of a center.
    Accessible for "center-manager" and "general-manager".

    Header {
      Authorization: Auth Token - JWT
    }

    Body {
        distance_points: List<List<Integer>>
        floor_plan: String
        floor_plan_scale: Float
        location: String
        manager_email: String
        manager_name: String
        name: String
        scale_meters: Float
    }

    Returns {
        distance_points: List<List<Integer>>
        floor_plan_px_per_meter: Float
        lat: Float
        lng: Float
        location: String
        manager_email: String
        manager_name: String
        name: String
        scale_meters: Float
    }
    """
    if request.method == "PUT":
        data = request.get_json()
        if data is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center_info = CenterFacade.update_center_info(role, data)
        return center_info


@centers_controller.route("/select/", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_all_centers_name():
    """
    SELECT CENTER - GET /api/v1/centers/select/
    Gets the list of selectable center names
    Header {
      Authorization: Auth Token - JWT
    }

    Returns List<String>
    """
    if request.method == "GET":
        resp = CenterFacade.get_all_centers_name()
        return jsonify(resp)


@centers_controller.route("/select/zones", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_all_zones_name():
    """
    SELECT CENTER AREAS - GET /api/v1/centers/select/zones/
    Gets the list of selectable center areas
    Header {
      Authorization: Auth Token - JWT
    }

    Params:
      - center: String (Center's name)

    Returns List<String>
    """
    if request.method == "GET":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center = request.args.get("center")
        resp = CenterFacade.get_all_zones_name(center)
        return jsonify(resp)


@centers_controller.route("/zones", methods=["GET", "PUT", "POST", "DELETE"])
@auto.doc()
@protected_endpoint()
def zone_management():
    """
    GET ALL AREAS INFO - GET /api/v1/centers/zones/
    Gets the list of selectable center areas
    Header {
      Authorization: Auth Token - JWT
    }

    Params
     - center: String (Center's name)

     Returns [
         {
            area_name: String
            area_type: String
            center_name: String
            polygon: List<List<Integer>>
         }
     ]

    CREATE CENTER AREA - POST /api/v1/centers/zones/
    Creates a new area for the given center
    Header {
      Authorization: Auth Token - JWT
    }

    Body {
        area_name: String
        area_type: String
        center_name: String
        polygon: List<List<Integer>>
    }

    Response {
        area_name: String
        area_type: String
        center_name: String
        polygon: List<List<Integer>>
    }

    UPDATE CENTER AREA - PUT /api/v1/centers/zones/
    Updates the given area values
    Header {
      Authorization: Auth Token - JWT
    }

    Body {
        old_zone: {
            area_name: String
            area_type: String
            center_name: String
            polygon: List<List<Integer>>
        }
        new_zone: {
            area_name: String
            area_type: String
            center_name: String
            polygon: List<List<Integer>>
        }
    }

    Response {
        area_name: String
        area_type: String
        center_name: String
        polygon: List<List<Integer>>
    }

    DELETE CENTER AREAS - DELETE /api/v1/centers/zones/
    Deletes a center's area
    Header {
      Authorization: Auth Token - JWT
    }

    Params:
    - center: String
    - area_name: String
    - area_type: String

    Returns {"msg":"OK"}

    """
    resp = None
    if (
        (request.method == "GET" or request.method == "DELETE") and request.args is None
    ) or (
        (request.method == "POST" or request.method == "PUT")
        and request.get_json() is None
    ):
        abort(make_response(jsonify(error=EMPTY_REQUEST), 400))

    if request.method == "GET":
        center = request.args.get("center")
        resp = CenterFacade.get_all_zones(center)
    if request.method == "POST":
        data = request.get_json()
        resp = CenterFacade.create_zone(data)
    if request.method == "PUT":
        data = request.get_json()
        resp = CenterFacade.update_zone(data.get("old_zone"), data.get("new_zone"))
    if request.method == "DELETE":
        center = request.args.get("center")
        area = request.args.get("area_name")
        area_type = request.args.get("area_type")
        resp = CenterFacade.delete_zone(center, area, area_type)
    return jsonify(resp)


@centers_controller.route("/waiting", methods=["GET"])
@auto.doc()
@protected_endpoint(return_role=True)
def waiting_stats(role):
    """
    CENTER WAITING STATS - GET /api/v1/center/waiting
    Returns the waiting time stats for a given center and timeframe

    Header {
      Authorization: Auth Token - JWT
    }

    Params {
        center: String (center's name)
        from_time: float or int (Timestamp in seconds)
        to_time: float or int (Timestamp in seconds)
        live: Bool ( If data requested is meant to be live or not)
    }

    Returns CenterWaitingStatistics {
        total_waiting_time: Timestamp in seconds
        waiting_areas_attendance: [
            {
                "area": String (Area's Name),
                "amount": Int (People count)
            }
        ]
        total_ppl_waiting: Int (People count)
        waiting_factors: [
            {
                "area": String (Area's Name),
                "factor": Float (Relevance percent)
            }
        ]
    }
    """
    if request.method == "GET":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center = request.args.get("center")
        try:
            is_live = str(request.args.get("live")).lower() == "true"
            from_time = float(request.args.get("from_time"))
            to_time = float(request.args.get("to_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        resp = CenterFacade.get_center_waiting_stats(
            center, from_time, to_time, is_live
        )
        return jsonify(resp)


@centers_controller.route("/area_happiness", methods=["GET"])
@auto.doc()
@protected_endpoint(return_role=True)
def area_happiness(role):
    """
    CENTER AREAS HAPPINESS EXPERIENCE - GET /api/v1/center/area_happiness
    Returns the happiness experience average for a center between the time given

    Header {
      Authorization: Auth Token - JWT
    }

    Params {
        center: String (center's name)
        from_time: float or int (Timestamp in seconds)
        to_time: float or int (Timestamp in seconds)
    }

    Result list of AreaWithHX [
        {
            "area": "Main Entrance",
            "area_type": "Exit",
            "center_name": "Headquarters",
            "coords": [[ 2889, 3019 ], [ 2904, 3879 ], [ 3996, 3880 ], [ 3996, 3033 ]],
            "happiness_avg": 81.6
        }
    ]
    """
    if request.method == "GET":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center = request.args.get("center")
        try:
            from_time = float(request.args.get("from_time"))
            to_time = float(request.args.get("to_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        if center is None or from_time is None or to_time is None:
            abort(make_response(jsonify(error=MISSING_PARAMS), 400))
        resp = CenterFacade.get_areas_hx(center, from_time, to_time)
        return jsonify(resp)


@centers_controller.route("/customers", methods=["GET"])
@auto.doc()
@protected_endpoint()
def customers_list():
    """
    GET ALL CUSTOMERS INFO - GET /api/v1/centers/customers/
    Gets the list of customers in a center

    Header {
      Authorization: Auth Token - JWT
    }

    Params
     - center: String (Center's name)
     - from_time: Integer (Initial date)
     - to_time: Integer (End date)
     - live: Boolean (Customer's information in live)
     - page: Integer (Page number)
     - page_size: Integer (Size of each page)

     Returns
         {
            total_customers: Integer
            total_pages: Integer
            customers: List<CustomerInfo>: {
                id: String (Customer's ID)
                date: String (Date)
                dwell_time: Integer (Customer's dwell time)
                gender: String (Customer's Gender)
                age: String (Customer's age range)
                ethnicity: String (Customer's ethnicity)
                happiness: Integer (Customer's happiness)
                highlight_on_customers_areas:  List<highlight_on_customers_areas> {
                    area_name: String (Area name)
                    value: Boolean (Customer has been/is in the area)
                }
            }

    """

    if request.method == "GET":
        if request.args is None or len(request.args) < 6 or len(request.args) > 6:
            if len(request.args) < 6:
                abort(make_response(jsonify(error=MISSING_PARAMS), 400))
            else:
                abort(make_response(jsonify(error=INVALID_FORMAT), 400))

        page = request.args.get("page", DEFAULT_PAGE, type=int)
        page_size = request.args.get("page_size", DEFAULT_PAGE_SIZE, type=int)
        center_name = request.args.get("center").strip()
        try:
            from_time = int(request.args.get("from_time"))
            to_time = int(request.args.get("to_time"))
            is_live = str(request.args.get("live")).lower() == "true"
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))

        resp = CenterFacade.get_customer_list(
            center_name, from_time, to_time, is_live, page, page_size
        )
        return jsonify(resp)


@centers_controller.route("/area_statistics", methods=["GET"])
@auto.doc()
@protected_endpoint()
def area_statistics():
    """
    GET AREA STATISTICS - GET /api/v1/centers/area_statistics/
    Gets the statistics of all areas in a center
    Header {
      Authorization: Auth Token - JWT
    }

    Params
     - center: String (Center's name)
     - from_time: Integer (Initial date)
     - to_time: Integer (End date)
     - live: Boolean (Customer's information in live)

     Returns
         {
            clients: Integer (number of clients),
            areas: List<AreaInfo>: {
                area_name: String (Area name),
                area_type: String (Area type),
                center_name: String (Center name),
                clients: Integer (Number of customer in the area),
                polygon: List<Coordinates>
            }
         }

    """

    if request.method == "GET":
        if request.args is None or len(request.args) < 4 or len(request.args) > 4:
            if len(request.args) < 4:
                abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
            else:
                abort(make_response(jsonify(error=INVALID_FORMAT), 400))

        center_name = request.args.get("center").strip()
        try:
            from_time = int(request.args.get("from_time"))
            to_time = int(request.args.get("to_time"))
            is_live = str(request.args.get("live")).lower() == "true"
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))

        resp = CenterFacade.get_center_area_statistics(
            center_name, from_time, to_time, is_live
        )
        return jsonify(resp)


@centers_controller.route("/area_dwell_statistics", methods=["GET"])
@auto.doc()
@protected_endpoint()
def area_dwell_statistics():
    """
    GET AREA DWELL STATISTICS - GET /api/v1/centers/area_dwell_statistics/
    Gets the dwell time statistics of all areas in a center
    Header {
      Authorization: Auth Token - JWT
    }

    Params
     - center: String (Center's name)
     - from_time: Integer (Initial date)
     - to_time: Integer (End date)

     Returns
         {
            areas: List<AreaInfo>: {
                area_name: String (Area name),
                area_type: String (Area type),
                center_name: String (Center name),
                dwell: Number (Average Dwell time in the area),
                polygon: List<Coordinates>
            }
         }

    """

    if request.method == "GET":
        if request.args is None or len(request.args) < 3 or len(request.args) > 3:
            if len(request.args) < 3:
                abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
            else:
                abort(make_response(jsonify(error=INVALID_FORMAT), 400))

        try:
            center_name = request.args.get("center").strip()
            from_time = int(request.args.get("from_time"))
            to_time = int(request.args.get("to_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))

        resp = CenterFacade.get_center_area_dwell_statistics(
            center_name, from_time, to_time
        )
        return jsonify(resp)


@centers_controller.route("/customer_journey", methods=["GET"])
@auto.doc()
@protected_endpoint()
def customer_journey():
    """
    GET CUSTOMER JOURNEY - GET /api/v1/centers/customer_journey/
    Gets the customer journey in a center
    GET PEOPLE WAITING DEMOGRAPHICS - GET /api/v1/centers/people_waiting_demographics/
    Gets the statistics of people waiting
    Header {
      Authorization: Auth Token - JWT
    }

    Params
     - center: String (Center's name)
     - global_identity: String (Customer ID)

     Returns
         {
            areas: List<AreaInfo>: {
                area_name: String (Area name),
                area_type: String (Area type),
                epoch_second_entrance: Integer (Epoch second of entrance),
                avg_hx: Number (Happiness average in the area),
                dwell_time: Number (Dwell time in the area)
            }
         }

    """

    if request.method == "GET":
        if request.args is None or len(request.args) < 2 or len(request.args) > 2:
            if len(request.args) < 2:
                abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
            else:
                abort(make_response(jsonify(error=INVALID_FORMAT), 400))

        try:
            center_name = request.args.get("center").strip()
            global_identity = request.args.get("global_identity")
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))

        resp = CenterFacade.get_customer_journey(center_name, global_identity)
        return jsonify(resp)


@centers_controller.route("/people_waiting_demographics", methods=["GET"])
@auto.doc()
@protected_endpoint()
def people_waiting_demographics():
    """
    GET PEOPLE WAITING DEMOGRAPHICS - GET /api/v1/centers/people_waiting_demographics/
    Gets the statistics of people waiting

    Header {
      Authorization: Auth Token - JWT
    }

    Params
     - center: String (Center's name)
     - from_time: Integer (Initial date)
     - to_time: Integer (End date)
     - live: Boolean (Customer's information in live)

     Response {
         Male: Int
         Female: Int
         Locals: Int
         Non: Int
     }
     """
    if request.method == "GET":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center = request.args.get("center")
        try:
            is_live = str(request.args.get("live")).lower() == "true"
            from_time = float(request.args.get("from_time"))
            to_time = float(request.args.get("to_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        resp = CenterFacade.get_waiting_demographics(
            center, from_time, to_time, is_live
        )
        return jsonify(resp)


@centers_controller.route("/generate_report", methods=["GET"])
# @auto.doc()
@protected_endpoint(["general-manager", "center-manager"], return_role=True)
def generate_report(role):
    """
    """
    if request.method == "GET":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center = request.args.get("center")
        try:
            from_time = float(request.args.get("from_time"))
            to_time = float(request.args.get("to_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        if center is None or from_time is None or to_time is None:
            abort(make_response(jsonify(error=MISSING_PARAMS), 400))
        resp = {}
        SECONDS_IN_A_DAY = 60 * 60 * 24
        # GET HX HISTORY
        if to_time - from_time > SECONDS_IN_A_DAY:
            timeinterval = SECONDS_IN_A_DAY
        else:
            timeinterval = 60 * 60
        hx_chart = TimelineFacade.get_history(
            center, "happiness", from_time, to_time, timeinterval, role
        )
        resp.update({"hx_index": hx_chart})
        # GET ATTENDANCE - General
        general_attendance = TimelineFacade.get_historic_attendance(
            center, from_time, to_time
        )
        # GET ATTENDANCE - per day
        attendance_intervals = []

        if to_time - from_time > SECONDS_IN_A_DAY:
            # Todo: query each day
            pass

        resp.update(
            {
                "customer_attendance": {
                    "general": general_attendance,
                    "intervals": attendance_intervals,
                }
            }
        )
        # GET WAITING TIME CHART
        # TODO FACADE of graph
        # GET CUSTOMER MOST TRAVELED JOURNEYS
        most_traveled_journeys = TimelineFacade.get_most_traveled_journey(
            center, from_time, to_time
        )
        resp.update({"most_traveled_journeys": most_traveled_journeys})
        # GET AREA/AREA_TYPE USAGE
        # TODO FACADE

        return jsonify(resp)
