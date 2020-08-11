from flask import Blueprint, request, jsonify, abort, Response, make_response
from .timeline_facade import TimelineFacade
from app.auth_tools import protected_endpoint
from app import auto
from app.utils import EMPTY_REQUEST, INVALID_FORMAT

timeline_controller = Blueprint("timeline", __name__, url_prefix="/api/v1/timeline")


@timeline_controller.route("/happiness", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_happiness_timeline():
    """
    CUSTOMER HAPPINESS HISTORY - GET /api/v1/timeline/happiness

    Gets the history of happinness indexes of a customer

    Header {
      Authorization: Auth Token - JWT
    }

    Params
    - center: String
    - customer: String
    - from_time: Epoch time in seconds

    Returns [
        {
            timestamp: BigInt (Timestamp)
            value: Float (Happiness Index)
        }
    ]
    """
    if request.method == "GET":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center_name = request.args.get("center")
        customer_id = request.args.get("customer")
        try:
            from_time = int(request.args.get("from_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        response = TimelineFacade.get_happiness_timeline(
            center_name, customer_id, from_time
        )
        return jsonify(response)


@timeline_controller.route("/stages", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_stages_timeline():
    """
    CUSTOMER STAGES HISTORY - GET /api/v1/timeline/stages

    Gets the history of area transitions of a customer

    Header {
      Authorization: Auth Token - JWT
    }

    Params
    - center: String
    - customer: String
    - from_time: Epoch time in seconds

    Returns [
        {
            timestamp: BigInt (Timestamp)
            type: String (Area Type)
            value: String ( Area Name)
        }
    ]
    """
    if request.method == "GET":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center_name = request.args.get("center")
        customer_id = request.args.get("customer")
        try:
            from_time = int(request.args.get("from_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        response = TimelineFacade.get_stages_timeline(
            center_name, customer_id, from_time
        )
        return jsonify(response)


@timeline_controller.route("/footage", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_footage_timeline():
    """
    CUSTOMER FOOTAGE HISTORY - GET /api/v1/timeline/happiness

    Gets the history of a customers Face crops

    Header {
      Authorization: Auth Token - JWT
    }

    Params
    - center: String
    - customer: String
    - from_time: Epoch time in seconds

    Returns [
        {
            timestamp: BigInt (Timestamp)
            value: String (Image Source)
    ]
    """
    if request.method == "GET":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center_name = request.args.get("center")
        customer_id = request.args.get("customer")
        try:
            from_time = int(request.args.get("from_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        response = TimelineFacade.get_footage_timeline(
            center_name, customer_id, from_time
        )
        return jsonify(response)


@timeline_controller.route("/history", methods=["GET"])
@auto.doc()
@protected_endpoint(return_role=True)
def get_history(role):
    """
    GENERAL CENTER HISTORY - GET /api/v1/timeline/history
    Gets the historical average for the happiness or attendance in a given center


    Header {
      Authorization: Auth Token - JWT
    }

    Params {
        "center": "Headquarters", (The employee's center's name)
        "history_type": "happiness", ("happiness" or "attendance)
        "from_time": 1591106400, (timestamp in seconds)
        "end_time": 1591110470, (timestamp in seconds)
        "time_interval": 60, (Frames of time in which the aggregations are made)
    }

    Returns list of AverageTimeFrame [
        {
            "0-18": 50,
            "19-49": 0,
            "50+": 0,
            "Female": 50,
            "Local": 50,
            "Male": 0,
            "Non": 0,
            "time": 1591106460,
            "total_avg": 50
        }
    ]
    """
    if request.method == "GET":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center = request.args.get("center").strip()
        history_type = request.args.get("history_type").strip()
        try:
            from_time = float(request.args.get("from_time"))
            to_time = float(request.args.get("to_time"))
            time_interval = float(request.args.get("time_interval"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        response = TimelineFacade.get_history(
            center, history_type, from_time, to_time, time_interval, role,
        )
        return jsonify(response)


@timeline_controller.route("/journey-summary", methods=["GET"])
@auto.doc()
@protected_endpoint(["general-manager", "center-manager"], return_role=True)
def journey_summary(role):
    """
    CENTER'S JOURNEY SUMMARY - GET /api/v1/timeline/journey-summary
    Gets the clients journey summary of a given center

    Header {
      Authorization: Auth Token - JWT
    }

    Params {
        "center": "Headquarters", (The employee's center's name)
        "from_time": 1591106400, (timestamp in seconds)
        "to_time": 1591110470, (timestamp in seconds)
    }

    Returns {
  "area_usage": [
    {
      "area": "Sitting",
      "value": 0.18181818181818182
    },
    {
      "area": "Walking",
      "value": 0.36363636363636365
    },
    {
      "area": "Entry",
      "value": 0.2727272727272727
    },
    {
      "area": "Speaking",
      "value": 0.18181818181818182
    }
  ],
  "areas_journey": [
    {
      "area_type": "Waiting",
      "value": 6
    },
    {
      "area_type": "Entry",
      "value": 3
    },
    {
      "area_type": "Service",
      "value": 2
    }
  ]
}
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
        resp = TimelineFacade.get_journey_summary(center, from_time, to_time)
        return jsonify(resp)


@timeline_controller.route("/most-traveled-journeys", methods=["GET"])
@auto.doc()
@protected_endpoint(return_role=True)
def most_traveled_journeys(role):
    """
    MOST TRAVELED JOURNEYS - GET /api/v1/timeline/most-traveled-journeys
    Returns the most traveled journeys at a given center

    Header {
      Authorization: Auth Token - JWT
    }

    Params {
        "center": "Headquarters", (The employee's center's name)
        "from_time": 1591106400, (timestamp in seconds)
        "to_time": 1591110470, (timestamp in seconds)
    }

    Returns an array of JourneyUsage [
      {
        "journey": [
          {
            "area_name": "Main Entrance",
            "area_type": "Entry",
            "center_name": "Headquarters",
          },
          {
            "area_name": "Devices and Tablets",
            "area_type": "Interaction",
            "center_name": "Headquarters",
          },
          {
            "area_name": "Happiness Lounge",
            "area_type": "Waiting",
            "center_name": "Headquarters",
          }
        ],
        "percent": 0.25
      },
    ]
"""
    if request.method == "GET":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center = request.args.get("center")
        try:
            from_time = int(request.args.get("from_time"))
            to_time = int(request.args.get("to_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        resp = TimelineFacade.get_most_traveled_journey(center, from_time, to_time)
        return jsonify(resp)


@timeline_controller.route("/position_heatmap", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_position_heatmap():
    """
    HEATMAP VALUES - GET /api/v1/timeline/position_heatmap
    Returns the amount of times that customers has gone through a space.

    Header {
      Authorization: Auth Token - JWT
    }

    Params {
        "center": "Headquarters", (The employee's center's name)
        "from_time": 1591106400, (timestamp in seconds)
        "to_time": 1591110470, (timestamp in seconds)
    }

    Returns {
        'max': int (Max value of reference)
        'values' : [
          {
            'x': int (Coordinate in X)
            'y':int (Coordinate in Y)
            'value': int (Amount of times customers has gone through this space)
          }
        ]
    """
    if request.method == "GET":
        data = request.args
        if data is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center = data.get("center")
        try:
            from_time = float(data.get("from_time"))
            to_time = float(data.get("to_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        resp = TimelineFacade.get_heatmap(center, from_time, to_time)
        return jsonify(resp)


@timeline_controller.route("/customer_position_heatmap", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_customer_position_heatmap():
    """
    CUSTOMER HEATMAP VALUES - GET /api/v1/timeline/customer_position_heatmap
    Returns the amount of times that a customer has gone through a space.

    Header {
      Authorization: Auth Token - JWT
    }

    Params {
        "center": "Headquarters", (The employee's center's name)
        "from_time": 1591106400, (timestamp in seconds)
        "to_time": 1591110470, (timestamp in seconds)
        "global_identity": C-001, (Customer ID)
    }

    Returns {
        'max': int (Max value of reference)
        'values' : [
          {
            'x': int (Coordinate in X)
            'y':int (Coordinate in Y)
            'value': int (Amount of times a customer has gone through this space)
          }
        ]
    """
    if request.method == "GET":
        data = request.args
        if data is None or data.get("global_identity") is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center = data.get("center")
        try:
            from_time = float(data.get("from_time"))
            to_time = float(data.get("to_time"))
            global_identity = data.get("global_identity")
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        resp = TimelineFacade.get_heatmap(center, from_time, to_time, global_identity)
        return jsonify(resp)


@timeline_controller.route("/position_dwell_heatmap", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_position_dwell_heatmap():
    """
    HEATMAP VALUES - GET /api/v1/timeline/position_dwell_heatmap
    Returns the average of time that customers has gone through a space.

    Header {
      Authorization: Auth Token - JWT
    }

    Params {
        "center": "Headquarters", (The employee's center's name)
        "from_time": 1591106400, (timestamp in seconds)
        "to_time": 1591110470, (timestamp in seconds)
    }

    Returns {
        'max': int (Max value of reference)
        'values' : [
          {
            'x': int (Coordinate in X)
            'y':int (Coordinate in Y)
            'dwell': int (Average of time customers has gone through this space)
          }
        ]
    """
    if request.method == "GET":
        data = request.args
        if data is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center = data.get("center")
        try:
            from_time = float(data.get("from_time"))
            to_time = float(data.get("to_time"))
        except (ValueError, TypeError):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        resp = TimelineFacade.get_dwell_heatmap(center, from_time, to_time)
        return jsonify(resp)


@timeline_controller.route("/historic_attendance", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_historic_attendance():
    """
    Historic Attendance - GET /api/v1/timeline/historic_attendance
    Returns the statistics of customer attendance for a given center in a given time range

    Header {
      Authorization: Auth Token - JWT
    }


    Params {
        "center": "Headquarters", (The employee's center's name)
        "from_time": 1591106400, (timestamp in seconds)
        "to_time": 1591110470, (timestamp in seconds)
    }

    Returns {
      total_customers: int,
      Female: int,
      Male: int,
      Local: int,
      Non: int,
      mask_on: int,
    }
  """
    if request.args is None:
        abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
    center = request.args.get("center")
    try:
        from_time = int(request.args.get("from_time"))
        to_time = int(request.args.get("to_time"))
    except (ValueError, TypeError):
        abort(make_response(jsonify(error=INVALID_FORMAT), 400))
    resp = TimelineFacade.get_historic_attendance(center, from_time, to_time)
    return jsonify(resp)

